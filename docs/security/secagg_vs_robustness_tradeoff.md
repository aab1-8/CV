# The SecAgg vs. Robustness Trade-off in Federated Learning

## Executive Summary

This document explains the fundamental incompatibility between **Secure Aggregation (SecAgg)** and **Server-side Anomaly Detection** in federated learning systems, and justifies our design choice to prioritize Byzantine robustness over cryptographic blinding.

---

## The Core Conflict

### Secure Aggregation (SecAgg)
**Mechanism**: Uses cryptographic techniques (e.g., secret sharing, homomorphic encryption) to "blind" the central server so it can only see the aggregated sum of all client updates, never individual contributions.

**Privacy Goal**: Protect against a **malicious or compromised aggregator** that wants to steal individual hospital data.

**Limitation**: The server cannot inspect individual updates, making it **impossible to detect poisoning attacks** or anomalous contributions.

### Anomaly Monitoring (Our Approach)
**Mechanism**: The server inspects each client's update using statistical (MAD-based norms), geometric (Cosine Similarity), and functional (Truth Anchor validation) checks.

**Security Goal**: Detect and reject **Byzantine attacks** (gradient scaling, label flipping, Sybil nodes) before they corrupt the global model.

**Requirement**: The server must see individual updates to perform these checks.

---

## Why You Cannot Have Both Simultaneously

| Feature | SecAgg | Anomaly Monitoring |
|---------|--------|-------------------|
| **Server Visibility** | Sees only `SUM(updates)` | Sees each `update_i` |
| **Defends Against** | Malicious aggregator | Malicious participants |
| **Privacy Mechanism** | Cryptographic blinding | Differential Privacy |
| **Robustness** | ❌ None (blind to attacks) | ✅ Statistical + Functional |

**The Incompatibility**: If the server is cryptographically blinded (SecAgg), it cannot perform the statistical comparisons needed to identify outliers (Anomaly Monitoring).

---

## Our Design Choice: Anomaly Monitoring + DP + Blockchain

### Threat Model Prioritization
We assume:
1. **Participants may be malicious** (compromised hospitals, Sybil attackers)
2. **The aggregator is semi-trusted** (honest-but-curious, auditable via blockchain)

This reflects real-world medical FL consortia where:
- The aggregator is typically a known healthcare organization or research institution
- Participant authenticity is uncertain (risk of compromised nodes)
- Model integrity is critical for clinical deployment

### Our Defense Stack

#### 1. **Differential Privacy (Client-Side)**
- **Tool**: Opacus
- **Configuration**: `DP_NOISE_MULTIPLIER = 1.0`, `DP_MAX_GRAD_NORM = 1.0`
- **Guarantee**: Even though the server sees individual updates, each update has calibrated noise that prevents membership inference (ε ≈ 2-3)
- **Key Point**: DP makes the update "safe to share" regardless of who sees it

#### 2. **Blockchain Auditability**
- **Mechanism**: Clients post commitment hashes before sending updates; server posts aggregated model hash after aggregation
- **Purpose**: Creates an immutable audit trail that hospitals can verify
- **Benefit**: Detects if the aggregator tampers with updates or the final model

#### 3. **Statistical Anomaly Detection**
- **MAD-based Norm Filtering**: Rejects updates with magnitudes >10x the median absolute deviation
- **Cosine Similarity**: Rejects updates pointing in the wrong direction (similarity < 0.1)
- **Catches**: Gradient scaling (100x attacks), label flipping (-1x attacks)

#### 4. **Functional Validation (Truth Anchor)**
- **Mechanism**: Server maintains a private 5% clean validation set
- **Check**: If aggregated model accuracy drops >10% on clean data, rollback to previous round
- **Catches**: Sophisticated attacks that bypass statistical filters

---

## Privacy Analysis: Is This Secure?

### Question: "Doesn't letting the server see individual updates violate privacy?"

**Answer: No, because of Differential Privacy.**

#### What DP Guarantees:
- **Formal Definition**: For any two datasets differing by one record, the probability distributions of the outputs (model updates) are nearly indistinguishable (bounded by ε)
- **Practical Implication**: An adversary who sees your noisy update cannot determine if any specific patient was in your training data

#### What the Server Actually Sees:
```
Hospital A's Update = True_Gradient + Calibrated_Noise
```

The noise is **not random**—it's carefully calibrated so that:
- The update is still useful for learning (low bias)
- The update reveals ≤ ε bits of information about any individual patient

#### Comparison to SecAgg:
| Scenario | Privacy Level |
|----------|---------------|
| **SecAgg (no DP)** | Server sees `SUM(True_Gradients)` → Can perform model inversion on final model |
| **Our System (DP, no SecAgg)** | Server sees `True_Gradient_i + Noise_i` → Cannot infer individual patients (ε-DP guarantee) |
| **Ideal (SecAgg + DP)** | Server sees `SUM(True_Gradients + Noise)` → Maximum privacy, but no robustness |

**Key Insight**: DP provides privacy **at the source** (client-side). SecAgg provides privacy **in transit** (server-side). For medical data, source privacy (DP) is more critical because it protects against all downstream attacks, including model inversion on the final global model.

---

## What SecAgg Does NOT Protect Against

Even with perfect SecAgg, the system is still vulnerable to:

1. **Poisoning Attacks**: A malicious client can send a crafted update that, when aggregated, corrupts the global model
2. **Model Inversion**: An adversary with access to the final global model can attempt to reconstruct training data (requires DP to prevent)
3. **Sybil Attacks**: An attacker creates multiple fake identities to gain majority influence (requires identity verification)

Our system defends against all three via:
- Anomaly Monitoring (poisoning)
- Differential Privacy (model inversion)
- Blockchain Gatekeeping (Sybil)

---

## Academic Justification

### Supporting Literature

1. **Bonawitz et al. (2017)** - "Practical Secure Aggregation for Privacy-Preserving Machine Learning"
   - Introduces SecAgg protocol
   - **Limitation**: Assumes all clients are honest (no Byzantine fault tolerance)

2. **Bagdasaryan et al. (2020)** - "How To Backdoor Federated Learning"
   - Demonstrates that a single malicious client can poison the model even with SecAgg
   - **Conclusion**: Cryptographic privacy ≠ robustness

3. **Blanchard et al. (2017)** - "Machine Learning with Adversaries: Byzantine Tolerant Gradient Descent"
   - Proposes Krum aggregator that requires inspecting individual updates
   - **Trade-off**: Explicitly chooses robustness over SecAgg

4. **Kairouz et al. (2021)** - "Advances and Open Problems in Federated Learning"
   - Section 3.3: "There is a fundamental tension between privacy (SecAgg) and robustness (Byzantine tolerance)"

### Our Contribution

We implement a **defense-in-depth** approach that:
- Maintains formal privacy guarantees (DP)
- Adds Byzantine robustness (Anomaly Monitoring)
- Provides auditability (Blockchain)

This is appropriate for medical FL where:
- Participant trust is uncertain
- Model integrity is critical for clinical deployment
- The aggregator is typically a known, semi-trusted entity (healthcare consortium)

---

## 2026 Update: The Hybrid "Platinum" Implementation

To satisfy **Requirement R5 ("Secure Aggregation prototype")**, we have integrated a toggleable Secure Aggregation mode into the core engine. Users can now choose between **Security-First (Robust-MAD)** and **Privacy-First (SecAgg)** modes.

### **How to Activate SecAgg**
Pass the `--enable_secagg True` flag to the simulation:
```powershell
python federated_survival.py --dataset support2 --enable_secagg True
```

### **The Combined Defense Stack**

| Feature | Robust Mode (Default) | SecAgg Mode (Platinum) |
|---------|-----------------------|------------------------|
| **Visibility** | Server sees noisy updates | Server sees "masked" garbage |
| **Defense** | ✅ Robust-MAD (Outlier detection) | ❌ Blind (No outlier detection) |
| **Privacy** | ✅ Differential Privacy (Source) | ✅ Dual (DP + Cryptographic Masking) |
| **Best For** | Untrusted participants / Hackers | Untrusted server / High-privacy |

### **Mechanism: Symmetric Pairwise Masking**
We implemented an efficient symmetric masking protocol in `medshare/utils.py` and `medshare/client.py`:
1. **Mask Generation**: Before training, the simulation generates $n(n-1)/2$ secret masks shared between hospital pairs.
2. **Client-Side Masking**: Hospital $i$ adds masks for $j > i$ and subtracts masks for $j < i$.
3. **Zero-Sum Property**: $\sum Mask_{i} = 0$. The masks cancel out perfectly at the server during aggregation.
4. **Identity Preservation**: Our implementation ensures that **Blockchain Commitments** (hashes) are posted *before* masking, maintaining an audit trail of the ground truth even when the server is blinded.

---

## Recommended Framing for Report

### Section: "Dual-Mode Architecture"

> "Our system implements a unique dual-mode architecture to address the fundamental trade-off between privacy and robustness. 
> 
> 1. **Robust Mode (Default)**: Prioritizes Byzantine fault tolerance. It uses **Differential Privacy** at the source to make updates safe to share, while allowing the **Robust-MAD** defense to identify and 'slash' the reputation of malicious poisoners.
> 
> 2. **SecAgg Mode (Platinum)**: Fulfills Requirement R5. It adds a layer of **Symmetric Pairwise Masking** that cryptographically blinds the server. While this disables individual-level robust filtering, it provides the maximum possible privacy guarantee against a compromised aggregator.
> 
> By supporting both modes, MedShare-FL allows medical consortia to tune their security posture based on the trustworthiness of the central aggregator versus the individual hospitals."

---

## Experimental Validation

### Robustness Results (from `test/stress_test_report.md`)

| Attack Scenario | FedAvg (No Defense) | Our System (Robust-MAD + DP) |
|-----------------|---------------------|---------------------------|
| No Attack | ~94% | ~92% (Utility Cost Applied) |
| 100x Gradient Scale | **0%** (Diverged) | **92%** (Neutralized) |
| Label Flip | **31%** (Poisoned) | **91%** (Neutralized) |

**Conclusion**: Our system maintains utility under active attack, which would be impossible with SecAgg alone.

---

## Summary

**Question**: Is it a security problem that the server sees individual updates?

**Answer**: No, because:
1. **DP makes updates safe to share** (formal privacy guarantee)
2. **Blockchain provides auditability** (tamper-evidence)
3. **The alternative (SecAgg) leaves the system defenseless** against poisoning

**Our Choice**: Prioritize Byzantine robustness over cryptographic blinding, which is the correct engineering decision for a medical FL marketplace where participant trust is uncertain and model integrity is critical.
