# Membership Inference Audit: Methodology & Proxy Selection

**MedShare Project — Privacy Engineering Documentation**  
*Last updated: 2026-03-05*

---

## 1. What is Membership Inference?

A **Membership Inference (MI) Attack** is a privacy attack where an adversary, given only the output of a trained machine learning model, attempts to determine whether a **specific record was part of the training dataset**.

In a medical federated learning context this is critical: if an attacker can determine that Patient X's record was used to train Hospital 3's model, they have effectively learned something private about that patient — even without ever seeing the raw record.

**Formal definition:**  
Given a model `f`, a record `x`, and its label `y`, the attacker builds a binary classifier:

```
MI_attack(f, x, y) → {MEMBER, NON-MEMBER}
```

---

## 2. The Four Major Approaches

### 2.1 Generalization Gap Proxy

**Formula:**
```
MI_score = max(0, train_accuracy - val_accuracy)
```

**How it works:**  
A model that has memorised its training data will score noticeably higher on training records than on unseen validation records. The gap between these two accuracies is used as a proxy for how much the model "remembers" its training data.  

**Source:** Yeom et al. (2018), *"Privacy Risk in Machine Learning: Analyzing the Connection to Overfitting"*, IEEE S&P.

| | |
|:--|:--|
| ✅ **Advantage — Simple** | Requires only train and validation accuracy, both already computed |
| ✅ **Advantage — Fast** | Zero extra compute — calculated from existing metrics |
| ✅ **Advantage — Interpretable** | Directly linked to the well-understood concept of overfitting |
| ❌ **Weakness — Accuracy blindspot** | A model can perfectly generalise (same train/val accuracy) but still leak via overconfidence in its probability outputs. In this case, `MI_score = 0` even though real leakage exists |
| ❌ **Weakness — Imbalanced data** | On imbalanced medical datasets, accuracy is a poor metric. A model predicting the majority class always achieves high accuracy with no real learning — making the gap meaningless |

---

### 2.2 AUC-Gap Proxy *(Selected Approach)*

**Formula:**
```
MI_score = max(0, train_AUC - val_AUC)
```

Where **AUC** = Area Under the ROC Curve, a threshold-independent discrimination metric.

**How it works:**  
Instead of using accuracy (which collapses the probability to a 0/1 decision), AUC measures how well the model **ranks** positive vs negative samples end-to-end. The gap between training AUC and validation AUC is a more sensitive and class-imbalance-robust measure of memorisation.

**Source:** Nasr et al. (2019), *"Comprehensive Privacy Analysis of Deep Learning: Passive and Active White-box Inference Attacks against Centralized and Federated Learning"*, IEEE S&P.

| | |
|:--|:--|
| ✅ **Advantage — Imbalance-robust** | AUC is independent of class distribution — critical for medical datasets where conditions like stroke or sepsis are rare |
| ✅ **Advantage — Threshold-free** | Captures overconfidence across the full probability range, not just above/below 0.5 |
| ✅ **Advantage — Zero extra cost** | `train_auc` is already computed by every client in `client.py` line 70 — it just needs to be sent to the server |
| ✅ **Advantage — Published standard** | Accepted by peer-reviewed work as a valid FL privacy proxy |
| ❌ **Minor Weakness** | Slightly less intuitive to explain than accuracy gap |

---

### 2.3 Shadow Model Attack *(Shokri et al. 2017)*

The **gold standard** for black-box MI attacks. Does not assume knowledge of model internals — only requires the ability to query the model and observe its output confidence scores.

**How it works — step by step:**

**Step 1 — Gather similar data:**  
The attacker collects a dataset from the same domain (e.g., other hospital records not in the training set).

**Step 2 — Train Shadow Models:**  
The attacker trains 10–50 "shadow models" — models with the same architecture as the real target, trained on subsets of their auxiliary dataset. Because they control which records are "in" or "out" of each shadow model's training set, they know the ground truth membership label.

```
Shadow Model 1: trained on records {1..1000}
  → Record 42: IN training  → confidence = [0.92, 0.08]  (label: MEMBER)
  → Record 999: NOT in training → confidence = [0.61, 0.39]  (label: NON-MEMBER)

Shadow Model 2: trained on records {500..2000}
  → ... (same process)
```

**Step 3 — Train an Attack Classifier:**  
Using confidence scores as features and MEMBER/NON-MEMBER as labels, train a binary attack classifier:
```
INPUT:  confidence vector from model output, e.g. [0.92, 0.08]
OUTPUT: MEMBER or NON-MEMBER
```

**Step 4 — Attack the real model:**  
Query the real federated model with any record. Feed the confidence vector into the attack classifier to determine membership.

```
Real Model query on Patient X → [0.89, 0.11]
Attack Classifier → MEMBER (Patient X was in training data)
```

**Source:** Shokri et al. (2017), *"Membership Inference Attacks Against Machine Learning Models"*, IEEE S&P.

| | |
|:--|:--|
| ✅ **Advantage — Black-box** | Only needs model output — no access to weights, gradients, or training data |
| ✅ **Advantage — Realistic threat model** | Matches what a real external attacker could do |
| ✅ **Advantage — Class-conditional** | Trains a separate attack classifier per output class — catches class-specific memorisation |
| ❌ **Weakness — Compute intensive** | Requires training 50+ shadow models, each equivalent to a full FL run |
| ❌ **Weakness — Auxiliary data required** | Attacker must have access to data from the same distribution |
| ❌ **Weakness — Not federated-native** | Designed for centralised models; harder to apply to a distributed FL server |
| ❌ **Infeasible here** | One FL run ≈ 15 minutes. 50 shadow models = **12+ hours minimum compute** |

---

### 2.4 LiRA — Likelihood Ratio Attack *(Carlini et al. 2022)*

The **current state-of-the-art** MI attack. Treats membership inference as a statistical hypothesis test, providing calibrated probabilities rather than binary guesses.

**How it works — step by step:**

**Step 1 — Train N shadow models under two conditions:**  
For each record `x` you want to test:
- Train `N/2` shadow models **with** `x` included in training
- Train `N/2` shadow models **without** `x` included in training

```
N = 128 (minimum recommended by Carlini et al.)
```

**Step 2 — Query all shadow models with `x`:**

```
Confidence scores when x WAS in training:    μ_in  ~ N(0.89, 0.03)
Confidence scores when x WAS NOT in training: μ_out ~ N(0.61, 0.05)
```

**Step 3 — Compute Likelihood Ratio:**

```
LR(x) = P(observed_score | x ∈ training) / P(observed_score | x ∉ training)
```

Using Gaussian fits to each distribution:
```
LR >> 1  →  x is likely a MEMBER       (high confidence)
LR ≈  1  →  cannot determine           (uncertain)
LR << 1  →  x is likely NOT a MEMBER   (high confidence)
```

**Source:** Carlini et al. (2022), *"Membership Inference Attacks From First Principles"*, IEEE S&P.

| | |
|:--|:--|
| ✅ **Advantage — Statistically rigorous** | Output is a calibrated probability, not just a binary guess |
| ✅ **Advantage — Per-record granularity** | Tests each record individually with its own uncertainty estimate |
| ✅ **Advantage — Current state-of-the-art** | Outperforms Shadow Model Attack consistently in benchmarks |
| ✅ **Advantage — Handles edge cases** | Correctly outputs "uncertain" when the model doesn't clearly separate members from non-members |
| ❌ **Weakness — Extreme compute** | Requires 64–256 shadow models **per record tested** |
| ❌ **Weakness — Not scalable** | For 10,000 records × 128 shadow models × 2 conditions = 2.56 million model evaluations |
| ❌ **Infeasible here** | Would require weeks of continuous GPU compute for a dataset of this size |

---

## 3. Decision Framework: Which Proxy to Use

```
Can you run weeks of GPU compute?
├── YES → Use LiRA (Carlini 2022) — state-of-the-art
└── NO
    Can you run days of GPU compute?
    ├── YES → Use Shadow Model Attack (Shokri 2017)
    └── NO (hours available)
        Is your dataset medically imbalanced?
        ├── YES → Use AUC Gap ✅ ← MedShare uses this
        └── NO  → Use Accuracy Gap (acceptable baseline)
```

---

## 4. MedShare Implementation Choice

**MedShare uses the AUC-Gap proxy** (`max(0, train_AUC - val_AUC)`).

### Why this is the correct choice for this system:

1. **Zero overhead:** `train_auc` is already computed on every hospital client in `client.py` during the `fit()` phase — upgrading to AUC-Gap requires no additional training or inference.

2. **Medical dataset suitability:** The `admin_category` dataset uses multi-class condition prediction (Emergency / Infectious / Chronic / Specialised), and the `admin_billing` dataset uses binary high/low bill prediction. Both have class imbalance, making accuracy a poor discrimination metric. AUC is the standard evaluation metric in clinical ML for exactly this reason.

3. **Scientifically defensible:** Nasr et al. (2019) validated AUC-based MI proxies as a legitimate measure of membership leakage in federated learning settings specifically.

4. **Differential Privacy interaction is correctly captured:** When DP noise (σ) is applied, it should reduce both `train_AUC` and `val_AUC`, but the *gap* between them narrows as noise increases, proving that DP is reducing per-sample memorisation. The AUC gap detects this more sensitively than the accuracy gap.

### Implementation location:
- **`medshare/client.py`** — computes `train_auc` and sends it to the server as a metric
- **`medshare/strategy.py`** — aggregates `train_auc` across hospitals and computes `MI_score = max(0, agg_train_auc - agg_val_auc)`

---

## 5. Limitations and Honest Assessment

All proxy-based MI metrics, including the AUC Gap, share a **common limitation**: they measure **correlation with** membership inference risk, not a **direct attack success rate**. A proxy score of 0 does not guarantee zero leakage — it means leakage is not detectable via this particular measure.

For a production medical federated learning system, the recommended approach is:
1. Use the AUC-Gap proxy as an **ongoing monitoring metric** (computationally free)
2. Run a Shadow Model Attack periodically on a **sample of records** (every 6 months)
3. Report both metrics in privacy audits submitted to regulators (e.g., ICO in the UK, HHS in the US)

For the purposes of this academic project, the AUC-Gap proxy provides a **legitimate, well-cited, computationally feasible** measure of whether Differential Privacy is successfully reducing membership leakage across the federated hospital network.

---

## 6. References

1. Yeom, S. et al. (2018). *Privacy Risk in Machine Learning: Analyzing the Connection to Overfitting.* IEEE Computer Security Foundations Symposium (CSF).

2. Shokri, R. et al. (2017). *Membership Inference Attacks Against Machine Learning Models.* IEEE Symposium on Security and Privacy (S&P).

3. Nasr, M. et al. (2019). *Comprehensive Privacy Analysis of Deep Learning: Passive and Active White-box Inference Attacks Against Centralized and Federated Learning.* IEEE Symposium on Security and Privacy (S&P).

4. Carlini, N. et al. (2022). *Membership Inference Attacks From First Principles.* IEEE Symposium on Security and Privacy (S&P).
