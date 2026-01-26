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
| `stroke_prediction` | Stroke Prediction (Real CSV) | **Binary** |
| `support2` | SUPPORT2 Clinical Study | **Binary** |
| `cdc_diabetes` | CDC Diabetes Indicators | **Binary** |
| `cdc_diabetes_balanced` | CDC Diabetes (Balanced) | **Binary** |
| `diabetes_hospital_binary` | Diabetes 130-US Hospitals | **Binary** |
| `diabetic_retinopathy` | Diabetic Retinopathy Debrecen | **Binary** |
| `cdc_diabetes_multiclass` | CDC Diabetes Multi-class | **Multi-class** |
| `diabetes_hospital` | Diabetes 130-US Hospitals | **Multi-class** |
| `thyroid` | Thyroid Disease Dataset | **Multi-class** |

---

## 2. Modifying FL Settings (DP, Security, Epochs)

### Method A: Command-Line (Dynamic)
Works for both Local and Colab (via the `!python` command).
- **Epochs**: `--epochs 5`
- **DP Noise**: `--experiment dp --dp_noise 2.0`
- **Skip Baseline**: `--skip_baseline`

### Method B: Global File Edits (Persistent)
Edit [federated_survival.py](../federated_survival.py) directly. This is the most reliable way to change defaults.

- **Enable/Disable Features**: Search for `GLOBAL CONFIGURATION` (approx. Line 51).
  - `ENABLE_DP = True/False`
  - `ENABLE_BLOCKCHAIN = True/False`
- **Defense Mechanism**: Change `DEFENSE_TYPE` to `"trimmed_avg"`, `"fedmedian"`, or `"krum"`.
- **Attack Simulation**: Toggle `ENABLE_ATTACK` and set `MALICIOUS_CLIENTS_RATIO`.

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
Enable automatic saving of the best global model weights:
- Use the `--save_best` flag.
- The model is saved to `test/best_model.pth` (or project root) as soon as a new accuracy record is hit.

Example:
```bash
python federated_survival.py --save_best --rounds 20
```

## 5. Adding New Datasets
To add a custom CSV:
1. Place the CSV in the project root.
2. Open `federated_survival.py`.
3. Add a new entry to the `DATASET_PRESETS` dictionary (approx. Line 84) with the filename and target column name.
