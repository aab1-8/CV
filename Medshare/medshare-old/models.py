import torch
import torch.nn as nn
from collections import OrderedDict

def get_parameters(net):
    """
    Extracted as a helper to convert PyTorch tensors into NumPy arrays.
    NumPy arrays are required by the Flower (flwr) framework for network transmission.
    """
    # Loops through the model state, moves every weight to CPU, and converts to a NumPy array
    return [val.cpu().numpy() for _, val in net.state_dict().items()]

def set_parameters(net, parameters):
    """
    The inverse of get_parameters: takes NumPy arrays from the server and loads them into the model.
    """
    # Guard clause: if no parameters are provided, do nothing
    if not parameters: return
    # Pairs the weight names (keys) with the incoming values (parameters)
    params_dict = zip(net.state_dict().keys(), parameters)
    # Creates an OrderedDict of Tensors—strict=True ensures dimensions must match exactly
    state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
    # Loads the state into the neural network
    net.load_state_dict(state_dict, strict=True)

class SurvivalMLP(nn.Module):
    """
    A Multi-Layer Perceptron (MLP) optimized for clinical tabular data.
    Structure: Input -> 256 Nodes -> ReLU -> 128 Nodes -> ReLU -> Output
    """
    def __init__(self, input_dim, num_classes=1):
        # Initialize the parent nn.Module class
        super().__init__()
        # layers starts as a list of sequentially executed operations
        layers = [
            nn.Linear(input_dim, 256),  # First Hidden Layer: mapping input to 256 features
            nn.ReLU(),  # Activation function to introduce non-linearity (capture complex patterns)
            nn.Linear(256, 128),  # Second Hidden Layer: refining features to 128 nodes
            nn.ReLU(),  # ReLU activation
            nn.Linear(128, num_classes if num_classes > 1 else 1)  # Final classification layer
        ]
        # For binary classification (num_classes=1), we add a Sigmoid to squash output to [0,1] probability
        if num_classes == 1: layers.append(nn.Sigmoid())
        # Packages the list of operations into a single executable pipeline
        self.fc = nn.Sequential(*layers)

    def forward(self, x): 
        # Defines the computation performed at every "Step" or "Round"
        return self.fc(x)
