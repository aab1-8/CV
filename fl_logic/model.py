# --------------------------------------------------------------------------------------
# MODEL.PY
# This file defines the Neural Network architecture and helper functions.
# --------------------------------------------------------------------------------------
import torch
import torch.nn as nn
from collections import OrderedDict

def get_parameters(net):
    """Extract weights from the model to send to server."""
    return [val.cpu().numpy() for _, val in net.state_dict().items()]

def set_parameters(net, parameters):
    """Update the model with new weights received from server."""
    params_dict = zip(net.state_dict().keys(), parameters)
    state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
    net.load_state_dict(state_dict, strict=True)

class SurvivalMLP(nn.Module):
    """Our Deep Learning Model (Multi-Layer Perceptron)."""
    def __init__(self, input_dim):
        super(SurvivalMLP, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 32), # Layer 1: Inputs -> 32 neurons
            nn.ReLU(),                # Activation: Filter negatives
            nn.Dropout(0.2),          # Dropout: Randomly ignore 20% to prevent memorizing
            nn.Linear(32, 16),        # Layer 2: 32 -> 16 neurons
            nn.ReLU(),                # Activation
            nn.Linear(16, 1),         # Output: 16 -> 1 single score
            nn.Sigmoid()              # Sigmoid: Squash score to 0-1 probability
        )

    def forward(self, x):
        return self.fc(x)

def train(net, trainloader, epochs):
    """Local Training Loop: Learns from local data."""
    criterion = nn.BCELoss() # Binary Cross Entropy Loss
    optimizer = torch.optim.Adam(net.parameters(), lr=0.01) # Standard Optimizer
    net.train()
    for _ in range(epochs):
        for images, labels in trainloader:
            optimizer.zero_grad() # Reset gradients
            outputs = net(images) # Predict
            loss = criterion(outputs, labels.unsqueeze(1).float()) # Measure error
            loss.backward() # Calculate corrections
            optimizer.step() # Apply corrections

def test(net, testloader):
    """Local Evaluation Loop: Checks accuracy on local test data."""
    criterion = nn.BCELoss()
    correct, total, loss = 0, 0, 0.0
    net.eval()
    with torch.no_grad():
        for images, labels in testloader:
            outputs = net(images)
            loss += criterion(outputs, labels.unsqueeze(1).float()).item()
            total += labels.size(0)
            predicted = (outputs > 0.5).float()
            correct += (predicted.squeeze() == labels).sum().item()
    return loss / len(testloader), correct / total
