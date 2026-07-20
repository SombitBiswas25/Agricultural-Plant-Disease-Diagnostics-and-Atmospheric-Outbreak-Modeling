import os
import ssl
import json
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np
import math

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from pydantic import BaseModel
from typing import List
import time

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
        
        # Threshold (0.65 matches healthy/diseased leaves, rejects text/furniture/faces)
        is_leaf = similarity >= 0.65
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

# Initialize classifier
MODEL_PATH = 'best_condition_model.pth'
MAPPING_PATH = 'condition_mapping.json'

if not os.path.exists(MODEL_PATH):
    print(f"⚠️ Warning: Model file '{MODEL_PATH}' not found!")
    classifier = None
else:
    try:
        classifier = ConditionClassifier(MODEL_PATH, MAPPING_PATH)
        print(f"✓ Model loaded successfully!")
    except Exception as e:
        print(f"⚠️ Error loading model: {e}")
        classifier = None

# Load disease info database
DISEASE_INFO_PATH = 'disease_info.json'
disease_info = {}
if os.path.exists(DISEASE_INFO_PATH):
    try:
        with open(DISEASE_INFO_PATH, 'r') as f:
            disease_info = json.load(f)
        print(f"✓ Disease treatment/prevention database loaded successfully!")
    except Exception as e:
        print(f"⚠️ Error loading disease_info.json: {e}")

# Helper: Simulate PennyLane Pauli-Z expectation values from predictions for visualizer
def simulate_quantum_expectations(predictions, is_leaf):
    if not is_leaf or not predictions:
        return [0.0, 0.0, 0.0, 0.0]
    
    # We take the confidence values of the predictions
    p_vals = list(predictions.values())
    while len(p_vals) < 4:
        p_vals.append(0.01)
    
    # RY Rotation angles (theta = probability * pi)
    angles = [p * math.pi for p in p_vals[:4]]
    
    # Expected Pauli-Z measurements <Z> = cos(theta)
    expectations = [math.cos(a) for a in angles]
    
    # Apply a virtual CNOT entangling matrix effect (q_i affected by q_{i-1})
    entangled = []
    for i in range(4):
        if i == 0:
            val = expectations[0]
        else:
            val = expectations[i] * expectations[i-1]
        entangled.append(val)
        
    return entangled

# Create static directories
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
HISTORY_FILE = "diagnostics_history.json"

import pymysql
from pymysql.cursors import DictCursor

# MySQL connection settings
MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = ""
MYSQL_DB = "plant_disease_db"

# Global flag to track MySQL availability
USE_MYSQL = False

def init_mysql_database():
    global USE_MYSQL
    try:
        # Step 1: Connect to MySQL server without a database name to create database if not exists
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            autocommit=True
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}")
        conn.close()
        
        # Step 2: Connect to specific database and create table if not exists
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            autocommit=True
        )
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS diagnostics_history (
                    id BIGINT PRIMARY KEY,
                    condition_name VARCHAR(255) NOT NULL,
                    confidence DOUBLE NOT NULL,
                    timestamp VARCHAR(255) NOT NULL,
                    quantum_states VARCHAR(512) NOT NULL,
                    image_url VARCHAR(512) NOT NULL
                )
            """)
            
            # Step 3: Migrate existing JSON data to MySQL if table is empty
            cursor.execute("SELECT COUNT(*) FROM diagnostics_history")
            count_row = cursor.fetchone()
            count = count_row[0] if count_row else 0
            
            if count == 0 and os.path.exists(HISTORY_FILE):
                try:
                    with open(HISTORY_FILE, "r") as f:
                        json_data = json.load(f)
                    if isinstance(json_data, list) and len(json_data) > 0:
                        print(f"Migrating {len(json_data)} history records from JSON to MySQL...")
                        for item in json_data:
                            q_states_str = json.dumps(item.get("quantum_states", [0.0, 0.0, 0.0, 0.0]))
                            cursor.execute("""
                                INSERT INTO diagnostics_history (id, condition_name, confidence, timestamp, quantum_states, image_url)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (item["id"], item["condition"], item["confidence"], item["timestamp"], q_states_str, item["image_url"]))
                        print("✓ Migration completed successfully.")
                except Exception as me:
                    print(f"⚠️ Migration failed: {me}")
                    
        conn.close()
        USE_MYSQL = True
        print("✓ Connected to MySQL database successfully.")
    except Exception as e:
        USE_MYSQL = False
        print(f"⚠️ MySQL connection failed: {e}. Falling back to JSON database file.")

# Run MySQL initialization
init_mysql_database()

def load_history_data():
    global USE_MYSQL
    if USE_MYSQL:
        try:
            conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB,
                cursorclass=DictCursor
            )
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM diagnostics_history ORDER BY id DESC")
                rows = cursor.fetchall()
            conn.close()
            
            history = []
            for row in rows:
                try:
                    q_states = json.loads(row["quantum_states"])
                except Exception:
                    q_states = [0.0, 0.0, 0.0, 0.0]
                history.append({
                    "id": row["id"],
                    "condition": row["condition_name"],
                    "confidence": row["confidence"],
                    "timestamp": row["timestamp"],
                    "quantum_states": q_states,
                    "image_url": row["image_url"]
                })
            return history
        except Exception as e:
            print(f"⚠️ Error reading from MySQL: {e}. Falling back to JSON file.")
            
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history_data(data):
    global USE_MYSQL
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error writing to JSON file: {e}")
        
    if USE_MYSQL:
        try:
            conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB,
                autocommit=True
            )
            with conn.cursor() as cursor:
                if len(data) == 0:
                    cursor.execute("TRUNCATE TABLE diagnostics_history")
            conn.close()
        except Exception as e:
            print(f"⚠️ Error resetting MySQL table: {e}")

class DiagnosticLog(BaseModel):
    condition: str
    confidence: float
    timestamp: str
    quantum_states: List[float]
    image_url: str

# FastAPI App
app = FastAPI(title="Bio-Quantum Plant Diagnostic Suite Backend")

# Mount Static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/api/model-info")
def get_model_info():
    if classifier is None:
        return JSONResponse(status_code=500, content={"error": "Classifier model is not initialized."})
    
    # Format accuracy display
    val_acc_val = classifier.val_acc
    if isinstance(val_acc_val, float):
        val_acc_str = f"{val_acc_val:.2f}%"
    elif isinstance(val_acc_val, str) and "%" not in val_acc_val and val_acc_val != 'N/A':
        try:
            val_acc_str = f"{float(val_acc_val):.2f}%"
        except ValueError:
            val_acc_str = val_acc_val
    else:
        val_acc_str = str(val_acc_val)
        
    return {
        "model_info": {
            "val_acc": val_acc_str,
            "device": str(classifier.device),
            "num_classes": classifier.num_classes,
            "conditions": classifier.conditions
        },
        "disease_info": disease_info
    }

@app.post("/api/predict")
async def api_predict(file: UploadFile = File(...)):
    if classifier is None:
        raise HTTPException(status_code=500, detail="Classifier model not loaded on server.")
    
    try:
        # Load uploaded image
        image = Image.open(file.file).convert('RGB')
        
        # Check leaf similarity gatekeeper
        is_leaf, similarity = classifier.is_plant_leaf(image)
        if not is_leaf:
            return {
                "is_leaf": False,
                "leaf_similarity": float(similarity),
                "predictions": [],
                "top_condition": "",
                "treatment_info": {},
                "quantum_states": [0.0, 0.0, 0.0, 0.0],
                "image_url": ""
            }
            
        # Run prediction
        raw_predictions = classifier.predict(image, top_k=5)
        
        # Format predictions list
        formatted_predictions = []
        for cond, prob in raw_predictions.items():
            formatted_predictions.append({
                "condition": cond,
                "probability": float(prob)
            })
            
        top_condition = list(raw_predictions.keys())[0] if raw_predictions else "healthy"
        
        # Get treatment advice
        treatment_advice = disease_info.get(top_condition, {
            "title": top_condition,
            "meds": ["No detailed treatments available."],
            "care": ["Refer to generic agronomic guidance."],
            "prevention": ["Keep crops inspected and healthy."]
        })
        
        # Get simulated PennyLane quantum wires state measurements
        quantum_states = simulate_quantum_expectations(raw_predictions, is_leaf=True)
        
        # Save image to upload folder for server-side persistence
        file_id = int(time.time() * 1000)
        filename = f"{file_id}.jpg"
        filepath = os.path.join(UPLOAD_DIR, filename)
        image.save(filepath, "JPEG")
        image_url = f"/static/uploads/{filename}"
        
        return {
            "is_leaf": True,
            "leaf_similarity": float(similarity),
            "predictions": formatted_predictions,
            "top_condition": top_condition,
            "treatment_info": treatment_advice,
            "quantum_states": quantum_states,
            "image_url": image_url
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

@app.post("/api/log-diagnostic")
def log_diagnostic(log: DiagnosticLog):
    global USE_MYSQL
    log_entry = {
        "id": int(time.time() * 1000),
        "condition": log.condition,
        "confidence": log.confidence,
        "timestamp": log.timestamp,
        "quantum_states": log.quantum_states,
        "image_url": log.image_url
    }
    
    saved_to_mysql = False
    if USE_MYSQL:
        try:
            conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB,
                autocommit=True
            )
            with conn.cursor() as cursor:
                q_states_str = json.dumps(log.quantum_states)
                cursor.execute("""
                    INSERT INTO diagnostics_history (id, condition_name, confidence, timestamp, quantum_states, image_url)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (log_entry["id"], log.condition, log.confidence, log.timestamp, q_states_str, log.image_url))
            conn.close()
            saved_to_mysql = True
        except Exception as e:
            print(f"⚠️ Error logging to MySQL: {e}. Attempting JSON write backup.")
            
    try:
        history = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    history = json.load(f)
            except Exception:
                history = []
        history.insert(0, log_entry)
        if len(history) > 50:
            history.pop()
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error writing backup log to JSON file: {e}")
        if not saved_to_mysql:
            raise HTTPException(status_code=500, detail=f"Database write error: {str(e)}")
            
    return {"status": "success", "entry": log_entry}

@app.get("/api/history")
def get_history():
    return load_history_data()

@app.delete("/api/history")
def clear_history():
    save_history_data([])
    if os.path.exists(UPLOAD_DIR):
        for file in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error purging file {file_path}: {e}")
    return {"status": "success", "message": "History and uploads cleared"}

@app.delete("/api/history/{id}")
def delete_history_item(id: int):
    global USE_MYSQL
    
    deleted_from_mysql = False
    deleted_item_image = None
    
    if USE_MYSQL:
        try:
            conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB,
                cursorclass=DictCursor,
                autocommit=True
            )
            with conn.cursor() as cursor:
                cursor.execute("SELECT image_url FROM diagnostics_history WHERE id = %s", (id,))
                row = cursor.fetchone()
                if row:
                    deleted_item_image = row["image_url"]
                cursor.execute("DELETE FROM diagnostics_history WHERE id = %s", (id,))
            conn.close()
            deleted_from_mysql = True
        except Exception as e:
            print(f"⚠️ Error deleting from MySQL: {e}. Checking JSON backup.")
            
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except Exception:
            history = []
            
    if not deleted_item_image:
        deleted_item = next((item for item in history if item["id"] == id), None)
        if deleted_item:
            deleted_item_image = deleted_item.get("image_url")
            
    updated_history = [item for item in history if item["id"] != id]
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(updated_history, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error syncing delete to JSON file: {e}")
        
    if deleted_item_image:
        img_path = deleted_item_image.lstrip("/")
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
            except Exception as e:
                print(f"Error deleting image {img_path}: {e}")
                
    return {"status": "success", "message": "Record deleted"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=7860, reload=True)
