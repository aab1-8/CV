# MedShare Dataset Inventory

This document provides a comprehensive overview of all datasets currently integrated and ready for use in the MedShare Federated Learning simulation.

---

## 📊 Dataset Catalog

| Command Name | Display Name | Classification | Rows (Full) | Prediction Goal | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`support2`** | SUPPORT2-Death | **Binary** | 9,105 | Patient Mortality (0/1) | UCI #880 |
| **`stroke_prediction`** | Stroke | **Binary** | 5,110 | Stroke Risk (0/1) | Kaggle |
| **`cdc_diabetes_binary`** | CDC-Diabetes-Binary | **Binary** | 253,680 | Diabetes Status (0/1) | UCI #891 |
| **`cdc_diabetes_012`** | CDC-Diabetes-012 | **Multi-class** | 253,680 | Status (None/Pre/Diabetic) | UCI #891 |
| **`maternal_health`** | Maternal-Health | **Multi-class** | 1,013 | Risk (low, mid, high) | UCI #863 |
| **`admin_billing`** | Admin-Billing | **Binary** | 1,000 | High vs Low Bill Amount | Kaggle |
| **`admin_category`** | Admin-Category | **Multi-class (4)** | 1,000 | Care Type (Emergency/Infectious/Chronic/Specialized) | Kaggle |
| **`diabetes_hospital`** | Diabetes-Hospitals | **Multi-class** | 101,766 | Readmission (<30, >30, NO) | UCI #296 |
| **`thyroid`** | Thyroid | **Multi-class** | 7,200 | Hypo / Hyper / Normal | UCI #102 |
| **`support2_disease`** | SUPPORT2-Disease | **Multi-class** | 9,105 | Disease Category | UCI #880 |

---

## 📊 Class Distribution Splits

This section details the **raw, unbalanced population counts** for each dataset before any simulation preprocessing (like SMOTE or sampling) is applied.

| Dataset | Total Rows | Raw Class Split (Counts) |
| :--- | :--- | :--- |
| **SUPPORT2-Death** | 9,105 | **Dead:** 6,201 | **Alive:** 2,904 |
| **Stroke** | 5,110 | **No Stroke:** 4,861 | **Stroke:** 249 |
| **CDC-Diabetes-Binary** | 253,680 | **Healthy:** 218,334 | **Diabetic:** 35,346 |
| **CDC-Diabetes-012** | 253,680 | **Healthy:** 213,703 | **Diabetic:** 35,346 | **Pre-diabetic:** 4,631 |
| **Maternal-Health** | 1,014 | **Low Risk:** 406 | **Mid Risk:** 336 | **High Risk:** 272 |
| **Admin-Billing** | 1,000 | **Low Bill:** 500 (50.0%) | **High Bill:** 500 (50.0%) |
| **Admin-Category** | 1,000 | **Infectious:** 313 | **Specialized:** 287 | **Chronic:** 228 | **Emergency:** 172 |
| **Diabetes-Hospitals** | 101,766 | **NO:** 54,864 | **>30 Days:** 35,545 | **<30 Days:** 11,357 |
| **Thyroid** | 7,200 | **Negative:** 6,771 | **Hypo/Hyper:** 429 |
| **SUPPORT2-Disease** | 9,105 | **Cancer:** 3,515 | **Sepsis:** 3,515 | **CHF:** 1,387 | **COPD:** 967 | **Other:** 2,721 |

---

## 🔍 Detailed Breakdown

### 1. SUPPORT2 (Study to Understand Prognoses Preferences Outcomes and Risks of Treatment)
*   **Role**: Primary benchmarking dataset.
*   **Binary Variant**: Predicts if a patient will die during the study period.
*   **Multi-class Variant**: Predicts which "disease group" the patient belongs to (e.g., Cancer, Coma, CHF, Lung Disease).

### 2. CDC Diabetes (BRFSS 2015)
*   **Role**: Largest available dataset for stress-testing scalability.
*   **Binary Variant**: A cleaned version focusing strictly on Diabetic vs. Non-Diabetic.
*   **Multi-class Variant (`012`)**: Includes a third category for **Pre-diabetic** patients.
*   **Size**: Totaling **253,680** records.

### 3. Diabetes 130-US Hospitals (1999-2008)
*   **Role**: High-complexity dataset for robustness testing.
*   **Features**: Includes over 50 attributes (lab results, medications, demographics).
*   **Target**: Categorizes readmission into three types: No readmission, readmission within 30 days, or readmission after 30 days.

### 4. Stroke Prediction Dataset
*   **Role**: Imbalanced data testing.
*   **Target**: Predicts stroke risk based on clinical factors like hypertension, age, and heart disease.
*   **Note**: This dataset uses **oversampling** (and optionally SMOTE) to handle the rarity of stroke events.

### 5. Thyroid Disease
*   **Role**: Classical medical classification.
*   **Target**: Identifies thyroid dysfunction state (hypothyroid, hyperthyroid, or normal).

---

## 🚀 Usage Guide

To use any of these datasets in a simulation, use the `--dataset` flag followed by the **Command Name**:

```powershell
# Example: Running the Multi-class CDC Diabetes simulation
python federated_survival.py --dataset cdc_diabetes_012 --rounds 3 --sample_size 2000

# Example: Running the Hospital Readmission simulation
python federated_survival.py --dataset diabetes_hospital --rounds 5
```

**Recommended Practices:**
*   For **Binary** tasks: Use standard AUC-ROC for evaluation.
*   For **Multi-class** tasks: The system automatically uses CrossEntropyLoss and One-vs-Rest (OvR) AUC calculation.
*   For **Large Datasets** (CDC & Hospitals): Always specify `--sample_size` to prevent excessive RAM usage on local machines.
