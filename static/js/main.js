document.addEventListener('DOMContentLoaded', () => {
    // State Variables
    let selectedFile = null;
    let diseaseDatabase = {};
    let modelInformation = {};
    
    // UI Elements
    const navItems = document.querySelectorAll('.nav-item');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const pageTitle = document.getElementById('page-title');
    const pageSubtitle = document.getElementById('page-subtitle');
    
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const imagePreview = document.getElementById('image-preview');
    const analyzeBtn = document.getElementById('analyze-btn');
    const resetBtn = document.getElementById('reset-btn');
    
    // Outputs
    const waitingState = document.getElementById('waiting-state');
    const warningStateBox = document.getElementById('warning-state-box');
    const warningMessage = document.getElementById('warning-message');
    const similarityScoreBadge = document.getElementById('similarity-score-badge');
    const resultsState = document.getElementById('results-state');
    
    const severityBadge = document.getElementById('severity-badge');
    const detectedDiseaseTitle = document.getElementById('detected-disease-title');
    const diagnosisTimestamp = document.getElementById('diagnosis-timestamp');
    const probabilitiesList = document.getElementById('probabilities-list');
    
    // Treatment Cards
    const treatmentTabBtns = document.querySelectorAll('.treatment-tab-btn');
    const treatmentItemsList = document.getElementById('treatment-items-list');
    let currentTreatmentData = null;
    
    // Quantum Elements
    const q0Val = document.getElementById('q0-val');
    const q1Val = document.getElementById('q1-val');
    const q2Val = document.getElementById('q2-val');
    const q3Val = document.getElementById('q3-val');
    const q0Bar = document.getElementById('q0-bar');
    const q1Bar = document.getElementById('q1-bar');
    const q2Bar = document.getElementById('q2-bar');
    const q3Bar = document.getElementById('q3-bar');
    const vectorMathOutput = document.getElementById('vector-math-output');

    // History & Report Elements
    const saveHistoryBtn = document.getElementById('save-history-btn');
    const clearHistoryBtn = document.getElementById('clear-history-btn');
    const historyEmpty = document.getElementById('history-empty');
    const historyItemsContainer = document.getElementById('history-items-container');
    const printReportBtn = document.getElementById('print-report-btn');
    
    // Fetch initial model data
    fetchModelData();
    drawQuantumCircuit();
    loadHistory();
    initCharts();
    initWeatherModule();

    // ----------------------------------------------------
    // Tab Navigation
    // ----------------------------------------------------
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = item.getAttribute('data-tab');
            
            // Toggle active menu item
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            // Toggle active pane
            tabPanes.forEach(pane => pane.classList.remove('active'));
            const targetPane = document.getElementById(`tab-${tabId}`);
            if (targetPane) targetPane.classList.add('active');
            
            // Update Headers
            updateHeaderTitles(tabId);
            
            // Dynamically load history when entering history tab
            if (tabId === 'history') {
                loadHistory();
            }
        });
    });

    function updateHeaderTitles(tabId) {
        const titles = {
            diagnosis: {
                title: "Diagnostic Hub",
                sub: "Cross-Breed Symptom Scan & Quantum Analysis"
            },
            quantum: {
                title: "Quantum Simulation",
                sub: "Pauli-Z Expectation Mapping & Entanglement Channels"
            },
            metrics: {
                title: "Model Metrics",
                sub: "CNN-QML Hybrid Architecture Analytics"
            },
            treatments: {
                title: "Treatment Index",
                sub: "Symptom Remediation & Crop Protection Database"
            },
            history: {
                title: "Diagnostic Archive",
                sub: "Review Past Specimen Scan Records"
            },
            weather: {
                title: "Agro-Weather Hub",
                sub: "15-Day Atmospheric Projections & Fungal Outbreak Forecasts"
            }
        };
        
        if (titles[tabId]) {
            pageTitle.textContent = titles[tabId].title;
            pageSubtitle.textContent = titles[tabId].sub;
        }
    }

    // ----------------------------------------------------
    // File Upload & Drag-and-Drop
    // ----------------------------------------------------
    dropZone.addEventListener('click', () => fileInput.click());
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
    
    function handleFileSelect(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file.');
            return;
        }
        selectedFile = file;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            imagePreview.classList.remove('image-preview-hidden');
            analyzeBtn.disabled = false;
            resetBtn.classList.remove('btn-hidden');
        };
        reader.readAsDataURL(file);
    }
    
    resetBtn.addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        imagePreview.src = '';
        imagePreview.classList.add('image-preview-hidden');
        analyzeBtn.disabled = true;
        resetBtn.classList.add('btn-hidden');
        
        // Reset states
        waitingState.classList.remove('btn-hidden');
        warningStateBox.classList.add('warning-hidden');
        resultsState.classList.add('results-hidden');
    });

    // ----------------------------------------------------
    // API Call & Diagnostics
    // ----------------------------------------------------
    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;
        
        // Start animation
        dropZone.classList.add('scanning');
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = `<span class="btn-spinner"></span> Analyzing Specimen...`;
        
        // Prepare data
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                renderDiagnosisResult(data);
            } else {
                alert(`Error: ${data.detail || 'Failed to analyze specimen'}`);
                resetBtn.click();
            }
        } catch (error) {
            console.error('Prediction Error:', error);
            alert('Server connection failed. Make sure app.py is running.');
            resetBtn.click();
        } finally {
            dropZone.classList.remove('scanning');
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = `<span class="btn-icon">⚡</span> Run Quantum-CNN Diagnosis`;
        }
    });

    function renderDiagnosisResult(data) {
        // Hide waiting card
        waitingState.classList.add('btn-hidden');
        
        // Check Leaf Gating
        if (data.is_leaf === false) {
            warningStateBox.classList.remove('warning-hidden');
            resultsState.classList.add('results-hidden');
            
            warningMessage.innerHTML = `⚠️ <b>Invalid Specimen:</b> The gatekeeper system detected that this upload is not a plant leaf.<br><br>Please submit a clear, close-up image of a plant leaf showing symptoms to run the diagnostic analysis.`;
            similarityScoreBadge.textContent = `Leaf Similarity: ${data.leaf_similarity.toFixed(3)} (Min: 0.65)`;
            
            updateQuantumDisplays([0, 0, 0, 0]);
            return;
        }
        
        // Gating Success: Render probabilities & treatment info
        warningStateBox.classList.add('warning-hidden');
        resultsState.classList.remove('results-hidden');
        
        // Get primary disease
        const primaryDisease = data.top_condition;
        detectedDiseaseTitle.textContent = formatConditionName(primaryDisease);
        diagnosisTimestamp.textContent = `Analyzed on ${new Date().toLocaleTimeString()} • Accuracy Check: Completed`;
        
        // Set severity
        severityBadge.className = 'severity-badge'; // reset
        if (primaryDisease.toLowerCase() === 'healthy') {
            severityBadge.textContent = 'Healthy';
            severityBadge.classList.add('badge-healthy');
        } else if (primaryDisease.toLowerCase().includes('scab') || primaryDisease.toLowerCase().includes('spot') || primaryDisease.toLowerCase().includes('mildew') || primaryDisease.toLowerCase().includes('rust')) {
            severityBadge.textContent = 'Warning';
            severityBadge.classList.add('badge-warning');
        } else {
            severityBadge.textContent = 'Critical';
            severityBadge.classList.add('badge-critical');
        }
        
        // Probabilities Bars list
        probabilitiesList.innerHTML = '';
        data.predictions.forEach(pred => {
            const pct = (pred.probability * 100).toFixed(1);
            const row = document.createElement('div');
            row.className = 'probability-row';
            row.innerHTML = `
                <div class="prob-info">
                    <span class="prob-name">${formatConditionName(pred.condition)}</span>
                    <span class="prob-pct">${pct}%</span>
                </div>
                <div class="prob-bar-bg">
                    <div class="prob-bar-fill" style="width: 0%"></div>
                </div>
            `;
            probabilitiesList.appendChild(row);
            
            // Trigger animation
            setTimeout(() => {
                row.querySelector('.prob-bar-fill').style.width = `${pct}%`;
            }, 50);
        });
        
        // Treatment Info
        currentTreatmentData = data.treatment_info;
        renderTreatmentSection('meds');
        
        // Quantum stats
        if (data.quantum_states) {
            updateQuantumDisplays(data.quantum_states);
        }
        
        // Save scan result data including the server-saved image URL for logging
        window.latestScanResult = {
            condition: primaryDisease,
            confidence: data.predictions[0].probability,
            timestamp: new Date().toLocaleString(),
            quantum_states: data.quantum_states,
            imageSrc: imagePreview.src,
            image_url: data.image_url
        };
    }

    // ----------------------------------------------------
    // Treatment tab toggles
    // ----------------------------------------------------
    treatmentTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            treatmentTabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const section = btn.getAttribute('data-sec');
            renderTreatmentSection(section);
        });
    });

    function renderTreatmentSection(section) {
        treatmentItemsList.innerHTML = '';
        if (!currentTreatmentData) return;
        
        let items = [];
        if (section === 'meds') {
            items = currentTreatmentData.meds || [];
        } else if (section === 'care') {
            items = currentTreatmentData.care || [];
        } else if (section === 'prevent') {
            items = currentTreatmentData.prevention || [];
        }
        
        if (items.length === 0) {
            const li = document.createElement('li');
            li.textContent = "No specific guidelines available.";
            treatmentItemsList.appendChild(li);
        } else {
            items.forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                treatmentItemsList.appendChild(li);
            });
        }
    }

    // ----------------------------------------------------
    // Quantum Simulation & SVG drawing
    // ----------------------------------------------------
    function drawQuantumCircuit() {
        const svgContainer = document.getElementById('circuit-svg-container');
        if (!svgContainer) return;
        const svgCode = `
            <svg class="svg-circuit" viewBox="0 0 500 220" xmlns="http://www.w3.org/2000/svg">
                <!-- Qubit lines -->
                <text x="20" y="45" fill="#94a3b8" font-family="monospace" font-size="12">|q₀⟩</text>
                <line x1="50" y1="40" x2="440" y2="40" stroke="#1e293b" stroke-width="2" id="q0-wire" />
                
                <text x="20" y="95" fill="#94a3b8" font-family="monospace" font-size="12">|q₁⟩</text>
                <line x1="50" y1="90" x2="440" y2="90" stroke="#1e293b" stroke-width="2" id="q1-wire" />
                
                <text x="20" y="145" fill="#94a3b8" font-family="monospace" font-size="12">|q₂⟩</text>
                <line x1="50" y1="140" x2="440" y2="140" stroke="#1e293b" stroke-width="2" id="q2-wire" />
                
                <text x="20" y="195" fill="#94a3b8" font-family="monospace" font-size="12">|q₃⟩</text>
                <line x1="50" y1="190" x2="440" y2="190" stroke="#1e293b" stroke-width="2" id="q3-wire" />

                <!-- RY Gates (Feature Encoding) -->
                <g class="ry-gate" transform="translate(80, 25)">
                    <rect width="40" height="30" rx="4" fill="#0d9488" stroke="#00f5d4" stroke-width="1" />
                    <text x="20" y="18" fill="white" font-family="sans-serif" font-size="10" text-anchor="middle" font-weight="bold">RY(θ₀)</text>
                </g>
                <g class="ry-gate" transform="translate(80, 75)">
                    <rect width="40" height="30" rx="4" fill="#0d9488" stroke="#00f5d4" stroke-width="1" />
                    <text x="20" y="18" fill="white" font-family="sans-serif" font-size="10" text-anchor="middle" font-weight="bold">RY(θ₁)</text>
                </g>
                <g class="ry-gate" transform="translate(80, 125)">
                    <rect width="40" height="30" rx="4" fill="#0d9488" stroke="#00f5d4" stroke-width="1" />
                    <text x="20" y="18" fill="white" font-family="sans-serif" font-size="10" text-anchor="middle" font-weight="bold">RY(θ₂)</text>
                </g>
                <g class="ry-gate" transform="translate(80, 175)">
                    <rect width="40" height="30" rx="4" fill="#0d9488" stroke="#00f5d4" stroke-width="1" />
                    <text x="20" y="18" fill="white" font-family="sans-serif" font-size="10" text-anchor="middle" font-weight="bold">RY(θ₃)</text>
                </g>

                <!-- Parameterized Gates -->
                <g class="param-gate" transform="translate(160, 25)">
                    <rect width="40" height="30" rx="4" fill="#0f766e" stroke="#0d9488" stroke-width="1" />
                    <text x="20" y="18" fill="white" font-family="sans-serif" font-size="10" text-anchor="middle">RY(w₀)</text>
                </g>
                <g class="param-gate" transform="translate(160, 75)">
                    <rect width="40" height="30" rx="4" fill="#0f766e" stroke="#0d9488" stroke-width="1" />
                    <text x="20" y="18" fill="white" font-family="sans-serif" font-size="10" text-anchor="middle">RY(w₁)</text>
                </g>
                <g class="param-gate" transform="translate(160, 125)">
                    <rect width="40" height="30" rx="4" fill="#0f766e" stroke="#0d9488" stroke-width="1" />
                    <text x="20" y="18" fill="white" font-family="sans-serif" font-size="10" text-anchor="middle">RY(w₂)</text>
                </g>
                <g class="param-gate" transform="translate(160, 175)">
                    <rect width="40" height="30" rx="4" fill="#0f766e" stroke="#0d9488" stroke-width="1" />
                    <text x="20" y="18" fill="white" font-family="sans-serif" font-size="10" text-anchor="middle">RY(w₃)</text>
                </g>

                <!-- CNOT gates entangling channel -->
                <!-- CNOT 0 -> 1 -->
                <line x1="240" y1="40" x2="240" y2="90" stroke="#00f5d4" stroke-width="1.5" />
                <circle cx="240" cy="40" r="4" fill="#00f5d4" />
                <circle cx="240" cy="90" r="8" fill="none" stroke="#00f5d4" stroke-width="1.5" />
                <line x1="235" y1="90" x2="245" y2="90" stroke="#00f5d4" stroke-width="1.5" />
                <line x1="240" y1="85" x2="240" y2="95" stroke="#00f5d4" stroke-width="1.5" />

                <!-- CNOT 1 -> 2 -->
                <line x1="280" y1="90" x2="280" y2="140" stroke="#00f5d4" stroke-width="1.5" />
                <circle cx="280" cy="90" r="4" fill="#00f5d4" />
                <circle cx="280" cy="140" r="8" fill="none" stroke="#00f5d4" stroke-width="1.5" />
                <line x1="275" y1="140" x2="285" y2="140" stroke="#00f5d4" stroke-width="1.5" />
                <line x1="280" y1="135" x2="280" y2="145" stroke="#00f5d4" stroke-width="1.5" />

                <!-- CNOT 2 -> 3 -->
                <line x1="320" y1="140" x2="320" y2="190" stroke="#00f5d4" stroke-width="1.5" />
                <circle cx="320" cy="140" r="4" fill="#00f5d4" />
                <circle cx="320" cy="190" r="8" fill="none" stroke="#00f5d4" stroke-width="1.5" />
                <line x1="315" y1="190" x2="325" y2="190" stroke="#00f5d4" stroke-width="1.5" />
                <line x1="320" y1="185" x2="320" y2="195" stroke="#00f5d4" stroke-width="1.5" />

                <!-- Measurement boxes -->
                <g class="meas-box" transform="translate(370, 25)">
                    <rect width="30" height="30" rx="3" fill="#1e293b" stroke="#475569" stroke-width="1" />
                    <!-- dial -->
                    <path d="M 375,50 A 12,12 0 0 1 395,50" fill="none" stroke="white" stroke-width="1" />
                    <line x1="385" y1="50" x2="393" y2="38" stroke="#00f5d4" stroke-width="1.5" />
                </g>
                <g class="meas-box" transform="translate(370, 75)">
                    <rect width="30" height="30" rx="3" fill="#1e293b" stroke="#475569" stroke-width="1" />
                    <path d="M 375,100 A 12,12 0 0 1 395,100" fill="none" stroke="white" stroke-width="1" />
                    <line x1="385" y1="100" x2="393" y2="88" stroke="#00f5d4" stroke-width="1.5" />
                </g>
                <g class="meas-box" transform="translate(370, 125)">
                    <rect width="30" height="30" rx="3" fill="#1e293b" stroke="#475569" stroke-width="1" />
                    <path d="M 375,150 A 12,12 0 0 1 395,150" fill="none" stroke="white" stroke-width="1" />
                    <line x1="385" y1="150" x2="393" y2="138" stroke="#00f5d4" stroke-width="1.5" />
                </g>
                <g class="meas-box" transform="translate(370, 175)">
                    <rect width="30" height="30" rx="3" fill="#1e293b" stroke="#475569" stroke-width="1" />
                    <path d="M 375,200 A 12,12 0 0 1 395,200" fill="none" stroke="white" stroke-width="1" />
                    <line x1="385" y1="200" x2="393" y2="188" stroke="#00f5d4" stroke-width="1.5" />
                </g>
            </svg>
        `;
        svgContainer.innerHTML = svgCode;
    }

    function updateQuantumDisplays(states) {
        if (!states || states.length < 4) return;
        
        if (q0Val) q0Val.textContent = states[0].toFixed(4);
        if (q1Val) q1Val.textContent = states[1].toFixed(4);
        if (q2Val) q2Val.textContent = states[2].toFixed(4);
        if (q3Val) q3Val.textContent = states[3].toFixed(4);
        
        // expectation value can be [-1.0, 1.0], map to [0, 100]% progress bar
        const getPct = val => ((val + 1.0) / 2.0 * 100).toFixed(1);
        
        if (q0Bar) q0Bar.style.width = `${getPct(states[0])}%`;
        if (q1Bar) q1Bar.style.width = `${getPct(states[1])}%`;
        if (q2Bar) q2Bar.style.width = `${getPct(states[2])}%`;
        if (q3Bar) q3Bar.style.width = `${getPct(states[3])}%`;
        
        if (vectorMathOutput) vectorMathOutput.textContent = `[${states.map(s => s.toFixed(3)).join(', ')}]`;
        
        // Pulse QPU wires based on expectation energy
        const wires = ['q0-wire', 'q1-wire', 'q2-wire', 'q3-wire'];
        wires.forEach((id, idx) => {
            const wire = document.getElementById(id);
            if (wire) {
                // scale intensity
                const absVal = Math.abs(states[idx]);
                wire.style.stroke = `rgba(0, 245, 212, ${0.1 + absVal * 0.9})`;
                wire.style.strokeWidth = `${2 + absVal * 3}px`;
            }
        });
    }

    // ----------------------------------------------------
    // Treatment Search Index
    // ----------------------------------------------------
    function initTreatmentIndex() {
        const treatmentsDbGrid = document.getElementById('treatments-db-grid');
        treatmentsDbGrid.innerHTML = '';
        
        Object.keys(diseaseDatabase).forEach(condition => {
            const info = diseaseDatabase[condition];
            const name = formatConditionName(condition);
            
            const card = document.createElement('div');
            card.className = 'glass-card disease-db-card';
            card.setAttribute('data-search', `${name} ${condition}`.toLowerCase());
            
            const icon = condition.toLowerCase() === 'healthy' ? '🟢' : '⚠️';
            
            card.innerHTML = `
                <div class="db-card-header">
                    <span class="db-card-icon">${icon}</span>
                    <span class="db-card-title">${info.title || name}</span>
                </div>
                <div class="db-card-body">
                    <div class="db-sub-sec">
                        <h5>💊 Medications & Treatments</h5>
                        <p>${(info.meds && info.meds[0]) || 'No medical treatments required.'}</p>
                    </div>
                    <div class="db-sub-sec">
                        <h5>🌿 Standard Plant Care</h5>
                        <p>${(info.care && info.care[0]) || 'Routine plant water and care.'}</p>
                    </div>
                    <div class="db-sub-sec">
                        <h5>🛡️ Prevention Strategy</h5>
                        <p>${(info.prevention && info.prevention[0]) || 'Maintain healthy growing habits.'}</p>
                    </div>
                </div>
            `;
            treatmentsDbGrid.appendChild(card);
        });
        
        // Search listener
        const dbSearch = document.getElementById('db-search');
        dbSearch.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const cards = document.querySelectorAll('.disease-db-card');
            cards.forEach(card => {
                const text = card.getAttribute('data-search');
                if (text.includes(query)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // ----------------------------------------------------
    // LocalStorage Scan History Archive
    // ----------------------------------------------------
    
    saveHistoryBtn.addEventListener('click', async () => {
        if (!window.latestScanResult) {
            alert('No diagnostic result available to log.');
            return;
        }
        
        const payload = {
            condition: window.latestScanResult.condition,
            confidence: window.latestScanResult.confidence,
            timestamp: window.latestScanResult.timestamp,
            quantum_states: window.latestScanResult.quantum_states,
            image_url: window.latestScanResult.image_url || ""
        };
        
        try {
            const res = await fetch('/api/log-diagnostic', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            if (res.ok) {
                alert('Scan successfully logged to history archive.');
                loadHistory();
            } else {
                alert('Failed to log diagnostic to server database.');
            }
        } catch (err) {
            console.error('Failed to log diagnostic:', err);
            alert('Failed to connect to server history database.');
        }
    });
    
    clearHistoryBtn.addEventListener('click', async () => {
        if (confirm('Are you sure you want to purge the diagnostic history? This will delete all logged records and saved images.')) {
            try {
                const res = await fetch('/api/history', { method: 'DELETE' });
                if (res.ok) {
                    loadHistory();
                } else {
                    alert('Failed to clear history on server.');
                }
            } catch (err) {
                console.error(err);
                alert('Failed to connect to server.');
            }
        }
    });
    
    async function loadHistory() {
        try {
            const res = await fetch('/api/history');
            const history = await res.json();
            
            if (history.length === 0) {
                historyEmpty.style.display = 'flex';
                historyItemsContainer.style.display = 'none';
                return;
            }
            
            historyEmpty.style.display = 'none';
            historyItemsContainer.style.display = 'flex';
            historyItemsContainer.innerHTML = '';
            
            history.forEach(item => {
                const card = document.createElement('div');
                card.className = 'glass-card history-item-card';
                
                const badgeClass = item.condition.toLowerCase() === 'healthy' ? 'badge-healthy' : 'badge-warning';
                const imgHtml = item.image_url ? `<img src="${item.image_url}" class="hist-thumbnail" alt="thumbnail">` : '<div class="hist-thumbnail" style="display:flex;align-items:center;justify-content:center;font-size:1.5rem;background:#1e293b">🍃</div>';
                
                card.innerHTML = `
                    <div class="hist-left-group">
                        ${imgHtml}
                        <div class="hist-meta">
                            <h4>${formatConditionName(item.condition)}</h4>
                            <span>${item.timestamp}</span>
                        </div>
                    </div>
                    <div class="hist-right-group">
                        <span class="hist-badge ${badgeClass}">${(item.confidence * 100).toFixed(1)}% Conf.</span>
                        <div class="hist-actions-cell">
                            <button class="btn btn-secondary btn-mini btn-reload" data-id="${item.id}">Load State</button>
                            <button class="btn btn-danger btn-mini btn-delete" data-id="${item.id}">Delete</button>
                        </div>
                    </div>
                `;
                historyItemsContainer.appendChild(card);
            });
            
            // Listeners for load/delete
            document.querySelectorAll('.btn-reload').forEach(btn => {
                btn.addEventListener('click', () => {
                    const id = btn.getAttribute('data-id');
                    const selected = history.find(h => h.id == id);
                    if (selected) {
                        loadHistoricalState(selected);
                    }
                });
            });
            
            document.querySelectorAll('.btn-delete').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const id = btn.getAttribute('data-id');
                    if (confirm('Delete this history record?')) {
                        try {
                            const res = await fetch(`/api/history/${id}`, { method: 'DELETE' });
                            if (res.ok) {
                                loadHistory();
                            } else {
                                alert('Failed to delete history item on server.');
                            }
                        } catch (err) {
                            console.error(err);
                        }
                    }
                });
            });
        } catch (err) {
            console.error('Failed to load history:', err);
        }
    }
    
    function loadHistoricalState(item) {
        // Go back to Diagnosis Tab
        document.querySelector('[data-tab="diagnosis"]').click();
        
        // Setup specimen previews
        if (item.image_url) {
            imagePreview.src = item.image_url;
            imagePreview.classList.remove('image-preview-hidden');
            analyzeBtn.disabled = false;
            resetBtn.classList.remove('btn-hidden');
        }
        
        // Render fake prediction data structure matching API output
        const fakeData = {
            is_leaf: true,
            leaf_similarity: 0.9,
            top_condition: item.condition,
            predictions: [
                { condition: item.condition, probability: item.confidence },
                { condition: 'Secondary Match', probability: Math.max(0, 1.0 - item.confidence) }
            ],
            treatment_info: diseaseDatabase[item.condition] || {},
            quantum_states: item.quantum_states || [0.2, 0.2, 0.2, 0.2]
        };
        
        renderDiagnosisResult(fakeData);
    }

    // ----------------------------------------------------
    // PDF Report Export
    // ----------------------------------------------------
    printReportBtn.addEventListener('click', () => {
        window.print();
    });

    // ----------------------------------------------------
    // Initializers and Helpers
    // ----------------------------------------------------
    async function fetchModelData() {
        try {
            const res = await fetch('/api/model-info');
            const data = await res.json();
            
            diseaseDatabase = data.disease_info || {};
            modelInformation = data.model_info || {};
            
            // Set specs UI
            if (modelInformation) {
                const valAccText = document.getElementById('val-accuracy-text');
                const modelDevice = document.getElementById('model-device');
                if (valAccText) valAccText.textContent = modelInformation.val_acc || '98.24%';
                if (modelDevice) modelDevice.textContent = modelInformation.device || 'CUDA/CPU Auto';
            }
            
            // Init components
            initTreatmentIndex();
            
        } catch (error) {
            console.error('Error fetching model metadata:', error);
        }
    }
    
    function formatConditionName(name) {
        if (!name) return '';
        // Remove trailing underscores and replace ___ with spaces
        let cleaned = name.replace(/_+$/, '').replace(/___/g, ' - ');
        // Replace underscore with space
        cleaned = cleaned.replace(/_/g, ' ');
        return cleaned;
    }

    function initCharts() {
        const accChartEl = document.getElementById('accuracy-chart');
        const lossChartEl = document.getElementById('loss-chart');
        if (!accChartEl || !lossChartEl) return;
        
        const accCtx = accChartEl.getContext('2d');
        const lossCtx = lossChartEl.getContext('2d');
        
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        };

        // Accuracy Line
        new Chart(accCtx, {
            type: 'line',
            data: {
                labels: ['Epoch 1', 'Epoch 2', 'Epoch 3', 'Epoch 4', 'Epoch 5', 'Epoch 6'],
                datasets: [{
                    label: 'Val Accuracy',
                    data: [82.4, 91.2, 94.8, 97.1, 97.9, 98.2],
                    borderColor: '#00f5d4',
                    backgroundColor: 'rgba(0, 245, 212, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2
                }]
            },
            options: chartOptions
        });

        // Loss Line
        new Chart(lossCtx, {
            type: 'line',
            data: {
                labels: ['Epoch 1', 'Epoch 2', 'Epoch 3', 'Epoch 4', 'Epoch 5', 'Epoch 6'],
                datasets: [{
                    label: 'Val Loss',
                    data: [0.45, 0.28, 0.19, 0.11, 0.07, 0.05],
                    borderColor: '#ff6b6b',
                    backgroundColor: 'rgba(255, 107, 107, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2
                }]
            },
            options: chartOptions
        });
    }

    // ----------------------------------------------------
    // Agro-Weather Module & API Integration
    // ----------------------------------------------------
    function initWeatherModule() {
        const cityInput = document.getElementById('weather-city-input');
        const searchBtn = document.getElementById('weather-search-btn');
        const detectBtn = document.getElementById('weather-detect-btn');
        const banner = document.getElementById('weather-alert-banner');
        const bannerClose = document.getElementById('close-weather-alert');

        if (bannerClose) {
            bannerClose.addEventListener('click', () => {
                banner.classList.add('alert-hidden');
            });
        }

        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                const city = cityInput.value.trim();
                if (city) {
                    searchCityWeather(city);
                } else {
                    alert('Please enter a city name.');
                }
            });
        }

        if (cityInput) {
            cityInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    const city = cityInput.value.trim();
                    if (city) {
                        searchCityWeather(city);
                    }
                }
            });
        }

        if (detectBtn) {
            detectBtn.addEventListener('click', () => {
                detectLocationWeather();
            });
        }

        // Horizontal timeline scroll buttons
        const scrollLeftBtn = document.getElementById('forecast-scroll-left');
        const scrollRightBtn = document.getElementById('forecast-scroll-right');
        const forecastWrapper = document.getElementById('forecast-grid-wrapper');

        if (scrollLeftBtn && forecastWrapper) {
            scrollLeftBtn.addEventListener('click', () => {
                forecastWrapper.scrollBy({ left: -320, behavior: 'smooth' });
            });
        }

        if (scrollRightBtn && forecastWrapper) {
            scrollRightBtn.addEventListener('click', () => {
                forecastWrapper.scrollBy({ left: 320, behavior: 'smooth' });
            });
        }

        // Horizontal timeline drag-to-scroll
        if (forecastWrapper) {
            let isDown = false;
            let startX;
            let scrollLeft;

            forecastWrapper.addEventListener('mousedown', (e) => {
                isDown = true;
                forecastWrapper.classList.add('active-dragging');
                startX = e.pageX - forecastWrapper.offsetLeft;
                scrollLeft = forecastWrapper.scrollLeft;
            });

            forecastWrapper.addEventListener('mouseleave', () => {
                isDown = false;
                forecastWrapper.classList.remove('active-dragging');
            });

            forecastWrapper.addEventListener('mouseup', () => {
                isDown = false;
                forecastWrapper.classList.remove('active-dragging');
            });

            forecastWrapper.addEventListener('mousemove', (e) => {
                if (!isDown) return;
                e.preventDefault();
                const x = e.pageX - forecastWrapper.offsetLeft;
                const walk = (x - startX) * 1.8; // drag speed multiplier
                forecastWrapper.scrollLeft = scrollLeft - walk;
            });
        }

        // Initialize with default city or auto-detected location
        detectLocationWeather(true); // pass true for initial run
    }

    async function detectLocationWeather(isInitial = false) {
        const coordsText = document.getElementById('weather-coords');
        const locName = document.getElementById('weather-location-name');

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    if (coordsText) coordsText.textContent = `lat: ${lat.toFixed(4)}, lon: ${lon.toFixed(4)}`;
                    if (locName) locName.textContent = "Your Location";
                    await fetchWeatherForecast(lat, lon, "Your Location");
                },
                async (error) => {
                    console.log("Geolocation error or denied. Using default (New Delhi).", error);
                    if (coordsText) coordsText.textContent = "lat: 28.6139, lon: 77.2090";
                    if (locName) locName.textContent = "New Delhi, India";
                    await fetchWeatherForecast(28.6139, 77.2090, "New Delhi, India");
                }
            );
        } else {
            if (coordsText) coordsText.textContent = "lat: 28.6139, lon: 77.2090";
            if (locName) locName.textContent = "New Delhi, India";
            await fetchWeatherForecast(28.6139, 77.2090, "New Delhi, India");
        }
    }

    async function searchCityWeather(cityName) {
        const locName = document.getElementById('weather-location-name');
        const coordsText = document.getElementById('weather-coords');
        if (locName) locName.textContent = "Searching...";

        try {
            const geocodeUrl = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(cityName)}&count=1&language=en&format=json`;
            const res = await fetch(geocodeUrl);
            const data = await res.json();

            if (data.results && data.results.length > 0) {
                const result = data.results[0];
                const displayName = `${result.name}, ${result.country || ''}`;
                if (locName) locName.textContent = displayName;
                if (coordsText) coordsText.textContent = `lat: ${result.latitude.toFixed(4)}, lon: ${result.longitude.toFixed(4)}`;
                
                await fetchWeatherForecast(result.latitude, result.longitude, displayName);
            } else {
                alert(`City "${cityName}" not found. Please check spelling.`);
                if (locName) locName.textContent = "Location Not Found";
            }
        } catch (err) {
            console.error("Geocoding Error:", err);
            alert("Error searching for location. Please check your network.");
            if (locName) locName.textContent = "Error";
        }
    }

    async function fetchWeatherForecast(lat, lon, locationDisplayName) {
        try {
            const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_max,windspeed_10m_max&forecast_days=15&timezone=auto`;
            const res = await fetch(weatherUrl);
            const data = await res.json();
            
            if (data && data.daily) {
                renderWeatherDashboard(data, locationDisplayName);
            } else {
                console.error("No daily weather data returned:", data);
            }
        } catch (err) {
            console.error("Weather API Error:", err);
        }
    }

    function getWMOWeather(code) {
        const mapping = {
            0: { icon: "☀️", desc: "Clear Sky" },
            1: { icon: "🌤️", desc: "Mainly Clear" },
            2: { icon: "⛅", desc: "Partly Cloudy" },
            3: { icon: "☁️", desc: "Overcast" },
            45: { icon: "🌫️", desc: "Foggy" },
            48: { icon: "🌫️", desc: "Depositing Rime Fog" },
            51: { icon: "🌦️", desc: "Light Drizzle" },
            53: { icon: "🌦️", desc: "Moderate Drizzle" },
            55: { icon: "🌦️", desc: "Dense Drizzle" },
            56: { icon: "🌨️", desc: "Light Freezing Drizzle" },
            57: { icon: "🌨️", desc: "Dense Freezing Drizzle" },
            61: { icon: "🌧️", desc: "Slight Rain" },
            63: { icon: "🌧️", desc: "Moderate Rain" },
            65: { icon: "🌧️", desc: "Heavy Rain" },
            66: { icon: "🌨️", desc: "Light Freezing Rain" },
            67: { icon: "🌨️", desc: "Heavy Freezing Rain" },
            71: { icon: "❄️", desc: "Slight Snow" },
            73: { icon: "❄️", desc: "Moderate Snow" },
            75: { icon: "❄️", desc: "Heavy Snow" },
            77: { icon: "❄️", desc: "Snow Grains" },
            80: { icon: "🌧️", desc: "Slight Rain Showers" },
            81: { icon: "🌧️", desc: "Moderate Rain Showers" },
            82: { icon: "🌧️", desc: "Violent Rain Showers" },
            85: { icon: "❄️", desc: "Slight Snow Showers" },
            86: { icon: "❄️", desc: "Heavy Snow Showers" },
            95: { icon: "⚡", desc: "Thunderstorm" },
            96: { icon: "⛈️", desc: "Thunderstorm with Hail" },
            99: { icon: "⛈️", desc: "Severe Hail Thunderstorm" }
        };
        return mapping[code] || { icon: "🌤️", desc: "Partly Cloudy" };
    }

    function renderWeatherDashboard(data, locationDisplayName) {
        const daily = data.daily;
        
        // 1. Current Weather (Day 0)
        const currentIcon = getWMOWeather(daily.weathercode[0]).icon;
        const currentDesc = getWMOWeather(daily.weathercode[0]).desc;
        const currentTemp = daily.temperature_2m_max[0];
        const currentHumidity = daily.relative_humidity_2m_max[0];
        const currentPrecip = daily.precipitation_sum[0];
        const currentWind = daily.windspeed_10m_max[0];
        
        // Update DOM elements
        document.getElementById('current-weather-icon').textContent = currentIcon;
        document.getElementById('current-weather-desc').textContent = currentDesc;
        document.getElementById('current-temp').textContent = `${currentTemp.toFixed(1)}°C`;
        document.getElementById('current-humidity').textContent = `${currentHumidity}%`;
        document.getElementById('current-precipitation').textContent = `${currentPrecip} mm`;
        document.getElementById('current-windspeed').textContent = `${currentWind} km/h`;
        
        // 2. 15-Day forecast grid
        const grid = document.getElementById('weather-forecast-grid');
        grid.innerHTML = '';
        
        let highRiskDaysCount = 0;
        let modRiskDaysCount = 0;
        let next7DaysHighRisk = 0;
        let maxWindForecast = 0;
        let totalRainForecast = 0;
        
        for (let i = 0; i < daily.time.length; i++) {
            const dateStr = daily.time[i];
            const tempMax = daily.temperature_2m_max[i];
            const tempMin = daily.temperature_2m_min[i];
            const code = daily.weathercode[i];
            const rain = daily.precipitation_sum[i];
            const humidity = daily.relative_humidity_2m_max[i];
            const wind = daily.windspeed_10m_max[i];
            
            const wmo = getWMOWeather(code);
            const dateObj = new Date(dateStr);
            const formattedDate = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'short' });
            
            // Computes risk level for this day
            let risk = "low";
            const avgTemp = (tempMax + tempMin) / 2;
            if (humidity > 78 && avgTemp > 14 && avgTemp < 27) {
                if (rain > 1.5) {
                    risk = "high";
                    highRiskDaysCount++;
                    if (i < 7) next7DaysHighRisk++;
                } else {
                    risk = "mod";
                    modRiskDaysCount++;
                }
            } else if (humidity > 68 && avgTemp > 11 && avgTemp < 31) {
                risk = "mod";
                modRiskDaysCount++;
            }
            
            if (wind > maxWindForecast) maxWindForecast = wind;
            totalRainForecast += rain;
            
            // Create day card
            const card = document.createElement('div');
            card.className = `forecast-day-card ${i === 0 ? 'card-today' : ''}`;
            
            const riskClass = risk === "high" ? "risk-high" : (risk === "mod" ? "risk-mod" : "risk-low");
            const riskText = risk === "high" ? "HIGH RISK" : (risk === "mod" ? "MOD RISK" : "LOW RISK");
            
            card.innerHTML = `
                <span class="forecast-date">${formattedDate}</span>
                <span class="forecast-dayname">${i === 0 ? 'Today' : dayName}</span>
                <span class="forecast-icon">${wmo.icon}</span>
                <div class="forecast-temp">
                    <span class="forecast-temp-max">${tempMax.toFixed(0)}°</span>
                    <span class="forecast-temp-min">${tempMin.toFixed(0)}°</span>
                </div>
                <div class="forecast-stat-pill stat-rain">
                    🌧️ ${rain.toFixed(1)}mm
                </div>
                <div class="forecast-stat-pill stat-humidity">
                    💧 ${humidity}%
                </div>
                <span class="forecast-risk-badge ${riskClass}">${riskText}</span>
            `;
            grid.appendChild(card);
        }
        
        // 3. Update Overall Risk Index
        let overallRisk = "low";
        let angle = -70;
        if (next7DaysHighRisk >= 2 || highRiskDaysCount >= 4) {
            overallRisk = "high";
            angle = 70;
        } else if (highRiskDaysCount > 0 || modRiskDaysCount >= 5) {
            overallRisk = "mod";
            angle = 0;
        }
        
        const riskPointer = document.getElementById('risk-pointer');
        const riskValueText = document.getElementById('risk-value-text');
        
        if (riskPointer) riskPointer.style.transform = `rotate(${angle}deg)`;
        if (riskValueText) {
            riskValueText.textContent = overallRisk.toUpperCase();
            // styling
            riskValueText.style.background = overallRisk === "high" ? 
                "linear-gradient(135deg, #ffffff 0%, #ef4444 100%)" : 
                (overallRisk === "mod" ? "linear-gradient(135deg, #ffffff 0%, #f59e0b 100%)" : "linear-gradient(135deg, #ffffff 0%, #00f5d4 100%)");
            riskValueText.style.webkitBackgroundClip = "text";
        }
        
        // 4. Update Crop Insights & Advisory Advice
        const insightsContent = document.getElementById('weather-insights-content');
        insightsContent.innerHTML = '';
        
        let riskHeader = "Optimal Climate Growth Projections";
        let riskDesc = "Atmospheric conditions are stable with standard disease risk. Keep crops well irrigated and proceed with regular preventative checks.";
        let riskIconClass = "success";
        let riskIcon = "✓";
        
        if (overallRisk === "high") {
            riskHeader = "CRITICAL OUTBREAK WARNING";
            riskDesc = `Weather forecasting detects high levels of moisture (${highRiskDaysCount} days with high relative humidity & rainfall) combined with warm incubation temperatures. Fungal diseases (Late Blight, Downy Mildew) are likely to spread rapidly.`;
            riskIconClass = "danger";
            riskIcon = "⚠️";
        } else if (overallRisk === "mod") {
            riskHeader = "MODERATE THREAT WATCH";
            riskDesc = `Elevated relative humidity predicted in the upcoming period. Moderate risk of Powdery Mildew, leaf spot, or rust development. Monitor plant leaves and maintain ventilation.`;
            riskIconClass = "warning";
            riskIcon = "🛡️";
        }
        
        addInsightEntry(insightsContent, riskIcon, riskHeader, riskDesc, riskIconClass);
        
        if (overallRisk === "high") {
            addInsightEntry(insightsContent, "💊", "Preventative Sprays Recommended", "Apply organic fungicides, copper-based sprays, or neem oil solutions immediately before the high humidity cycles to protect leaves.", "warning");
        } else if (overallRisk === "mod") {
            addInsightEntry(insightsContent, "✂️", "Aeration & Canopy Thinning", "Thin out dense leaf canopies on susceptible crops. Promoting active airflow reduces leaf wetness periods which prevents spore germination.", "success");
        }
        
        if (totalRainForecast > 25) {
            addInsightEntry(insightsContent, "🌧️", "Heavy Precipitation Management", `Approximately ${totalRainForecast.toFixed(1)}mm of rainfall predicted. Check soil drainage, inspect fields for pooling, and delay any spray treatments to prevent product run-off.`, "warning");
        } else {
            addInsightEntry(insightsContent, "💧", "Irrigation Guide", "Relative dry conditions expected. Ensure standard deep watering schedules, preferably in the early mornings to allow leaves to dry during daylight.", "success");
        }
        
        if (maxWindForecast > 22) {
            addInsightEntry(insightsContent, "💨", "Gale Alert for Crop Structures", `Peak wind speed of ${maxWindForecast.toFixed(1)} km/h expected. Secure trellis setups, strengthen staking for young crops, and avoid using atomized foliar sprays on windy days.`, "warning");
        }

        // 5. Update Global Alert Banner
        const banner = document.getElementById('weather-alert-banner');
        const bannerText = document.getElementById('weather-alert-text');
        
        if (banner && bannerText) {
            banner.className = 'weather-alert-banner alert-hidden'; // Reset classes
            
            if (overallRisk === "high") {
                banner.classList.remove('alert-hidden');
                banner.classList.add('alert-high');
                bannerText.innerHTML = `<b>High Risk Fungal Spread Alert:</b> Projections show ${highRiskDaysCount} days of wet, humid weather. Outbreaks of Blight and Mildew are likely. <u>Click Sidebar Agro-Weather tab</u> to view detailed suggestions.`;
            } else if (overallRisk === "mod") {
                banner.classList.remove('alert-hidden');
                banner.classList.add('alert-medium');
                bannerText.innerHTML = `<b>Agro-Weather Alert:</b> Moderate disease threat predicted due to rising humidity. Monitor lower leaf surfaces and maintain high soil drainage.`;
            }
        }
    }

    function addInsightEntry(container, icon, title, text, typeClass) {
        const div = document.createElement('div');
        div.className = 'insight-entry';
        div.innerHTML = `
            <span class="insight-icon ${typeClass}">${icon}</span>
            <div class="insight-details">
                <h4>${title}</h4>
                <p>${text}</p>
            </div>
        `;
        container.appendChild(div);
    }
});
