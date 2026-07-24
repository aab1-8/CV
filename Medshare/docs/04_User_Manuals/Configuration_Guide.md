# MedShare Configuration Guide: Datasets & Settings

This document explains how to customize the federated learning environment for both Local Windows and Google Colab.

## 1. Choosing a Dataset

### Local Windows
Use the `--dataset` command-line argument when running the script.
- **Run Default**: `python federated_survival.py` (Currently sets to `stroke_prediction`)
- **Switch Dataset**: `python federated_survival.py --dataset support2`

### Google Colab
Modify the execution cell in the **Infrastructure & Evaluation** section of the notebook.
- **Change Command**: Update the line starting with `!python` to include the dataset flag:
  ```python
  !python federated_survival.py --experiment $cmd --dataset support2 --epochs 3
  ```

### Available Datasets
| Key | Dataset | Type |
| :--- | :--- | :--- |
| `support2` | SUPPORT2 Clinical Study | **Binary** |
| `stroke_prediction` | Stroke Prediction (Real CSV) | **Binary** |
| `cdc_diabetes_binary` | CDC Diabetes Indicators | **Binary** |
| `thyroid` | Thyroid Disease Dataset | **Multi-class** |
| `cdc_diabetes_012` | CDC Diabetes Multi-class | **Multi-class** |
| `diabetes_hospital` | Diabetes 130-US Hospitals | **Multi-class** |
| `maternal_health` | Maternal Health Risk | **Multi-class** |
| `admin_billing` | Admin-Billing-Risk | **Binary** |
| `admin_category` | Admin-Category | **Multi-class** |
| `support2_disease` | SUPPORT2-Disease | **Multi-class** |
| `diabetic_retinopathy` | Diabetic Retinopathy Debrecen | **Binary** |
---

## 2. Modifying FL Settings (DP, Security, Epochs)

### Method A: Command-Line (Dynamic)
Works for both Local and Colab (via the `!python` command).
- **Epochs**: `--epochs 20`
- **FL Rounds**: `--rounds 100`
- **DP Noise**: `--experiment dp --sigma 1.0 --enable_dp True`
- **Blockchain**: `--enable_blockchain True`

### Method B: Code Customization (Persistent)
Edit [federated_survival.py](../../federated_survival.py) directly to change experiment logic or defaults.

- **Adaptive Calibration**: Settings are automatically calculated based on dataset size in `get_adaptive_experiment_config`.
- **Strategy Logic**: The `AnomalyMonitoringStrategy` inside the script controls how updates are merged (FedAvg vs Robust-MAD).
- **Network Architecture**: Modify the `SurvivalMLP` class in `medshare/models.py`.

> [!IMPORTANT]
> **Colab Users**: Since your notebook is synced with Google Drive, saving changes to the `.py` file in your local editor will automatically update the code used by Colab on the next cell run.

---

---

## 3. Data Heterogeneity
You can simulate non-uniform data distributions across hospitals using the `--heterogeneity` flag:
- `none` (Default): Data is distributed uniformly (IID).
- `label`: Pathological skew; hospitals receive data sorted by the target outcome.
- `feature`: Attribute skew; hospitals receive data sorted by the primary numeric feature.

Example:
```bash
python federated_survival.py --heterogeneity label --dataset stroke_prediction
```

### 4. Model Checkpointing
The system automatically saves the best global model weights during evaluation:
- The model is saved to `test/best_model.pth`.
- This happens as soon as a new accuracy record is hit during the evaluation phase of any round.

Example:
```bash
python federated_survival.py --rounds 20
```

## 5. Adding New Datasets
To add a custom CSV:
1. Place the CSV in the project root.
2. Open `federated_survival.py`.
3. Add a new entry to the `DATASET_PRESETS` dictionary (approx. Line 84) with the filename and target column name.
