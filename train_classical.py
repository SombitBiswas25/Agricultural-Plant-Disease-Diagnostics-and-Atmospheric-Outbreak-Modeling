import os
import argparse
from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms, datasets, models
import torch.optim as optim
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

class CustomConditionDataset(Dataset):
    """
    Wrapper dataset that extracts only the condition/disease part from folder names.
    Expects folder names in format: PlantName___Condition
    """
    def __init__(self, image_folder_dataset):
        self.base_dataset = image_folder_dataset
        self.original_classes = image_folder_dataset.classes
        
        # Extract conditions from full class names (after '___')
        self.condition_map = {}
        for full_class in self.original_classes:
            if '___' in full_class:
                condition = full_class.split('___')[-1]  # Get part after ___
            else:
                condition = full_class  # Fallback if no ___ found
            self.condition_map[full_class] = condition
        
        # Get unique conditions and create mapping
        self.conditions = sorted(list(set(self.condition_map.values())))
        self.condition_to_idx = {cond: idx for idx, cond in enumerate(self.conditions)}
        
        # Create reverse mapping for samples
        original_class_to_condition_idx = {}
        for full_class, condition in self.condition_map.items():
            original_idx = self.base_dataset.class_to_idx[full_class]
            condition_idx = self.condition_to_idx[condition]
            original_class_to_condition_idx[original_idx] = condition_idx
        
        self.label_mapping = original_class_to_condition_idx
        
        print(f"Original classes: {len(self.original_classes)}")
        print(f"Unique conditions: {len(self.conditions)}")
        print(f"Conditions: {self.conditions}")
    
    def __len__(self):
        return len(self.base_dataset)
    
    def __getitem__(self, idx):
        image, original_label = self.base_dataset[idx]
        condition_label = self.label_mapping[original_label]
        return image, condition_label

def get_data_loaders(data_dir, batch_size=32, img_size=224, val_split=0.2):
    transform_train = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
    ])
    transform_val = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
    ])

    # If data_dir contains train/ and val/ folders, use them. Otherwise treat data_dir as root ImageFolder and split.
    train_dir = os.path.join(data_dir, 'train')
    val_dir = os.path.join(data_dir, 'val')
    if os.path.isdir(train_dir) and os.path.isdir(val_dir):
        train_base = datasets.ImageFolder(train_dir, transform=transform_train)
        val_base = datasets.ImageFolder(val_dir, transform=transform_val)
        
        # Wrap with CustomConditionDataset to extract only conditions
        train_ds = CustomConditionDataset(train_base)
        val_ds = CustomConditionDataset(val_base)
    else:
        full_base = datasets.ImageFolder(data_dir, transform=transform_train)
        n = len(full_base)
        n_val = int(n * val_split)
        n_train = n - n_val
        train_split, val_split = torch.utils.data.random_split(full_base, [n_train, n_val])
        
        # Wrap splits with CustomConditionDataset
        train_ds = CustomConditionDataset(train_split)
        val_ds = CustomConditionDataset(val_split)
        # set val transforms
        val_ds.base_dataset.dataset.transform = transform_val

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=4)
    return train_loader, val_loader, (train_ds, val_ds)

def build_model(num_classes, pretrained=True):
    model = models.resnet18(pretrained=pretrained)
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)
    return model

def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * images.size(0)
    return running_loss / len(loader.dataset)

def evaluate(model, loader, device, class_names):
    model.eval()
    preds = []
    trues = []
    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            preds.extend(predicted.cpu().numpy())
            trues.extend(labels.numpy())
    report = classification_report(trues, preds, target_names=class_names, digits=4)
    cm = confusion_matrix(trues, preds)
    return report, cm, trues, preds

def main(args):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    train_loader, val_loader, datasets_tuple = get_data_loaders(args.data_dir, args.batch_size, args.img_size)
    train_ds, val_ds = datasets_tuple
    
    # Get condition names from the custom dataset
    class_names = train_ds.conditions
    
    print(f"\n{'='*60}")
    print(f"Training on {len(class_names)} unique conditions (cross-breed compatible)")
    print(f"{'='*60}\n")
    
    model = build_model(num_classes=len(class_names), pretrained=True).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    for epoch in range(args.epochs):
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device)
        report, cm, trues, preds = evaluate(model, val_loader, device, class_names)
        print(f"Epoch {epoch+1}/{args.epochs} - Train Loss: {train_loss:.4f}")
        print(report)
        torch.save(model.state_dict(), f'model_epoch{epoch+1}.pth')
    plt.figure(figsize=(10,8))
    sns.heatmap(cm, annot=False, fmt='d', xticklabels=class_names, yticklabels=class_names)
    plt.xlabel('Predicted'); plt.ylabel('True'); plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig('confusion_matrix.png')
    print("Training complete. Model and confusion matrix saved.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, required=True, help='Path to dataset root or train/val folders')
    parser.add_argument('--epochs', type=int, default=1)
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--lr', type=float, default=1e-4)
    parser.add_argument('--img_size', type=int, default=224)
    args = parser.parse_args()
    main(args)
