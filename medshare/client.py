import torch, flwr
from torch.utils.data import DataLoader, TensorDataset
from .models import get_parameters, set_parameters
from .engine import train, test
from .blockchain import BlockchainManager

class FlowerSurvivalClient(flwr.client.NumPyClient):
    def __init__(self, net, trainloader, valloader, num_classes=1, mask_add=None, mask_sub=None, is_malicious=False, client_id=0, task_id=0, attack_type="label_flip", enable_dp=False, noise_multiplier=1.0, max_grad_norm=1.5, attack_scale_factor=100.0, local_epochs=1, enable_blockchain=False):
        self.net, self.trainloader, self.valloader = net, trainloader, valloader
        self.num_classes, self.mask_add, self.mask_sub = num_classes, mask_add, mask_sub
        self.is_malicious, self.client_id, self.task_id = is_malicious, client_id, task_id
        self.attack_type, self.enable_dp = attack_type, enable_dp
        self.noise_multiplier, self.max_grad_norm, self.attack_scale_factor = noise_multiplier, max_grad_norm, attack_scale_factor
        self.local_epochs, self.enable_blockchain = local_epochs, enable_blockchain
        
        # GPU Support Detection
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.net.to(self.device)

        if self.is_malicious and self.attack_type == "label_flip":
             X, y = next(iter(DataLoader(self.trainloader.dataset, batch_size=len(self.trainloader.dataset))))
             # Handle multi-class label flipping: shift labels by 1 modulo num_classes
             if self.num_classes > 1:
                 y_flipped = (y.long() + 1) % self.num_classes
                 y_flipped = y_flipped.float()
             else:
                 y_flipped = 1.0 - y
             self.trainloader = DataLoader(TensorDataset(X, y_flipped), batch_size=32, shuffle=True)

    def fit(self, parameters, config):
        print(f"[Client {self.client_id}] Starting fit on {self.device}...")
        set_parameters(self.net, parameters)
        pe = None
        if self.enable_dp:
            from opacus import PrivacyEngine
            pe = PrivacyEngine(accountant="rdp")
        
        eps, train_loss = train(self.net, self.trainloader, epochs=self.local_epochs, privacy_engine=pe, 
                              num_classes=self.num_classes, noise_multiplier=self.noise_multiplier, 
                              max_grad_norm=self.max_grad_norm, device=self.device)
        
        # Weights must be on CPU for serialization back to server
        weights = get_parameters(self.net.cpu())
        self.net.to(self.device) # Move back to GPU for testing

        # Blockchain Commitment & Gas Tracking
        gas_used = 0
        if self.enable_blockchain:
            bcm = BlockchainManager.get_instance()
            if bcm:
                try: 
                    gas_used = bcm.post_commitment(self.task_id, int(config.get("server_round", 0)), weights, self.client_id)
                except Exception as e:
                    print(f"[Client {self.client_id}] Blockchain log failed: {e}")
        
        if self.is_malicious and self.attack_type == "gradient_scale":
            weights = [w * self.attack_scale_factor for w in weights]
        
        # Calculate training and validation metrics
        _, train_acc, train_auc = test(self.net, self.trainloader, num_classes=self.num_classes, device=self.device)
        _, val_acc, val_auc = test(self.net, self.valloader, num_classes=self.num_classes, device=self.device)
        
        # Combine client metrics with server-provided config metadata
        metrics = {
            "accuracy": float(val_acc), 
            "auc": float(val_auc),
            "loss": float(train_loss),
            "privacy_spent": float(eps) if eps is not None else 0.0,
            "train_accuracy": float(train_acc),
            "test_accuracy": float(val_acc),
            "test_auc": float(val_auc),
            "gas_used": int(gas_used) if gas_used else 0,
            "client_id": int(self.client_id),
            "noise_multiplier": float(self.noise_multiplier),
            "attack_type": str(self.attack_type),
            "is_malicious": bool(self.is_malicious),
            "experiment": str(self.experiment_info if hasattr(self, 'experiment_info') else "none")
        }
        
        # Inject all server config (total_rounds, defense_name, etc.) into metrics
        for k, v in config.items():
            metrics[k] = v
            
        return weights, len(self.trainloader.dataset), metrics

    def evaluate(self, parameters, config):
        set_parameters(self.net, parameters)
        loss, accuracy, auc = test(self.net, self.valloader, num_classes=self.num_classes, device=self.device)
        
        metrics = {"accuracy": float(accuracy), "auc": float(auc)}
        # Inject all server config (total_rounds, experiment type, etc.) for proper logging
        for k, v in config.items():
            metrics[k] = v
            
        return float(loss), len(self.valloader.dataset), metrics
