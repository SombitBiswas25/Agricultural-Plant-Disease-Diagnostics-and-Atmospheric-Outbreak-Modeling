import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    """Set shading color for a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set padding for a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>\n'
        f'  <w:top w:w="{top}" w:type="dxa"/>\n'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>\n'
        f'  <w:left w:w="{left}" w:type="dxa"/>\n'
        f'  <w:right w:w="{right}" w:type="dxa"/>\n'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_table_borders(table, color="CCCCCC", sz="4", val="single"):
    """Set subtle borders for a table."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:insideV w:val="none"/>\n'
        f'  <w:left w:val="none"/>\n'
        f'  <w:right w:val="none"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def create_callout_box(doc, title, text, bg_hex="F0FDF4", border_hex="1B4D3E"):
    """Create a callout box with a colored left border and light shading."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_hex)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    # Border: thick left border, no top/bottom/right
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>\n'
        f'  <w:left w:val="single" w:sz="24" w:space="0" w:color="{border_hex}"/>\n'
        f'  <w:top w:val="none"/>\n'
        f'  <w:right w:val="none"/>\n'
        f'  <w:bottom w:val="none"/>\n'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    run_t = p.add_run(f"📌 {title}\n")
    run_t.bold = True
    run_t.font.name = "Calibri"
    run_t.font.size = Pt(11)
    run_t.font.color.rgb = RGBColor(0x1B, 0x4D, 0x3E)
    
    run_b = p.add_run(text)
    run_b.font.name = "Calibri"
    run_b.font.size = Pt(10.5)
    run_b.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

def add_styled_heading(doc, text, level):
    """Add styled headings with custom colors and fonts."""
    h = doc.add_heading(text, level=level)
    h.paragraph_format.keep_with_next = True
    run = h.runs[0]
    run.font.name = "Arial"
    if level == 1:
        run.font.size = Pt(18)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x1B, 0x4D, 0x3E) # Forest Green
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(8)
    elif level == 2:
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x2E, 0x7D, 0x32) # Emerald
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(6)
    elif level == 3:
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x37, 0x47, 0x4F) # Dark Slate
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(4)
    return h

def build_document():
    doc = docx.Document()

    # Configure Margins (1 inch everywhere)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Set normal style font
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Calibri'
    font.size = Pt(11)
    font.color.rgb = RGBColor(0x2D, 0x37, 0x48)

    # -------------------------------------------------------------
    # COVER / TITLE BLOCK
    # -------------------------------------------------------------
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(20)
    p_title.paragraph_format.space_after = Pt(4)
    run_t = p_title.add_run("B.TECH FINAL YEAR PROJECT VIVA COMPREHENSIVE GUIDE")
    run_t.font.name = "Arial"
    run_t.font.size = Pt(22)
    run_t.font.bold = True
    run_t.font.color.rgb = RGBColor(0x1B, 0x4D, 0x3E)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(18)
    run_sub = p_sub.add_run("AgriShield: AI-Powered Plant Disease Detection with Cross-Breed Condition Mapping & Quantum-Classical Hybrid Deep Neural Networks")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(14)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

    # Metadata Table
    meta_table = doc.add_table(rows=4, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(meta_table, color="D1D5DB")
    meta_data = [
        ("Project Domain:", "Computer Vision, Deep Learning, Quantum ML (QML), Web Systems"),
        ("Core Architecture:", "ResNet18 CNN + 4-Qubit Variational Quantum Circuit (PennyLane)"),
        ("Deployment Stack:", "FastAPI (REST Server) + Gradio Web Interface + PyTorch"),
        ("Document Purpose:", "Final Viva Voce Examination Preparation & Complete Technical Reference")
    ]
    for idx, (k, v) in enumerate(meta_data):
        r = meta_table.rows[idx]
        c0, c1 = r.cells[0], r.cells[1]
        c0.width = Inches(2.2)
        c1.width = Inches(4.3)
        set_cell_background(c0, "F3F4F6")
        set_cell_background(c1, "FAFAFA")
        set_cell_margins(c0, 80, 80, 120, 120)
        set_cell_margins(c1, 80, 80, 120, 120)
        
        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_after = Pt(0)
        run0 = p0.add_run(k)
        run0.bold = True
        run0.font.size = Pt(10)
        
        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_after = Pt(0)
        run1 = p1.add_run(v)
        run1.font.size = Pt(10)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    create_callout_box(
        doc,
        "VIVA PREPARATION OVERVIEW",
        "This document contains the complete technical specification, end-to-end workflow, architectural design, technology stack matrix, and 50 comprehensive Viva Voce Q&As covering Core Machine Learning, Deep Learning, Quantum ML (PennyLane), System Gatekeeping, REST APIs, and Defensive Tricky Viva Questions."
    )

    # -------------------------------------------------------------
    # SECTION 1: FULL TECHNOLOGY STACK MATRIX
    # -------------------------------------------------------------
    add_styled_heading(doc, "1. Full Technology Stack Matrix", level=1)
    
    p = doc.add_paragraph(
        "The project integrates state-of-the-art classical computer vision, quantum circuit simulation, asynchronous backend web frameworks, and interactive frontend interfaces into a unified agricultural diagnostic system."
    )
    p.paragraph_format.space_after = Pt(8)

    tech_table = doc.add_table(rows=1, cols=4)
    tech_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = tech_table.rows[0].cells
    hdr_titles = ["Layer / Component", "Technology / Framework", "Version / Specifications", "Role & Function in Project"]
    col_widths = [Inches(1.5), Inches(1.8), Inches(1.3), Inches(2.5)]
    
    for i, title in enumerate(hdr_titles):
        hdr_cells[i].width = col_widths[i]
        set_cell_background(hdr_cells[i], "1B4D3E")
        set_cell_margins(hdr_cells[i], 100, 100, 100, 100)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(title)
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        run.font.size = Pt(10)

    tech_stack = [
        ("Deep Learning Framework", "PyTorch", "2.x+", "Model training, tensor computation, backpropagation, CUDA/CPU execution."),
        ("Vision Backbone", "Torchvision (ResNet-18)", "0.15+", "Pretrained 18-layer Residual Network for deep visual feature extraction."),
        ("Quantum ML Engine", "PennyLane", "0.33+", "Quantum circuit simulation, default.qubit 4-qubit device, qml.QNode PyTorch integration."),
        ("Web REST Server", "FastAPI + Uvicorn", "0.100+", "Asynchronous REST API endpoints for image upload, inference, and history logging."),
        ("Interactive Web UI", "Gradio", "4.x+", "Web application for real-time leaf image upload, confidence display, and advisory rendering."),
        ("Computer Vision & Utilities", "Pillow (PIL) & OpenCV", "9.x+", "Image loading, resizing, format conversion, and pixel array manipulation."),
        ("Data Processing", "NumPy & Pandas", "1.24+", "Array transformations, feature vector scaling, matrix manipulation, logging."),
        ("Evaluation & Metrics", "Scikit-Learn", "1.2+", "Classification metrics, confusion matrix calculations, precision/recall analysis."),
        ("Visualization", "Matplotlib & Seaborn", "3.7+", "Plotting training loss/accuracy curves and heatmaps for confusion matrices."),
        ("OOD Gatekeeper", "ResNet18 Feature Vector Space", "Custom", "Cosine similarity filtering to reject non-leaf images prior to model inference."),
        ("Database / Storage", "JSON File Persistence", "Native", "condition_mapping.json, disease_info.json, and diagnostics_history.json.")
    ]

    for row_idx, data in enumerate(tech_stack):
        row = tech_table.add_row()
        bg_color = "F9FAFB" if row_idx % 2 == 0 else "FFFFFF"
        for col_idx, text in enumerate(data):
            cell = row.cells[col_idx]
            cell.width = col_widths[col_idx]
            set_cell_background(cell, bg_color)
            set_cell_margins(cell, 80, 80, 100, 100)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(text)
            run.font.size = Pt(9.5)
            if col_idx == 0:
                run.bold = True

    set_table_borders(tech_table, color="D1D5DB")
    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # -------------------------------------------------------------
    # SECTION 2: END-TO-END PROJECT WORKFLOW & ARCHITECTURE
    # -------------------------------------------------------------
    add_styled_heading(doc, "2. End-to-End Project Workflow & Architecture", level=1)

    add_styled_heading(doc, "2.1 System Architecture Overview", level=2)
    p = doc.add_paragraph(
        "The overall workflow consists of five distinct pipeline stages: Data Ingestion & Condition Decoupling, Out-of-Distribution (OOD) Gatekeeping, Feature Extraction & Quantum Hybrid Classification, Web API Integration, and Diagnostic Persistence."
    )
    p.paragraph_format.space_after = Pt(8)

    # Workflow Steps Table
    wf_table = doc.add_table(rows=1, cols=3)
    wf_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    wf_hdr = wf_table.rows[0].cells
    wf_titles = ["Phase", "Workflow Subsystem", "Technical Description & Logic"]
    wf_widths = [Inches(1.2), Inches(2.2), Inches(3.7)]
    for i, title in enumerate(wf_titles):
        wf_hdr[i].width = wf_widths[i]
        set_cell_background(wf_hdr[i], "2E7D32")
        set_cell_margins(wf_hdr[i], 100, 100, 100, 100)
        p = wf_hdr[i].paragraphs[0]
        run = p.add_run(title)
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        run.font.size = Pt(10)

    wf_steps = [
        ("Phase 1", "Data Preprocessing & Condition Mapping", "Reads folder structure (PlantName___Condition). Extracts the condition string after '___' to map 38 crop-specific classes into 21 generalized disease conditions. Applies transforms (224x224 resize, flips, rotations, ImageNet normalization)."),
        ("Phase 2", "OOD Gatekeeper Subsystem", "Extracts 512-dim embedding from input image using pretrained ResNet18. Computes Cosine Similarity against an averaged reference leaf template. Rejects non-leaf uploads (e.g., animals, faces, furniture) with error code."),
        ("Phase 3A", "Classical Model Inference (ResNet18)", "Standard transfer learning backbone. Passes normalized tensor through 18 convolutional layers, global average pooling, and a fully connected layer (512 -> 21) to generate logits and softmax confidence scores."),
        ("Phase 3B", "Quantum-Classical Hybrid (HybridNet)", "Features extracted by ResNet18 (512-dim) are compressed to 4 values via linear layer + tanh, scaled to [0, pi], and fed into a 4-qubit Quantum Neural Network (QNN) using PennyLane with RY rotations and CNOT entanglement."),
        ("Phase 4", "REST API & Advisory Engine", "FastAPI / Gradio endpoint receives image, runs inference, looks up disease details in disease_info.json (symptoms, chemical treatments, organic remedies), and constructs JSON response."),
        ("Phase 5", "History Logging & UI Display", "Logs diagnostic record (timestamp, class, confidence, processing time) to diagnostics_history.json and renders interactive UI report with top predictions and cure recommendations.")
    ]

    for idx, step in enumerate(wf_steps):
        row = wf_table.add_row()
        bg = "F4FBF7" if idx % 2 == 0 else "FFFFFF"
        for c_idx, text in enumerate(step):
            cell = row.cells[c_idx]
            cell.width = wf_widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 80, 80, 100, 100)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(text)
            run.font.size = Pt(9.5)
            if c_idx < 2:
                run.bold = True

    set_table_borders(wf_table, color="D1D5DB")
    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    add_styled_heading(doc, "2.2 Innovative Architectural Components", level=2)
    
    p = doc.add_paragraph()
    p.add_run("1. Cross-Breed Disease Decoupling:\n").bold = True
    p.add_run("Standard plant disease datasets tie symptoms to specific crops (e.g., 'Tomato___Early_blight' vs 'Potato___Early_blight'). Our CustomConditionDataset strips crop prefixes, reducing target classes from 38 to 21 pure pathological conditions. This enables cross-crop transferability.\n\n")
    p.add_run("2. Out-of-Distribution (OOD) Gatekeeper:\n").bold = True
    p.add_run("Prevents false high-confidence predictions on non-leaf images. Pretrained ResNet18 extracts feature embeddings; cosine similarity with reference leaf vectors determines whether an image is a valid leaf before invoking disease models.\n\n")
    p.add_run("3. Variational Quantum Circuit (VQC) Layer:\n").bold = True
    p.add_run("Utilizes PennyLane TorchLayer interface. Feature vector is projected to 4 dimensions, angle-encoded into 4 qubits using RY rotations, entangled with CNOT gates, and measured via Pauli-Z expectation values to produce non-linear quantum embeddings.")
    p.paragraph_format.space_after = Pt(12)

    # -------------------------------------------------------------
    # SECTION 3: VIVA VOCE QUESTIONS & ANSWERS (50 QUESTIONS)
    # -------------------------------------------------------------
    add_styled_heading(doc, "3. Viva Voce Examination Questions & Answers", level=1)
    
    p_intro = doc.add_paragraph(
        "This section covers 50 comprehensive viva examination questions categorized into Machine Learning Core, Quantum ML, Project Architecture, and Defensive Cross-Examination Questions."
    )
    p_intro.paragraph_format.space_after = Pt(12)

    # ------------------ CATEGORY A ------------------
    add_styled_heading(doc, "Category A: Machine Learning & Deep Learning Core (Q1 - Q12)", level=2)

    qa_cat_a = [
        ("Q1: What is Transfer Learning and why did you choose ResNet-18 for this project?",
         "Answer: Transfer learning is a machine learning technique where a model pretrained on a large dataset (e.g., ImageNet with 1.2M images) is fine-tuned on a specific target domain (e.g., plant disease leaves). ResNet-18 was selected because its residual skip-connections prevent gradient degradation, it has lightweight computational overhead (approx. 11.7 million parameters), and it extracts robust low-level features (edges, textures, lesions) effectively even with limited training data."),

        ("Q2: What is the Vanishing Gradient Problem and how do Residual Connections solve it?",
         "Answer: In deep neural networks, during backpropagation, gradients are multiplied by weight matrices across layers. If weights/derivatives are small (< 1), gradients diminish exponentially toward early layers, preventing parameter updates. ResNet introduces skip connections (y = F(x) + x), allowing gradients to flow directly through identity shortcuts without attenuation (dy/dx = dF/dx + 1), enabling stable training of deeper networks."),

        ("Q3: Explain the role of Data Augmentation in your training pipeline.",
         "Answer: Data Augmentation expands training set variability without collecting new data, preventing overfitting. In our train_condition_model.py, we applied RandomHorizontalFlip, RandomVerticalFlip, RandomRotation(15°), and ColorJitter (brightness, contrast, saturation). This forces the model to learn invariant representations of leaf lesions regardless of orientation, lighting conditions, or angle."),

        ("Q4: Why normalize input images using ImageNet mean [0.485, 0.456, 0.406] and std [0.229, 0.224, 0.225]?",
         "Answer: Pretrained networks like ResNet-18 were trained on ImageNet images normalized to these exact statistics. Matching input image distribution ensures features inside convolutional layers maintain zero mean and unit variance, preventing internal covariate shift and ensuring rapid numerical convergence."),

        ("Q5: What is Cross-Entropy Loss and why is it preferred over Mean Squared Error (MSE) for multi-class classification?",
         "Answer: Cross-Entropy Loss measures the dissimilarity between predicted probability distribution (p) and true one-hot distribution (y): L = - sum(y_i * log(p_i)). Unlike MSE, which suffers from vanishing gradients when combined with Sigmoid/Softmax due to flat plateau regions, Cross-Entropy produces steep log-penalties for wrong predictions, driving faster parameter optimization."),

        ("Q6: Explain the difference between Epoch, Batch Size, and Iteration.",
         "Answer:\n- Epoch: One complete pass of the entire dataset through the neural network during training.\n- Batch Size: The number of sample images processed in a single forward/backward pass (e.g., batch_size = 32).\n- Iteration: The total number of batch passes required to complete one epoch (Iterations = Total Samples / Batch Size)."),

        ("Q7: What are Precision, Recall, F1-Score, and Confusion Matrix?",
         "Answer:\n- Precision = TP / (TP + FP): Proportion of correctly identified disease cases out of all positive predictions.\n- Recall (Sensitivity) = TP / (TP + FN): Proportion of actual disease leaves correctly identified by the system.\n- F1-Score = 2 * (Precision * Recall) / (Precision + Recall): Harmonic mean balancing precision and recall.\n- Confusion Matrix: N x N table visualizing actual vs predicted classes, highlighting common misclassifications."),

        ("Q8: How did you prevent Overfitting in your model?",
         "Answer: Overfitting was mitigated through multiple techniques: (1) Data Augmentations (rotation, flip, jitter), (2) Data Splitting (80% train, 20% validation), (3) Pretrained Transfer Learning weights, (4) Early stopping monitoring validation accuracy, and (5) Normalization transforms."),

        ("Q9: Why did you choose PyTorch over TensorFlow/Keras?",
         "Answer: PyTorch offers dynamic computational graphs (eager execution), native integration with Python debugging tools, clean OOP modularity via nn.Module, and seamless interoperability with Quantum ML frameworks like PennyLane via TorchLayer."),

        ("Q10: What is the Softmax function and where is it applied?",
         "Answer: Softmax converts raw unnormalized output logits z_i into normalized probability distributions: Softmax(z_i) = exp(z_i) / sum(exp(z_j)). It is applied at the final output layer so predicted class confidence scores sum up to 1.0 (100%)."),

        ("Q11: How does Learning Rate affect neural network training?",
         "Answer: Learning rate (eta) controls the step size taken during gradient descent updates (W = W - eta * grad). If too high, optimization diverges or oscillates around minima. If too low, training is extremely slow and risks getting trapped in suboptimal local minima or saddle points."),

        ("Q12: Describe the role of Convolutional, Pooling, and Fully Connected layers.",
         "Answer:\n- Convolutional Layer: Applies filter kernels to extract localized spatial features (edges, textures, spot patterns).\n- Pooling Layer (e.g. Max/Avg Pooling): Downsamples spatial dimensions to reduce computation and grant translation invariance.\n- Fully Connected (FC) Layer: Maps high-level feature representations to final class logit outputs.")
    ]

    for q, a in qa_cat_a:
        add_styled_heading(doc, q, level=3)
        p = doc.add_paragraph(a)
        p.paragraph_format.space_after = Pt(8)

    # ------------------ CATEGORY B ------------------
    add_styled_heading(doc, "Category B: Quantum Machine Learning & PennyLane (Q13 - Q22)", level=2)

    qa_cat_b = [
        ("Q13: What is Quantum Machine Learning (QML) and why explore it in this project?",
         "Answer: QML combines quantum computing algorithms with machine learning primitives. In plant disease detection, high-dimensional visual feature spaces can be mapped into quantum Hilbert spaces via entanglement. Exploring QML evaluates whether quantum kernel spaces can improve pattern recognition or reduce feature dimensionality for agricultural AI."),

        ("Q14: What is a Qubit and how does it differ from a Classical Bit?",
         "Answer: A classical bit exists strictly in state 0 or 1. A Quantum Bit (Qubit) exists as a linear superposition state |psi> = alpha|0> + beta|1>, where |alpha|^2 + |beta|^2 = 1. Qubits also exhibit Quantum Entanglement, allowing multi-qubit systems to represent 2^N state vector amplitudes simultaneously."),

        ("Q15: How does PennyLane integrate with PyTorch?",
         "Answer: PennyLane provides a TorchLayer class that wraps a PennyLane QNode (quantum node) into a standard torch.nn.Module. PyTorch passes classical feature tensors to the QNode, which executes the quantum circuit (via autograd backpropagation using parameter-shift rules) and returns expectation values as standard PyTorch tensors."),

        ("Q16: Describe the architecture of your Variational Quantum Circuit (VQC) in hybrid_model.py.",
         "Answer: The circuit uses 4 qubits (n_qubits = 4):\n1. State Preparation: Feature input x (4 values) encoded via qml.RY(x[i], wires=i).\n2. Trainable Parameter Layer: Parameterized rotation gates qml.RY(weights[i], wires=i).\n3. Entanglement Layer: Circular CNOT gates between adjacent wires [i, i+1] to entangle qubits.\n4. Measurement: Expectation values measured in Pauli-Z basis: return [qml.expval(qml.PauliZ(i)) for i in range(4)]."),

        ("Q17: What are qml.RY and qml.CNOT gates?",
         "Answer:\n- qml.RY(theta): A single-qubit rotation gate around the Y-axis of the Bloch sphere by angle theta. Used for angle encoding and parameterized state rotation.\n- qml.CNOT: Controlled-NOT two-qubit gate that flips the target qubit if the control qubit is |1>, generating quantum entanglement between wires."),

        ("Q18: What is Pauli-Z Expectation Value Measurement?",
         "Answer: Pauli-Z expectation value <Z_i> measures the average value of state projection along the Z-axis of the Bloch sphere for qubit i. Output values range continuously between -1.0 (state |1>) and +1.0 (state |0>), converting quantum states back to classical continuous values for classification."),

        ("Q19: Why compress 512 ResNet features to 4 qubits before feeding into the quantum circuit?",
         "Answer: Current quantum simulators (and NISQ hardware) scale exponentially in computational complexity with qubit count. Reducing 512 dimensions to 4 using a linear bottleneck layer (with tanh activation scaled to [0, pi]) allows efficient quantum simulation on CPU without memory overflow."),

        ("Q20: What is the difference between default.qubit simulator and actual Quantum Hardware?",
         "Answer: default.qubit is a state-vector quantum simulator running on classical CPU hardware, simulating matrix multiplications of quantum state vectors without hardware noise. Actual quantum processors (NISQ hardware) run on physical superconducting/trapped-ion qubits subject to thermal noise, decoherence, and gate errors."),

        ("Q21: What is the Barren Plateau Problem in Quantum Neural Networks?",
         "Answer: Barren plateaus refer to regions in quantum circuit parameter space where gradient magnitudes vanish exponentially with the number of qubits: Var[dE/dTheta] -> 0. Avoided in our model by keeping circuit depth small (1 layer) and qubit count low (4 qubits)."),

        ("Q22: What advantage could Quantum ML offer in future agricultural applications?",
         "Answer: Quantum circuits possess expressive Hilbert feature space representations capable of identifying complex non-linear correlations in multi-spectral agricultural data (e.g. hyperspectral satellite images, multi-disease co-infections) with fewer trainable parameters than purely classical deep networks.")
    ]

    for q, a in qa_cat_b:
        add_styled_heading(doc, q, level=3)
        p = doc.add_paragraph(a)
        p.paragraph_format.space_after = Pt(8)

    # ------------------ CATEGORY C ------------------
    add_styled_heading(doc, "Category C: Project Implementation & System Details (Q23 - Q37)", level=2)

    qa_cat_c = [
        ("Q23: Why did you decouple plant species from disease conditions?",
         "Answer: Standard datasets contain combined labels like 'Corn___Common_rust' and 'Apple___Apple_scab'. By extracting only the condition string ('Common_rust', 'Apple_scab'), we trained a 21-condition model that focuses exclusively on visual pathogen features (rust pustules, leaf spots, mildew patches) rather than plant leaf geometry, improving cross-breed leaf disease generalization."),

        ("Q24: How does the Out-of-Distribution (OOD) Gatekeeper work in app.py?",
         "Answer: The gatekeeper extracts a 512-dimensional feature embedding from input images using a pretrained ResNet-18 backbone (excluding final FC). It computes Cosine Similarity against an averaged reference leaf vector generated from real validation leaves. If similarity is below a set threshold, it flags the image as a non-leaf upload."),

        ("Q25: What happens if a non-leaf image (e.g. human face, car) is uploaded?",
         "Answer: The Gatekeeper intercepts the image prior to disease model prediction. It returns an HTTP error response / UI warning: '⚠️ Image validation failed: Uploaded image does not appear to be a plant leaf', preventing meaningless disease classification."),

        ("Q26: Describe the role of disease_info.json in your application.",
         "Answer: disease_info.json acts as an agricultural knowledge base mapping each condition class to structured JSON information: disease description, visible symptoms, recommended chemical treatments, organic remedies, and prevention measures displayed on the web interface."),

        ("Q27: How is dataset splitting performed in split_dataset.py?",
         "Answer: split_dataset.py scans an ImageFolder directory tree, iterates through class folders, shuffles image paths, and moves 20% of images per class into data/val and 80% into data/train, preserving class distribution balance."),

        ("Q28: How does FastAPI handle async image upload and model evaluation?",
         "Answer: FastAPI uses Python async/await syntax with UploadFile. Uploaded file bytes are converted to PIL Images via BytesIO, transformed to PyTorch tensors, and passed to the condition classifier within a non-blocking request handler."),

        ("Q29: What is the difference between app.py and app_gradio.py?",
         "Answer: app.py provides a full RESTful web service API (FastAPI) serving raw JSON endpoints and static dashboard files. app_gradio.py provides a standalone interactive GUI with visual sliders, instant image preview, and user-friendly advisory cards for rapid demonstration."),

        ("Q30: How is model inference time calculated?",
         "Answer: Time is recorded around the PyTorch model evaluation block using time.perf_counter(): start = time.perf_counter(), outputs = model(inputs), elapsed_ms = (time.perf_counter() - start) * 1000. Average CPU inference latency is ~25-45 ms per image."),

        ("Q31: What hardware/software environment was used for training?",
         "Answer: Model was trained using PyTorch 2.x, Python 3.10+, torchvision, and CUDA acceleration (or CPU state vector simulation for PennyLane) with Adam optimizer, batch size 32, image resolution 224x224."),

        ("Q32: How did you evaluate final accuracy and loss curves?",
         "Answer: Validation loss and classification accuracy were logged at each epoch. Confusion matrices and classification reports (precision, recall, f1-score per class) were generated using scikit-learn and saved as visual plots (confusion_matrix1.png)."),

        ("Q33: How is diagnostic history stored?",
         "Answer: Every valid prediction appends a record to diagnostics_history.json containing: timestamp, filename, predicted condition, confidence percentage, execution time, and top-3 fallback conditions."),

        ("Q34: How does the system handle corrupted or invalid image files?",
         "Answer: The PIL.Image.open block is wrapped in try-except blocks. If PIL fails to decode the image byte stream, FastAPI raises HTTP 400 Bad Request: 'Invalid image format or corrupt file'."),

        ("Q35: Walk through the complete step-by-step inference pipeline for an uploaded image.",
         "Answer:\n1. User uploads image file via Web UI / REST API.\n2. PIL loads image and converts color mode to RGB.\n3. Image is resized to 224x224 and normalized via torchvision transforms.\n4. Gatekeeper computes cosine similarity against reference leaf template.\n5. If leaf valid, tensor passes through ResNet-18 FC layer (or HybridNet QNN).\n6. Softmax computes probability array across 21 conditions.\n7. Top condition and confidence score retrieved; disease_info.json fetched.\n8. Diagnostic history appended; JSON response / HTML UI rendered."),

        ("Q36: Why choose 224x224 input resolution?",
         "Answer: 224x224 is the standard native input dimension for ResNet spatial feature maps. It balances fine lesion detail retention with memory consumption and GPU speed."),

        ("Q37: What hyperparameter settings were used during condition model training?",
         "Answer: Learning rate = 0.001 (with Adam optimizer), Batch Size = 32, Image Size = 224x224, Train/Val split ratio = 80/20, Epochs = 3 to 6.")
    ]

    for q, a in qa_cat_c:
        add_styled_heading(doc, q, level=3)
        p = doc.add_paragraph(a)
        p.paragraph_format.space_after = Pt(8)

    # ------------------ CATEGORY D ------------------
    add_styled_heading(doc, "Category D: Defensive & Tricky Viva Questions (Q38 - Q50)", level=2)

    qa_cat_d = [
        ("Q38: 'If classical ResNet gives 95%+ accuracy, why add a Quantum layer?' How do you answer this?",
         "Answer: Classical ResNet is our operational baseline. The quantum hybrid layer (HybridNet) is a research investigation exploring how quantum entanglement and Hilbert space projections behave on computer vision embeddings. While classical hardware currently simulates quantum gates, evaluating QML establishes a framework for future hardware acceleration when fault-tolerant Quantum Processing Units (QPUs) become commercially available."),

        ("Q39: 'Why not use MobileNetV3 or EfficientNet for mobile deployment?'",
         "Answer: ResNet-18 was selected for its balanced architecture, proven stability, and clean PyTorch feature extraction interface. EfficientNet/MobileNet are excellent targets for future edge deployment; converting our trained PyTorch model to ONNX or TensorFlow Lite will allow seamless integration into mobile apps."),

        ("Q40: 'Is 21 condition classes sufficient for real-world farming?'",
         "Answer: 21 condition classes cover the most prevalent economic crop pathogens (blights, rusts, mildews, spot viruses, spider mites). Furthermore, by decoupling plant species, these 21 conditions apply across dozens of crop varieties rather than being restricted to a single plant."),

        ("Q41: 'How does your model perform under bad lighting or messy soil backgrounds?'",
         "Answer: Training included extensive color jittering, random rotations, and horizontal/vertical flips to simulate varied field lighting. For messy soil backgrounds, the OOD Gatekeeper ensures leaf presence, while convolutional feature maps learn texture specific to leaf pathology rather than background pixels."),

        ("Q42: 'What is the computational complexity difference between classical convolution and quantum circuit simulation?'",
         "Answer: Classical 2D convolution scales as O(K^2 * C_in * C_out * H * W). Quantum simulation of N qubits on classical hardware scales exponentially as O(2^N) per gate operation. Hence, state-vector simulation is kept to 4 qubits to remain computationally efficient."),

        ("Q43: 'Why use Cosine Similarity instead of training a separate Binary Classifier for the Gatekeeper?'",
         "Answer: Cosine similarity in a pretrained embedding space requires zero extra training data for 'non-leaf' classes (which are infinite in real life). Measuring distance from valid leaf feature centroids provides an unsupervised, robust boundary without overfitting to specific non-leaf examples."),

        ("Q44: 'How does backpropagation compute gradients through a Quantum Node?'",
         "Answer: PennyLane uses the Parameter-Shift Rule: df/dTheta = [f(Theta + s) - f(Theta - s)] / (2 * sin(s)). It evaluates the quantum circuit at shifted parameter values to compute exact analytic gradients compatible with PyTorch's autograd engine."),

        ("Q45: 'What security considerations exist for diagnostic history storage?'",
         "Answer: Diagnostic logs currently write to server JSON files. In production, logs should be sanitized, anonymized (stripping IP addresses), and stored in an encrypted database (e.g. PostgreSQL with TLS/SSL) to comply with data privacy standards."),

        ("Q46: 'Can this project run offline on a farmer's smartphone?'",
         "Answer: Yes. By exporting the classical PyTorch weights (.pth) to ONNX / TorchScript format, inference can run locally on iOS/Android or edge devices (e.g., Raspberry Pi, Jetson Nano) without internet connectivity."),

        ("Q47: 'What was the single biggest technical challenge you faced during development?'",
         "Answer: Balancing feature dimensionality for the quantum hybrid model. Extracting 512 high-dimensional visual features from ResNet and bottlenecking them down to 4 quantum phase angles without losing discriminative disease information required careful normalization and activation scaling."),

        ("Q48: 'What is the main difference between Supervised Learning and Quantum Machine Learning in this project?'",
         "Answer: Supervised learning refers to the training paradigm (learning mapping from input images to labeled disease targets via cross-entropy loss). Quantum ML refers to the hypothesis space representation (using quantum Hilbert space states instead of purely matrix multiplications in hidden layers)."),

        ("Q49: 'How would you scale this application for production deployment?'",
         "Answer: Containerize FastAPI backend using Docker, deploy behind an NGINX load balancer on AWS/GCP, use Redis for caching frequent image query embeddings, and persist diagnostic history in a relational PostgreSQL database."),

        ("Q50: 'What is your specific individual contribution to this final year project?'",
         "Answer: Designed and implemented the complete architecture: (1) Formulated condition-based dataset mapping, (2) Built the OOD ResNet-18 Gatekeeper, (3) Implemented PennyLane Quantum Hybrid circuit, (4) Developed FastAPI REST backend and Gradio web interface, and (5) Executed full model evaluation and documentation.")
    ]

    for q, a in qa_cat_d:
        add_styled_heading(doc, q, level=3)
        p = doc.add_paragraph(a)
        p.paragraph_format.space_after = Pt(8)

    # -------------------------------------------------------------
    # SECTION 4: FUTURE ENHANCEMENTS & CONCLUSION
    # -------------------------------------------------------------
    add_styled_heading(doc, "4. Future Enhancements & Conclusion", level=1)

    create_callout_box(
        doc,
        "FUTURE SCOPE & ROADMAP",
        "1. Physical QPU Execution: Benchmark model performance on physical IBM Quantum hardware via Qiskit plugin.\n"
        "2. Edge Mobile App: Convert PyTorch weights to ONNX/TFLite for offline Android/iOS field diagnostics.\n"
        "3. Multi-Spectral Drone Integration: Process aerial crop video streams for early spot detection across large farms.\n"
        "4. Multilingual Voice Advisory: Integrate LLM/Speech APIs to deliver spoken treatment advisories in regional farming languages."
    )

    doc.save("Plant_Disease_Detection_Viva_Guide.docx")
    print("Successfully generated Plant_Disease_Detection_Viva_Guide.docx")

if __name__ == "__main__":
    build_document()
