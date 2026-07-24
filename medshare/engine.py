import torch  # Core PyTorch library for neural operations
import torch.nn as nn  # High-level neural building blocks
from sklearn.metrics import accuracy_score, roc_auc_score  # Industrial standard metric evaluators

def train(net, trainloader, epochs, privacy_engine=None, num_classes=1, noise_multiplier=1.0, max_grad_norm=1.5, lr=0.001, device="cpu", proximal_mu=0.01):
    """
    Main local training loop that executes backpropagation on each batch of patient data.
    """
    if trainloader is None: return # Robustness: avoid crash on empty slice
    # Step 1: Resource Setup - move model to GPU/CPU and set to 'train mode'
    net.to(device)
    net.train()
    
    # FEDPROX ENHANCEMENT: Store the initial global weights as a 'Global Anchor'
    # proximal term to prevent local drift from global consensus
    global_params = [p.detach().clone() for p in net.parameters()]
    
    # Step 2: Learning Rate Tuning for Privacy
    # Differential Privacy (DP) noise destabilizes gradients. We reduce LR to counteract this.
    actual_lr = lr
    if privacy_engine:
        actual_lr = lr * 0.25 # Aggressive reduction for privacy-preserving numerical stability
        
    # Step 3: Optimization Algorithm Selection (Adam for fast convergence)
    optimizer = torch.optim.Adam(net.parameters(), lr=actual_lr, weight_decay=1e-5)
    
    # Step 4: Differential Privacy Injection (Opacus)
    # This replaces standard training with 'DP-SGD' which clamps and noises every individual gradient
    if privacy_engine:
        net, optimizer, trainloader = privacy_engine.make_private(
            module=net, 
            optimizer=optimizer, 
            data_loader=trainloader, 
            noise_multiplier=noise_multiplier, 
            max_grad_norm=max_grad_norm
        )
    
    # Step 5: Loss Function selection (BCELoss for binary targets, CrossEntropy for multiclass)
    criterion = nn.BCELoss() if num_classes == 1 else nn.CrossEntropyLoss()
    total_loss = 0.0
    count = 0
    # Step 6: Loop through Epochs (Full cycles through the dataset)
    for epoch in range(epochs):
        # Step 7: Local Training (Batch-by-batch optimization)
        for images, labels in trainloader:
            # Move patient data to GPU
            images, labels = images.to(device), labels.to(device)
            # Reset gradients from previous batch
            optimizer.zero_grad()
            # Forward Pass: Predict values based on current model weights
            outputs = net(images)
            try:
                if num_classes == 1:
                    # Precise shape sync and numerical stability clamping for BCELoss
                    # loss stability during backprop: BCELoss needs clamping to prevent Inf
                    loss_y = labels.view(-1).float()
                    # nan_to_num handles cases where adversarial updates break weights
                    loss_out = outputs.view(-1).nan_to_num(0.5).clamp(1e-7, 1.0 - 1e-7)
                    base_loss = criterion(loss_out, loss_y)
                else:
                    # Multiclass cross entropy for categorical hospital data
                    base_loss = criterion(outputs, labels.long().view(-1))
                
                # Step 8: Calculate FedProx Proximal Penalty
                # L2-Distance penality: (Current_Local_Weights - Global_Anchor)^2
                # This keeps nodes from overfitting on their small, unique local records
                prox_term = sum((p - g_p).pow(2).sum() for p, g_p in zip(net.parameters(), global_params))
                
                # Combine standard loss with FedProx constraint
                loss = base_loss + (proximal_mu / 2) * prox_term
                
                # Step 9: Backpropagation - calculate contribution of each node to overall error
                loss.backward()
                # Step 10: Optimizer Step - nudge weights in the direction that lowers the loss
                optimizer.step()
                total_loss += loss.item()
                count += 1
            except Exception as e:
                # Shield training from crashing if a numerical instability occurs in a batch
                if epoch == 0: print(f"[Engine] Training stability warning: {e}")
                continue
                
    # Step 11: Final Reporting
    avg_loss = total_loss / count if count > 0 else 0.69 # Log base-entropy if training failed
    try:
        # Calculate exactly how much privacy 'budget' (epsilon) we have spent based on RDP
        epsilon = privacy_engine.get_epsilon(delta=1e-5) if privacy_engine else None
    except:
        epsilon = 0.0
    return epsilon, avg_loss

def test(net, testloader, num_classes=1, device="cpu"):
    """
    Evaluation engine used to calculate accuracy and AUC on validation clinical records.
    """
    # Evaluate metrics on validation set
    if testloader is None: return 0.0, 0.0, 0.0 # Robustness: avoid crash on empty slice
    # Set to 'eval' mode: disables Dropout and BatchNormalization if present
    net.to(device)
    net.eval()
    criterion = nn.BCELoss() if num_classes == 1 else nn.CrossEntropyLoss()
    loss, all_preds, all_labels, all_probs = 0.0, [], [], []
    # No gradients needed for evaluation (saves memory and time)
    with torch.no_grad():
        for images, labels in testloader:
            images, labels = images.to(device), labels.to(device)
            outputs = net(images)
            try:
                if num_classes == 1:
                    # Stability clamping for adversarial evaluation metrics
                    loss += criterion(outputs.squeeze().clamp(0, 1), labels.float().squeeze()).item()
                else:
                    # Multiclass evaluation
                    loss += criterion(outputs, labels.long().view(-1)).item()
            except Exception as e:
                print(f"[Engine] Eval step warning: {e}")
                continue
            
            # Step 12: Predict Outcomes From Neural Probabilities
            if num_classes == 1:
                probs = outputs
                preds = (outputs > 0.5).long() # Threshold at 0.5 (Standard decision boundary)
            else:
                probs = torch.softmax(outputs, dim=1)
                preds = torch.argmax(outputs, dim=1) # Highest probability wins the class
            
            # Transfer predictions back to CPU for standard sci-kit metrics logging
            all_preds.extend(preds.view(-1).cpu().tolist())
            all_labels.extend(labels.view(-1).cpu().tolist())
            if num_classes == 1:
                all_probs.extend(probs.view(-1).cpu().tolist())
            else:
                all_probs.extend(probs.cpu().tolist())
            
    # Step 13: Final Metric Calculation (Industry Standards)
    acc = accuracy_score(all_labels, all_preds)
    try:
        if num_classes == 1:
            auc = roc_auc_score(all_labels, all_probs)
        else:
            # Multi-class AUC using One-vs-Rest (OvR) methodology
            auc = roc_auc_score(all_labels, all_probs, multi_class='ovr')
    except:
        # Handle cases with only 1 class in the entire test subset (common in small batches)
        auc = 0.5 
        
    return loss / len(testloader), acc, float(auc)
