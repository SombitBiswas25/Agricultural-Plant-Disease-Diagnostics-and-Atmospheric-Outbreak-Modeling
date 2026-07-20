# AgriShield: Agricultural Plant Disease Diagnostics and Atmospheric Outbreak Modeling

An AI-powered agricultural diagnostic system combining Classical Deep Learning (ResNet-18), Hybrid Quantum Machine Learning (PennyLane QML), Out-of-Distribution (OOD) Gatekeeping, Cross-Breed Disease Decoupling, and interactive FastAPI/Gradio web application interfaces.

## 🚀 Features
- **Cross-Breed Condition Mapping**: Decouples crop species from pathogen conditions (38 classes -> 21 generalized disease conditions).
- **Out-of-Distribution (OOD) Gatekeeper**: ResNet-18 embedding space cosine similarity filtering to reject non-leaf image uploads.
- **Hybrid Quantum Neural Network (QNN)**: 4-qubit Variational Quantum Circuit using PennyLane (`default.qubit`) integrated into PyTorch via `TorchLayer`.
- **Full Web Application**: FastAPI REST backend server and Gradio UI with real-time diagnostic reporting and treatment recommendations.
- **Viva Voce Documentation**: Includes complete technical reports and viva voce guides (`.docx`).

## 📁 Key Files & Modules
- `app.py` : FastAPI REST server with OOD Gatekeeper, prediction endpoint, and history logging.
- `app_gradio.py` : Interactive Gradio web interface for user diagnostic demonstrations.
- `train_condition_model.py` : PyTorch training pipeline with data augmentations and cross-breed condition mapping.
- `train_classical.py` : Baseline ResNet18 classifier training script.
- `hybrid_model.py` : HybridNet architecture combining ResNet18 feature extractor with PennyLane QML layer.
- `predict_condition.py` : Single image inference script with top-K prediction probabilities.
- `split_dataset.py` : Utility script to partition raw dataset into train/validation folders.
- `disease_info.json` : Structured knowledge base for symptoms, chemical treatments, and organic remedies.
- `Plant_Disease_Detection_Viva_Guide.docx` : Complete 50 Q&A Viva Voce Preparation Guide.

## 🛠️ Installation & Setup
1. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start the FastAPI Web Server:
   ```bash
   python3 app.py
   ```
3. Or launch the Gradio Interactive UI:
   ```bash
   python3 app_gradio.py
   ```

## 📊 Requirements
- `torch`, `torchvision`, `pennylane`, `fastapi`, `uvicorn`, `gradio`, `scikit-learn`, `numpy`, `pillow`, `matplotlib`, `seaborn`, `python-docx`
