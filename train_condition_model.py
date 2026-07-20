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
import json

class CustomConditionDataset(Dataset):
    """
    Wrapper dataset that extracts only the condition/disease part from folder names.
    Expects folder names in format: PlantName___Condition
    This enables cross-breed disease detection by focusing on disease symptoms rather than plant-specific patterns.
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
        
        print(f"\n{'='*70}")
        print(f"Dataset Processing Summary:")
        print(f"  Original plant-specific classes: {len(self.original_classes)}")
        print(f"  Unique conditions extracted: {len(self.conditions)}")
        print(f"{'='*70}")
        print(f"\nConditions detected:")
        for i, cond in enumerate(self.conditions, 1):
            print(f"  {i:2d}. {cond}")
        print(f"{'='*70}\n")
    
    def __len__(self):
        return len(self.base_dataset)
    
    def __getitem__(self, idx):
        image, original_label = self.base_dataset[idx]
        condition_label = self.label_mapping[original_label]
        return image, condition_label
    
    def save_mapping(self, filepath):
        """Save the condition mapping for inference"""
        mapping = {
            'conditions': self.conditions,
            'condition_to_idx': self.condition_to_idx,
            'num_classes': len(self.conditions)
        }
        with open(filepath, 'w') as f:
            json.dump(mapping, f, indent=2)
        print(f"Condition mapping saved to: {filepath}")

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
        train_split, val_split_ds = torch.utils.data.random_split(full_base, [n_train, n_val])
        
        # Wrap splits with CustomConditionDataset
        train_ds = CustomConditionDataset(train_split)
        val_ds = CustomConditionDataset(val_split_ds)
        # set val transforms
        val_ds.base_dataset.dataset.transform = transform_val

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=4, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=4, pin_memory=True)
    return train_loader, val_loader, (train_ds, val_ds)

def build_model(num_classes, pretrained=True):
    model = models.resnet18(pretrained=pretrained)
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)
    return model

def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item() * images.size(0)
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
    
    epoch_loss = running_loss / len(loader.dataset)
    epoch_acc = 100.0 * correct / total
    return epoch_loss, epoch_acc

def evaluate(model, loader, device, class_names):
    model.eval()
    preds = []
    trues = []
    correct = 0
    total = 0
    
    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            preds.extend(predicted.cpu().numpy())
            trues.extend(labels.numpy())
            total += labels.size(0)
            correct += (predicted.cpu() == labels).sum().item()
    
    accuracy = 100.0 * correct / total
    report = classification_report(trues, preds, target_names=class_names, digits=4)
    cm = confusion_matrix(trues, preds)
    return report, cm, trues, preds, accuracy

def main(args):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\n{'='*70}")
    print(f"CONDITION-BASED PLANT DISEASE DETECTION")
    print(f"Training Device: {device}")
    print(f"{'='*70}\n")
    
    train_loader, val_loader, datasets_tuple = get_data_loaders(args.data_dir, args.batch_size, args.img_size)
    train_ds, val_ds = datasets_tuple
    
    # Get condition names from the custom dataset
    class_names = train_ds.conditions
    
    # Save the condition mapping
    train_ds.save_mapping('condition_mapping.json')
    
    print(f"Building ResNet18 model for {len(class_names)} conditions...")
    model = build_model(num_classes=len(class_names), pretrained=True).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=2, verbose=True)
    
    best_val_acc = 0.0
    
    print(f"\nStarting training for {args.epochs} epochs...")
    print(f"{'='*70}\n")
    
    for epoch in range(args.epochs):
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        report, cm, trues, preds, val_acc = evaluate(model, val_loader, device, class_names)
        
        print(f"\n{'='*70}")
        print(f"Epoch {epoch+1}/{args.epochs}")
        print(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        print(f"  Val Acc: {val_acc:.2f}%")
        print(f"{'='*70}")
        print(report)
        
        # Save model checkpoint
        checkpoint_path = f'condition_model_epoch{epoch+1}.pth'
        torch.save({
            'epoch': epoch + 1,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'val_acc': val_acc,
            'conditions': class_names,
        }, checkpoint_path)
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                'epoch': epoch + 1,
                'model_state_dict': model.state_dict(),
                'val_acc': val_acc,
                'conditions': class_names,
            }, 'best_condition_model.pth')
            print(f"✓ Best model saved with val_acc: {val_acc:.2f}%")
        
        scheduler.step(val_acc)
    
    # Final confusion matrix
    print(f"\n{'='*70}")
    print(f"Training Complete!")
    print(f"Best Validation Accuracy: {best_val_acc:.2f}%")
    print(f"{'='*70}\n")
    
    plt.figure(figsize=(14, 12))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names, yticklabels=class_names,
                cbar_kws={'label': 'Count'})
    plt.xlabel('Predicted Condition', fontsize=12, fontweight='bold')
    plt.ylabel('True Condition', fontsize=12, fontweight='bold')
    plt.title('Condition-Based Classification - Confusion Matrix', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig('condition_confusion_matrix.png', dpi=300)
    print("Confusion matrix saved as: condition_confusion_matrix.png")
    print("Best model saved as: best_condition_model.pth")
    print("Condition mapping saved as: condition_mapping.json")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train condition-based plant disease detection model')
    parser.add_argument('--data_dir', type=str, required=True, help='Path to dataset root or train/val folders')
    parser.add_argument('--epochs', type=int, default=10, help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size for training')
    parser.add_argument('--lr', type=float, default=1e-4, help='Learning rate')
    parser.add_argument('--img_size', type=int, default=224, help='Input image size')
    args = parser.parse_args()
    main(args)
