import pennylane as qml
import torch
import torch.nn as nn
from pennylane.qnn import TorchLayer
import torchvision.models as models

# Small quantum layer example with 4 qubits
n_qubits = 4
dev = qml.device('default.qubit', wires=n_qubits)

def circuit(weights, x):
    # x is length n_qubits
    for i in range(n_qubits):
        qml.RY(x[i], wires=i)
    for i in range(n_qubits):
        qml.RY(weights[i], wires=i)
    for i in range(n_qubits - 1):
        qml.CNOT(wires=[i, i+1])
    return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]

weight_shapes = {'weights': n_qubits}
qnode = qml.QNode(circuit, dev, interface='torch', diff_method='backprop')
qlayer = TorchLayer(qnode, weight_shapes)

class HybridNet(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        base = models.resnet18(pretrained=True)
        modules = list(base.children())[:-1]
        self.feature_extractor = nn.Sequential(*modules)
        self.reduce = nn.Linear(512, n_qubits)
        self.qlayer = qlayer
        self.classifier = nn.Linear(n_qubits, num_classes)

    def forward(self, x):
        features = self.feature_extractor(x)
        features = features.view(features.size(0), -1)
        small = torch.tanh(self.reduce(features))
        # map to [0, pi]
        small = (small + 1.0) * (3.1415/2.0)
        q_out = torch.stack([self.qlayer(small[i]) for i in range(small.shape[0])])
        logits = self.classifier(q_out)
        return logits
