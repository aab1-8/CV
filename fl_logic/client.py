# --------------------------------------------------------------------------------------
# CLIENT.PY
# This file acts as the "Agent" for the hospital.
# --------------------------------------------------------------------------------------
import flwr as fl
import torch
from fl_logic.model import get_parameters, set_parameters, train, test

class FlowerSurvivalClient(fl.client.NumPyClient):
    """The Flower Client that connects to the FedAvg Server."""
    def __init__(self, net, trainloader, valloader):
        self.net = net
        self.trainloader = trainloader
        self.valloader = valloader

    def get_parameters(self, config):
        """Send weights to server."""
        return get_parameters(self.net)

    def fit(self, parameters, config):
        """Receive global weights, Train locally, Send back updates."""
        set_parameters(self.net, parameters)
        train(self.net, self.trainloader, epochs=5)
        return get_parameters(self.net), len(self.trainloader.dataset), {}

    def evaluate(self, parameters, config):
        """Receive global weights, Test locally, Send back accuracy."""
        set_parameters(self.net, parameters)
        loss, accuracy = test(self.net, self.valloader)
        return float(loss), len(self.valloader.dataset), {"accuracy": float(accuracy)}
