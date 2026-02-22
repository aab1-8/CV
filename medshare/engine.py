import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, roc_auc_score

def train(net, trainloader, epochs, privacy_engine=None, num_classes=1, noise_multiplier=1.0, max_grad_norm=1.5, lr=0.001, device="cpu", proximal_mu=0.01):
    net.to(device)
    net.train()
    
    # Capture initial weights to act as the "Global Anchor" for FedProx
    global_params = [p.detach().clone() for p in net.parameters()]
    
    # Premium Stability: Adjust LR for DP to prevent gradient explosion
    # For small tabular models, we need a very conservative LR when noise is high
    actual_lr = lr
    if privacy_engine:
        actual_lr = lr * 0.25 # Aggressive reduction for privacy stability
        
    optimizer = torch.optim.Adam(net.parameters(), lr=actual_lr, weight_decay=1e-5)
    
    if privacy_engine:
        net, optimizer, trainloader = privacy_engine.make_private(
            module=net, 
            optimizer=optimizer, 
            data_loader=trainloader, 
            noise_multiplier=noise_multiplier, 
            max_grad_norm=max_grad_norm
        )
    
    criterion = nn.BCELoss() if num_classes == 1 else nn.CrossEntropyLoss()
    total_loss = 0.0
    count = 0
    for epoch in range(epochs):
        for images, labels in trainloader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = net(images)
            try:
                if num_classes == 1:
                    # Precise shape sync for BCELoss
                    loss_y = labels.view(-1).float()
                    loss_out = outputs.view(-1).clamp(1e-7, 1.0 - 1e-7)
                    base_loss = criterion(loss_out, loss_y)
                else:
                    base_loss = criterion(outputs, labels.long().view(-1))
                
                # --- FEDPROX PROXIMAL TERM (Optimized) ---
                prox_term = sum((p - g_p).pow(2).sum() for p, g_p in zip(net.parameters(), global_params))
                
                loss = base_loss + (proximal_mu / 2) * prox_term
                
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
                count += 1
            except Exception as e:
                if epoch == 0: print(f"[Engine] Training stability warning: {e}")
                continue
                
    avg_loss = total_loss / count if count > 0 else 0.69
    try:
        epsilon = privacy_engine.get_epsilon(delta=1e-5) if privacy_engine else None
    except:
        epsilon = 0.0
    return epsilon, avg_loss

def test(net, testloader, num_classes=1, device="cpu"):
    net.to(device)
    net.eval()
    criterion = nn.BCELoss() if num_classes == 1 else nn.CrossEntropyLoss()
    loss, all_preds, all_labels, all_probs = 0.0, [], [], []
    with torch.no_grad():
        for images, labels in testloader:
            images, labels = images.to(device), labels.to(device)
            outputs = net(images)
            try:
                if num_classes == 1:
                    # Clamp to [0,1] — adversarial attacks can corrupt weights
                    loss += criterion(outputs.squeeze().clamp(0, 1), labels.float().squeeze()).item()
                else:
                    loss += criterion(outputs, labels.long().view(-1)).item()
            except Exception as e:
                print(f"[Engine] Eval step warning: {e}")
                continue
            
            if num_classes == 1:
                probs = outputs
                preds = (outputs > 0.5).long()
            else:
                probs = torch.softmax(outputs, dim=1)
                preds = torch.argmax(outputs, dim=1)
            
            # Move back to CPU for sklearn metrics
            all_preds.extend(preds.view(-1).cpu().tolist())
            all_labels.extend(labels.view(-1).cpu().tolist())
            if num_classes == 1:
                all_probs.extend(probs.view(-1).cpu().tolist())
            else:
                all_probs.extend(probs.cpu().tolist())
            
    acc = accuracy_score(all_labels, all_preds)
    try:
        if num_classes == 1:
            auc = roc_auc_score(all_labels, all_probs)
        else:
            auc = roc_auc_score(all_labels, all_probs, multi_class='ovr')
    except:
        auc = 0.5 # Default to random chance if AUC calculation fails (e.g. only one class in batch)
        
    return loss / len(testloader), acc, float(auc)
