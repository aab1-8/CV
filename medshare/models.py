import torch
import torch.nn as nn
from collections import OrderedDict

def get_parameters(net):
    return [val.cpu().numpy() for _, val in net.state_dict().items()]

def set_parameters(net, parameters):
    if not parameters: return
    params_dict = zip(net.state_dict().keys(), parameters)
    state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
    net.load_state_dict(state_dict, strict=True)

class SurvivalMLP(nn.Module):
    def __init__(self, input_dim, num_classes=1):
        super().__init__()
        layers = [nn.Linear(input_dim, 256), nn.ReLU(), nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, num_classes if num_classes > 1 else 1)]
        if num_classes == 1: layers.append(nn.Sigmoid())
        self.fc = nn.Sequential(*layers)
    def forward(self, x): return self.fc(x)
