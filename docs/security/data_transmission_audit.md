# Audit: Federated Data Transmission Strategy

This document provides a technical audit of the information transmitted between hospitals (clients) and the central server in the MedShare project.

## 1. Transmission Flow
The project strictly follows the "Principle of Local Processing." No raw patient data is ever staged, cached, or transmitted.

### A. Hospital to Blockchain (The "Commitment")
Before communicating with the FL server, the hospital interacts with the Ethereum smart contract (`CommitmentRegistry.sol`).
- **Data Sent**: `SHA-256 Hash` of the model weights.
- **Purpose**: Creates an immutable audit trail. The server cannot "tamper" with the hospital's contribution without invalidating the hash.
- **Trigger**: `medshare/client.py` -> `bcm.post_commitment()`

### B. Hospital to Central FL Server (The "Gradient/Weight Update")
The hospital sends a serialized package containing:
1. **Model Weights**: A list of `NumPy arrays` representing the trained state of the neural network layers (`SurvivalMLP`).
2. **Cardinality**: The integer count of patient records used for training (e.g., `num_examples=1014`). This is used for volume-weighted averaging.
3. **Privacy Metadata**: 
   - `privacy_spent` ($\epsilon$): The privacy budget consumed (calculated via Opacus RDP).
   - `loss`: local training convergence metric.
4. **Validation Metrics**: 
   - `accuracy` & `auc`: Local performance proof.
5. **Operational Metadata**:
   - `gas_used`: Transaction cost tracking.
   - `client_id` & `node_name`: For identification and reputation management.
   - `is_malicious`: Used during STRESS TESTS ONLY to identify attack sources.

## 2. Server Processing (Aggregation)
The server receives these packages and performs the following:
1. **Validation**: The `AnomalyMonitoringStrategy` calculates the **L2 Norm** of the weights.
2. **Filtering**: If a hospital's update is a statistical outlier (Norm > Threshold), it is dropped to prevent "Model Poisoning."
3. **Aggregation**: Remaining weights are combined using **Federated Averaging (FedAvg)**, proportioned by the `num_examples` sent by each hospital.

## 3. Data Safety Summary
| Information Type | Shared? | Format | Privacy Protection |
| :--- | :--- | :--- | :--- |
| Raw Medical Records | **NO** | N/A | Localized Storage |
| Patient Identifiers | **NO** | N/A | Never processed by ML engine |
| Model Weights | **YES** | NumPy Arrays | Differential Privacy (Gaussian Noise) |
| Performance Metrics | **YES** | Float/Int | Summarized Averages |

**Audit Status**: VERIFIED. The codebase strictly enforces these boundaries in `medshare/client.py` and `medshare/strategy.py`.
