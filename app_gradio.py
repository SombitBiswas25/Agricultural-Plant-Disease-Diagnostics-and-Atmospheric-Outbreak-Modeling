import gradio as gr
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import json
import os
import numpy as np
import ssl

# Bypass SSL certificate checks for model downloads if necessary
ssl._create_default_https_context = ssl._create_unverified_context


class ConditionClassifier:
    """Inference class for condition-based plant disease detection."""
    
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
            self.val_acc = checkpoint.get('val_acc', 'N/A')
        else:
            self.model.load_state_dict(checkpoint)
            self.val_acc = 'N/A'
        
        self.model.to(self.device)
        self.model.eval()
        
        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        # Load gatekeeper (pretrained ResNet18 for leaf classification gating)
        try:
            self.gatekeeper = models.resnet18(pretrained=True)
            self.gatekeeper_features = nn.Sequential(*list(self.gatekeeper.children())[:-1])
            self.gatekeeper_features.to(self.device)
            self.gatekeeper_features.eval()
            self._initialize_leaf_template(model_path)
        except Exception as e:
            print(f"⚠️ Warning: Failed to load gatekeeper model: {e}")
            self.leaf_template = None

    def _initialize_leaf_template(self, model_path):
        """Create a reference 'leaf' vector from your actual dataset."""
        base_dir = os.path.dirname(os.path.abspath(model_path))
        val_dir = os.path.join(base_dir, 'data/val')
        if not os.path.exists(val_dir):
            self.leaf_template = None
            print(f"⚠️ Warning: Validation directory {val_dir} not found for template initialization.")
            return

        # Find healthy folders first to get good leaf references
        healthy_dirs = [d for d in os.listdir(val_dir) if 'healthy' in d.lower() and os.path.isdir(os.path.join(val_dir, d))]
        image_paths = []
        for hd in healthy_dirs[:3]:
            folder_path = os.path.join(val_dir, hd)
            files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if files:
                image_paths.append(os.path.join(folder_path, files[0]))
        
        # Fallback to any images if no healthy folder is found
        if not image_paths:
            for root, dirs, files in os.walk(val_dir):
                for f in files:
                    if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                        image_paths.append(os.path.join(root, f))
                        if len(image_paths) >= 3:
                            break
                if len(image_paths) >= 3:
                    break
        
        # Extract features and average
        feats = []
        for path in image_paths:
            try:
                img = Image.open(path).convert('RGB')
                tensor = self.transform(img).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    feat = self.gatekeeper_features(tensor).view(-1)
                    feat = feat / torch.norm(feat)
                    feats.append(feat)
            except Exception as e:
                print(f"Error loading template image {path}: {e}")
        
        if feats:
            self.leaf_template = torch.stack(feats).mean(dim=0)
            self.leaf_template = self.leaf_template / torch.norm(self.leaf_template)
            print(f"✓ Leaf template initialized using {len(feats)} images.")
        else:
            self.leaf_template = None
            print("⚠️ Warning: Could not initialize leaf template. Similarity check disabled.")

    def is_plant_leaf(self, image):
        """Checks if the uploaded image resembles a plant leaf using latent cosine similarity."""
        if self.leaf_template is None:
            return True, 1.0
        
        # Ensure RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            feat = self.gatekeeper_features(input_tensor).view(-1)
            feat = feat / torch.norm(feat)
            similarity = torch.dot(feat, self.leaf_template).item()
        
        # Threshold (0.55 matches healthy/diseased leaves, rejects text/furniture/faces)
        is_leaf = similarity >= 0.55
        return is_leaf, similarity
    
    def predict(self, image, top_k=5):
        """Predict disease condition from PIL image."""
        if image is None:
            return None
        
        # Ensure RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Preprocess
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        # Inference
        with torch.no_grad():
            outputs = self.model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
        
        # Get top k predictions
        top_probs, top_indices = torch.topk(probabilities, k=min(top_k, self.num_classes))
        
        results = {}
        for prob, idx in zip(top_probs[0], top_indices[0]):
            condition = self.conditions[idx.item()]
            results[condition] = float(prob.item())
        
        return results

# Initialize classifier (will be loaded when the app starts)
MODEL_PATH = 'best_condition_model.pth'
MAPPING_PATH = 'condition_mapping.json'

# Check if model exists
if not os.path.exists(MODEL_PATH):
    print(f"⚠️ Warning: Model file '{MODEL_PATH}' not found!")
    print("Please train the model first using: python train_condition_model.py --data_dir data --epochs 10")
    classifier = None
else:
    try:
        classifier = ConditionClassifier(MODEL_PATH, MAPPING_PATH)
        print(f"✓ Model loaded successfully!")
        print(f"✓ Validation Accuracy: {classifier.val_acc}")
    except Exception as e:
        print(f"⚠️ Error loading model: {e}")
        classifier = None

DISEASE_INFO_PATH = 'disease_info.json'
if os.path.exists(DISEASE_INFO_PATH):
    try:
        with open(DISEASE_INFO_PATH, 'r') as f:
            disease_info = json.load(f)
        print(f"✓ Disease treatment/prevention database loaded successfully!")
    except Exception as e:
        print(f"⚠️ Error loading disease_info.json: {e}")
        disease_info = {}
else:
    print(f"⚠️ Warning: '{DISEASE_INFO_PATH}' not found!")
    disease_info = {}

def generate_treatment_html(condition):
    if not disease_info or condition not in disease_info:
        return f"""
        <div class="treatment-card disease-card">
            <div class="treatment-header">
                <div class="treatment-badge">
                    <span class="treatment-icon">❓</span>
                    <span class="treatment-title">No detailed advice available for: {condition}</span>
                </div>
            </div>
        </div>
        """
    
    info = disease_info[condition]
    title = info.get("title", condition)
    meds = info.get("meds", [])
    care = info.get("care", [])
    prevention = info.get("prevention", [])
    
    # Render healthy card differently
    if condition == "healthy":
        card_class = "healthy-card"
        icon = "🟢"
    else:
        card_class = "disease-card"
        icon = "⚠️"
        
    html = f"""
    <div class="treatment-card {card_class}">
        <div class="treatment-header">
            <div class="treatment-badge">
                <span class="treatment-icon">{icon}</span>
                <span class="treatment-title">{title}</span>
            </div>
        </div>
        
        <div class="treatment-body">
            <div class="treatment-group">
                <div class="group-header meds-header">
                    <span class="group-icon">💊</span>
                    <h4>Recommended Treatments & Medications</h4>
                </div>
                <ul class="group-list">
                    {"".join(f"<li>{m}</li>" for m in meds)}
                </ul>
            </div>
            
            <div class="treatment-group">
                <div class="group-header care-header">
                    <span class="group-icon">🌿</span>
                    <h4>Plant Care Guidelines</h4>
                </div>
                <ul class="group-list">
                    {"".join(f"<li>{c}</li>" for c in care)}
                </ul>
            </div>
            
            <div class="treatment-group">
                <div class="group-header prevent-header">
                    <span class="group-icon">🛡️</span>
                    <h4>Prevention & Control</h4>
                </div>
                <ul class="group-list">
                    {"".join(f"<li>{p}</li>" for p in prevention)}
                </ul>
            </div>
        </div>
    </div>
    """
    return html

def predict_disease(image):
    """Main prediction function for Gradio."""
    if classifier is None:
        error_label = {"Error": 1.0}
        error_html = "<div class='error-box'><h4>Model not loaded</h4><p>Please train the model first.</p></div>"
        return error_label, error_html
    
    if image is None:
        error_label = {"Error": 1.0}
        error_html = "<div class='error-box'><h4>No Image Provided</h4><p>Please upload or drop an image.</p></div>"
        return error_label, error_html
    
    try:
        # Check if the uploaded image resembles a plant leaf
        is_leaf, similarity = classifier.is_plant_leaf(image)
        if not is_leaf:
            error_label = {
                "❌ INVALID: Not a plant leaf image": 1.0,
                f"Similarity Score: {similarity:.2f} (Expected >= 0.55)": 0.0
            }
            warning_html = f"""
            <div class="warning-box">
                <h4 style="margin: 0 0 8px 0; color: #856404;">⚠️ Not a Plant Leaf Image Detected</h4>
                <p style="margin: 0 0 8px 0;">The uploaded image does not resemble a plant leaf (Similarity: <b>{similarity:.2f}</b>, Expected: <b>>= 0.55</b>).</p>
                <p style="margin: 0; font-size: 0.9em;">Please upload a clear, focused image of a plant leaf.</p>
            </div>
            """
            return error_label, warning_html
            
        results = classifier.predict(image, top_k=5)
        
        # Get top predicted condition
        top_condition = list(results.keys())[0] if results else "healthy"
        treatment_html = generate_treatment_html(top_condition)
        
        return results, treatment_html
    except Exception as e:
        error_label = {"Error": 1.0}
        error_html = f"""
        <div class="error-box">
            <h4 style="margin: 0 0 8px 0; color: #721c24;">❌ Prediction Failed</h4>
            <p style="margin: 0;">{str(e)}</p>
        </div>
        """
        return error_label, error_html

def format_info():
    """Return model information."""
    if classifier is None:
        return "❌ Model not loaded"
    
    info = f"""
    ### 📊 Model Information
    - **Model Type:** ResNet18 (Transfer Learning)
    - **Classification Type:** Condition-Based (Cross-Breed Compatible)
    - **Number of Conditions:** {classifier.num_classes}
    - **Validation Accuracy:** {classifier.val_acc if isinstance(classifier.val_acc, str) else f'{classifier.val_acc:.2f}%'}
    - **Device:** {classifier.device}
    
    ### 🌿 Detected Conditions
    """
    
    for i, cond in enumerate(classifier.conditions, 1):
        info += f"\n{i}. {cond}"
    
    return info

# Custom CSS for better styling
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap');

/* Global Container Styling */
.gradio-container {
    font-family: 'Inter', -apple-system, sans-serif !important;
    background-color: var(--background-fill-primary, #f8fafc) !important;
    max-width: 1200px !important;
    margin: 40px auto !important;
    padding: 0 20px !important;
}

/* Typography Overrides */
h1, h2, h3, h4, .treatment-title, .gr-button, .output-class {
    font-family: 'Outfit', sans-serif !important;
}

/* Glassmorphism Title Card */
#title {
    text-align: center;
    background: linear-gradient(135deg, #115e59 0%, #0d9488 100%);
    padding: 40px 20px;
    border-radius: 20px;
    color: white;
    margin-bottom: 24px;
    box-shadow: 0 10px 25px -5px rgba(13, 148, 136, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

#title h1 {
    font-size: 2.5rem !important;
    font-weight: 800 !important;
    margin: 0 0 10px 0 !important;
    letter-spacing: -0.5px !important;
    color: #ffffff !important;
}

#title h3 {
    font-size: 1.2rem !important;
    font-weight: 500 !important;
    opacity: 0.9 !important;
    margin: 0 !important;
    color: #ccfbf1 !important;
}

#subtitle {
    text-align: center;
    color: var(--body-text-color, #475569);
    margin-bottom: 30px;
    font-size: 1.05rem;
    line-height: 1.6;
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
}

/* Card Styling for left and right columns */
#left-column, #right-column {
    background: var(--block-background-fill, #ffffff) !important;
    border: 1px solid var(--border-color-primary, #e2e8f0) !important;
    border-radius: 20px !important;
    padding: 24px !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    margin-bottom: 24px !important;
}

/* Customize Image Upload Block */
#upload-card {
    border-radius: 20px !important;
    border: 2px dashed #0d9488 !important;
    background: var(--background-fill-secondary, #f1f5f9) !important;
    overflow: hidden;
}

/* Primary Button Styling */
#predict-btn {
    background: linear-gradient(135deg, #0d9488 0%, #115e59 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    color: white !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    padding: 14px 28px !important;
    box-shadow: 0 4px 14px 0 rgba(13, 148, 136, 0.4) !important;
    transition: all 0.2s ease !important;
    cursor: pointer;
    margin-top: 10px;
}

#predict-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px 0 rgba(13, 148, 136, 0.5) !important;
}

#predict-btn:active {
    transform: translateY(0) !important;
}

/* Guide & Tips box styling */
.guide-box {
    background: var(--background-fill-secondary, #f8fafc);
    border: 1px solid var(--border-color-primary, #e2e8f0);
    border-radius: 16px;
    padding: 20px;
    margin-top: 20px;
}

.guide-box h4 {
    margin-top: 0;
    margin-bottom: 12px;
    color: #0d9488;
    font-size: 1.1rem;
    font-weight: 700;
}

.guide-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 12px;
}

.guide-item:last-child {
    margin-bottom: 0;
}

.guide-icon {
    font-size: 1.2rem;
    background: rgba(13, 148, 136, 0.1);
    color: #0d9488;
    border-radius: 50%;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.guide-text {
    font-size: 0.95rem;
    line-height: 1.5;
    color: var(--body-text-color, #334155);
}

/* Treatment Card Styling (Behance layout) */
.treatment-card {
    background: var(--block-background-fill, #ffffff);
    border: 1px solid var(--border-color-primary, #e2e8f0);
    border-radius: 18px;
    padding: 24px;
    margin-top: 24px;
    box-shadow: 0 10px 25px -10px rgba(0, 0, 0, 0.05);
}

.healthy-card {
    border-left: 6px solid #10b981;
    background: linear-gradient(to right, rgba(16, 185, 129, 0.02), transparent);
}

.disease-card {
    border-left: 6px solid #f43f5e;
    background: linear-gradient(to right, rgba(244, 63, 94, 0.02), transparent);
}

.treatment-header {
    margin-bottom: 20px;
    border-bottom: 1px solid var(--border-color-primary, #f1f5f9);
    padding-bottom: 16px;
}

.treatment-badge {
    display: inline-flex;
    align-items: center;
    gap: 12px;
}

.treatment-icon {
    font-size: 2rem;
}

.treatment-title {
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--block-title-text-color, #0f172a);
}

.treatment-body {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.treatment-group {
    background: var(--background-fill-secondary, #f8fafc);
    border-radius: 12px;
    padding: 18px;
    border: 1px solid var(--border-color-secondary, #e2e8f0);
}

.group-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
}

.group-header h4 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 700;
}

.meds-header h4 {
    color: #10b981;
}

.care-header h4 {
    color: #f59e0b;
}

.prevent-header h4 {
    color: #3b82f6;
}

.group-list {
    margin: 0;
    padding-left: 20px;
    list-style-type: square;
}

.group-list li {
    font-size: 0.95rem;
    line-height: 1.6;
    color: var(--body-text-color, #475569);
    margin-bottom: 8px;
}

.group-list li:last-child {
    margin-bottom: 0;
}

/* Warnings and errors */
.warning-box, .error-box {
    border-radius: 14px;
    padding: 20px;
    margin-top: 24px;
}

.warning-box {
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid #f59e0b;
    border-left: 6px solid #f59e0b;
}

.warning-box h4 {
    margin-top: 0;
    margin-bottom: 8px;
    color: #d97706;
    font-weight: 700;
}

.warning-box p {
    margin: 0;
    color: var(--body-text-color, #475569);
    line-height: 1.5;
}

.error-box {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid #ef4444;
    border-left: 6px solid #ef4444;
}

.error-box h4 {
    margin-top: 0;
    margin-bottom: 8px;
    color: #dc2626;
    font-weight: 700;
}

.error-box p {
    margin: 0;
    color: var(--body-text-color, #475569);
    line-height: 1.5;
}

/* Footer / Tech stack section */
.footer-container {
    text-align: center;
    margin-top: 40px;
    padding-top: 24px;
    border-top: 1px solid var(--border-color-primary, #e2e8f0);
}

.footer-container h4 {
    color: var(--block-title-text-color, #0f172a);
    margin-bottom: 6px;
    font-size: 1.1rem;
}

.footer-container p {
    color: #64748b;
    font-size: 0.92rem;
    margin: 4px 0;
}
"""

# Create Gradio interface
with gr.Blocks(css=custom_css, title="Plant Disease Detection") as demo:
    
    gr.HTML("""
        <div id="title">
            <h1>🌿 Plant Disease Diagnostic Dashboard</h1>
            <h3>Cross-Breed Symptom Scan & Quantum Analysis</h3>
        </div>
    """)
    
    gr.HTML("""
        <div id="subtitle">
            This advanced diagnostic system scans agricultural crops for visual symptoms of diseases. 
            By mapping leaves to symptom-based feature spaces rather than plant species, the classification performs 
            accurately across multiple varieties and plant breeds.
        </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=1, elem_id="left-column"):
            gr.Markdown("### 📤 Scan New Leaf")
            image_input = gr.Image(
                type="pil",
                label="Select or Drag Image",
                sources=["upload", "clipboard"],
                height=350,
                elem_id="upload-card"
            )
            
            predict_btn = gr.Button("🔍 Run Disease Diagnosis", variant="primary", size="lg", elem_id="predict-btn")
            
            # Guidelines block with clean HTML layout
            gr.HTML("""
                <div class="guide-box">
                    <h4>💡 Quick Scanning Guidelines</h4>
                    <div class="guide-item">
                        <div class="guide-icon">🎯</div>
                        <div class="guide-text"><b>Focus on Symptoms:</b> Center the affected spot or leaf area in the camera frame.</div>
                    </div>
                    <div class="guide-item">
                        <div class="guide-icon">☀️</div>
                        <div class="guide-text"><b>Good Lighting:</b> Avoid shadows or dark background environments for accurate color scanning.</div>
                    </div>
                    <div class="guide-item">
                        <div class="guide-icon">🌿</div>
                        <div class="guide-text"><b>Single Leaf:</b> For best results, scan one leaf at a time rather than a whole branch.</div>
                    </div>
                </div>
            """)
            
        with gr.Column(scale=1, elem_id="right-column"):
            gr.Markdown("### 📊 Diagnostic Results")
            output_label = gr.Label(
                num_top_classes=5,
                label="Confidence Scores",
                show_label=True
            )
            
            treatment_info = gr.HTML(
                label="Treatments & Care Guide",
                elem_id="treatment-info"
            )
            
            gr.Markdown("""
                *To test the validation gates, upload an image of text or household items; the system will detect and reject the non-plant image.*
            """)
    
    with gr.Accordion("📋 Model Information & Supported Conditions", open=False):
        model_info = gr.Markdown(format_info(), elem_id="model-info")
    
    # Set up prediction
    predict_btn.click(
        fn=predict_disease,
        inputs=image_input,
        outputs=[output_label, treatment_info]
    )
    
    # Also predict on image change (optional)
    image_input.change(
        fn=predict_disease,
        inputs=image_input,
        outputs=[output_label, treatment_info]
    )
    
    gr.HTML("""
        <div class="footer-container">
            <h4>🔬 About Plant Disease Analysis using CNN & Quantum Computing</h4>
            <p>B.Tech Final Year Capstone Project</p>
            <p><b>Backend Stack:</b> PyTorch • ResNet18 • PennyLane QML Simulator • Gradio</p>
        </div>
    """)

# Launch the app
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",  # Allow external connections
        server_port=7860,
        share=False,  # Set to True to create public link
        show_error=True,
        inbrowser=True  # Automatically open in browser
    )
