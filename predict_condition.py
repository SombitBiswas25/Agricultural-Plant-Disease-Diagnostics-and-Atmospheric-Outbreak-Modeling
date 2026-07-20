import os
import argparse
import json
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

class ConditionClassifier:
    """
    Inference class for condition-based plant disease detection.
    Works across different plant breeds by focusing on disease symptoms.
    """
    def __init__(self, model_path, mapping_path, device=None):
        self.device = device if device else torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load condition mapping
        with open(mapping_path, 'r') as f:
            mapping = json.load(f)
        
        self.conditions = mapping['conditions']
        self.num_classes = mapping['num_classes']
        
        # Load model
        self.model = models.resnet18(pretrained=False)
        in_features = self.model.fc.in_features
        self.model.fc = nn.Linear(in_features, self.num_classes)
        
        # Load weights
        checkpoint = torch.load(model_path, map_location=self.device)
        if 'model_state_dict' in checkpoint:
            self.model.load_state_dict(checkpoint['model_state_dict'])
            print(f"Model loaded from epoch {checkpoint.get('epoch', 'unknown')}")
            print(f"Validation accuracy: {checkpoint.get('val_acc', 'unknown'):.2f}%")
        else:
            self.model.load_state_dict(checkpoint)
        
        self.model.to(self.device)
        self.model.eval()
        
        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        
        print(f"\n{'='*70}")
        print(f"Condition-Based Plant Disease Classifier Loaded")
        print(f"  Device: {self.device}")
        print(f"  Number of conditions: {self.num_classes}")
        print(f"  Model: ResNet18")
        print(f"{'='*70}\n")
    
    def predict(self, image_path, top_k=3):
        """
        Predict the condition/disease from an image.
        
        Args:
            image_path: Path to the plant image
            top_k: Number of top predictions to return
            
        Returns:
            List of (condition_name, probability) tuples
        """
        # Load and preprocess image
        image = Image.open(image_path).convert('RGB')
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        # Inference
        with torch.no_grad():
            outputs = self.model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
        
        # Get top k predictions
        top_probs, top_indices = torch.topk(probabilities, k=min(top_k, self.num_classes))
        
        results = []
        for prob, idx in zip(top_probs[0], top_indices[0]):
            condition = self.conditions[idx.item()]
            results.append((condition, prob.item()))
        
        return results, image
    
    def predict_and_display(self, image_path, top_k=3, save_path=None):
        """Predict and display results with visualization"""
        results, image = self.predict(image_path, top_k)
        
        # Print results
        print(f"\nImage: {os.path.basename(image_path)}")
        print(f"{'='*70}")
        print(f"Top {len(results)} Predictions:")
        for i, (condition, prob) in enumerate(results, 1):
            print(f"  {i}. {condition:40s} - {prob*100:6.2f}%")
        print(f"{'='*70}\n")
        
        # Create visualization
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Display image
        ax1.imshow(image)
        ax1.axis('off')
        ax1.set_title(f'Input: {os.path.basename(image_path)}', fontweight='bold', fontsize=12)
        
        # Display predictions
        conditions = [r[0] for r in results]
        probs = [r[1] * 100 for r in results]
        colors = plt.cm.RdYlGn(np.linspace(0.5, 0.9, len(results)))
        
        bars = ax2.barh(conditions, probs, color=colors)
        ax2.set_xlabel('Confidence (%)', fontweight='bold', fontsize=11)
        ax2.set_title('Condition Predictions', fontweight='bold', fontsize=12)
        ax2.set_xlim(0, 100)
        
        # Add percentage labels on bars
        for i, (bar, prob) in enumerate(zip(bars, probs)):
            ax2.text(prob + 2, i, f'{prob:.1f}%', va='center', fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=200, bbox_inches='tight')
            print(f"Visualization saved to: {save_path}")
        else:
            plt.show()
        
        plt.close()
        
        return results

def main():
    parser = argparse.ArgumentParser(description='Predict plant disease condition from image')
    parser.add_argument('--image', type=str, required=True, help='Path to plant image')
    parser.add_argument('--model', type=str, default='best_condition_model.pth', 
                        help='Path to trained model')
    parser.add_argument('--mapping', type=str, default='condition_mapping.json',
                        help='Path to condition mapping JSON')
    parser.add_argument('--top_k', type=int, default=3, 
                        help='Number of top predictions to show')
    parser.add_argument('--save', type=str, default=None,
                        help='Path to save visualization (optional)')
    
    args = parser.parse_args()
    
    # Check if files exist
    if not os.path.exists(args.image):
        print(f"Error: Image not found at {args.image}")
        return
    
    if not os.path.exists(args.model):
        print(f"Error: Model not found at {args.model}")
        return
    
    if not os.path.exists(args.mapping):
        print(f"Error: Mapping file not found at {args.mapping}")
        return
    
    # Create classifier and predict
    classifier = ConditionClassifier(args.model, args.mapping)
    results = classifier.predict_and_display(args.image, args.top_k, args.save)
    
    # Return top prediction
    top_condition, top_prob = results[0]
    
    if top_prob > 0.7:
        confidence_level = "High"
    elif top_prob > 0.4:
        confidence_level = "Medium"
    else:
        confidence_level = "Low"
    
    print(f"\n{'='*70}")
    print(f"FINAL DIAGNOSIS")
    print(f"  Condition: {top_condition}")
    print(f"  Confidence: {confidence_level} ({top_prob*100:.2f}%)")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    main()
