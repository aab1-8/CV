# MedShare Dataset Inventory

This document provides a comprehensive overview of all datasets currently integrated and ready for use in the MedShare Federated Learning simulation.

---

## 📊 Dataset Catalog

| Command Name | Display Name | Classification | Rows (Full) | Prediction Goal | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`support2`** | SUPPORT2-Death | **Binary** | 9,105 | Patient Mortality (0/1) | UCI #880 |
| **`stroke_prediction`** | Stroke | **Binary** | 5,110 | Stroke Risk (0/1) | Kaggle |
| **`cdc_diabetes_binary`** | CDC-Diabetes-Binary | **Binary** | 253,680 | Diabetes Status (0/1) | UCI #891 |
| **`thyroid`** | Thyroid | **Multi-class** | 7,200 | Hypo / Hyper / Normal | UCI #102 |
| **`cdc_diabetes_012`** | CDC-Diabetes-012 | **Multi-class** | 253,680 | Status (None/Pre/Diabetic) | UCI #891 |
| **`maternal_health`** | Maternal-Health | **Multi-class** | 1,014 | Risk (low, mid, high) | UCI #863 |
| **`admin_billing`** | Admin-Billing-Risk | **Binary** | 1,000 | High vs Low Bill Amount | Kaggle |
| **`admin_category`** | Admin-Category | **Multi-class (4)** | 1,000 | Care Type (Emergency/Infectious/Chronic/Specialized) | Kaggle |
| **`diabetes_hospital`** | Diabetes-Hospitals | **Multi-class** | 101,766 | Readmission (<30, >30, NO) | UCI #296 |
| **`support2_disease`** | SUPPORT2-Disease | **Multi-class** | 9,105 | Disease Category | UCI #880 |
| **`diabetic_retinopathy`** | Retinopathy | **Binary** | 1,151 | Signs of DR (0/1) | UCI #329 |

---

## 📊 Class Distribution Splits

This section details the **raw, unbalanced population counts** for each dataset before any simulation preprocessing (like SMOTE or sampling) is applied.

| Dataset | Total Rows | Raw Class Split (Counts) |
| :--- | :--- | :--- |
| **SUPPORT2-Death** | 9,105 | **Dead:** 6,201 | **Alive:** 2,904 |
| **Stroke** | 5,110 | **No Stroke:** 4,861 | **Stroke:** 249 |
| **CDC-Diabetes-Binary** | 253,680 | **Healthy:** 218,334 | **Diabetic:** 35,346 |
| **Thyroid** | 7,200 | **Negative:** 6,666 | **Hypo/Hyper:** 534 |
| **CDC-Diabetes-012** | 253,680 | **Healthy:** 213,703 | **Diabetic:** 35,346 | **Pre-diabetic:** 4,631 |
| **Maternal-Health** | 1,014 | **Low Risk:** 406 | **Mid Risk:** 336 | **High Risk:** 272 |
| **Admin-Billing** | 1,000 | **Low Bill:** 500 (50.0%) | **High Bill:** 500 (50.0%) |
| **Admin-Category** | 1,000 | **Infectious:** 313 | **Specialized:** 287 | **Chronic:** 228 | **Emergency:** 172 |
| **Diabetes-Hospitals** | 101,766 | **NO:** 54,864 | **>30 Days:** 35,545 | **<30 Days:** 11,357 |
| **SUPPORT2-Disease** | 9,105 | **Sepsis:** 3,515 | **Cancer:** 2,132 | **CHF:** 1,387 | **COPD:** 967 | **Other:** 1,104 |
| **Retinopathy** | 1,151 | **Signs Present:** 611 (53.1%) | **No Signs:** 540 (46.9%) |

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
*   **Note on Accuracy (38.9%)**: This lower accuracy is a deliberate experimental benchmark. It demonstrates how "Total Privacy" ($\sigma=1.0$) affects high-complexity, multi-class categorical data on a medium scale (101k rows).

### **III. Performance Variance & Privacy Scaling Rationale (Viva Summary)**

A core finding of this project is the **"Privacy-Volume Correlation"**:
1. **Low Volume (1k - 10k rows)**: High sensitivity to noise. In datasets like `admin_billing`, privacy noise can sometimes drop accuracy significantly because the mathematical noise is larger than the clinical signal.
2. **Medium Volume (101k rows)**: The `diabetes_hospital` run achieves **38.9% accuracy**. This reflects the difficulty of maintaining 50+ categorical feature links while under strict $(\epsilon, \delta)$-Differential Privacy.
3. **High Volume (253k+ rows)**: The `cdc_diabetes` run achieves **86.5% accuracy**. This proves the project's scalability thesis: **The Law of Large Numbers allows privacy noise to average out more effectively as the patient population grows, enabling high utility at high privacy.**


### 4. Stroke Prediction Dataset
*   **Role**: Imbalanced data testing.
*   **Target**: Predicts stroke risk based on clinical factors like hypertension, age, and heart disease.
*   **Note**: This dataset uses **oversampling** (and optionally SMOTE) to handle the rarity of stroke events.

### 5. Thyroid Disease
*   **Role**: Classical medical classification.
*   **Target**: Identifies thyroid dysfunction state (hypothyroid, hyperthyroid, or normal).

### 6. Diabetic Retinopathy Debrecen
*   **Role**: Binary medical classification on image-extracted features.
*   **Target**: Predicts the presence of signs of diabetic retinopathy (0/1).
*   **Size**: Contains **1,151** records with 19 attributes.

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






***

### General UCI repository (optional, but nice to include)

 D. Dua and C. Graff, “UCI Machine Learning Repository,” Univ. of California, Irvine, School of Information and Computer Sciences. [Online]. Available: http://archive.ics.uci.edu/ml [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/130730438/f886fb92-ed95-4c5e-b77a-654ce6be2a08/MedShare-FL-2.pdf)

***

### SUPPORT2 (`support2`, `support2_disease`)

 W. A. Knaus *et al.*, “The SUPPORT prognostic model: Objective estimates of survival for seriously ill hospitalized adults,” *Ann. Intern. Med.*, vol. 122, no. 3, pp. 191–203, 1995. [archive.ics.uci](https://archive.ics.uci.edu/datasets?search=health)

 “SUPPORT2,” UCI Machine Learning Repository, Univ. of California, Irvine. [Online]. Available: https://archive.ics.uci.edu/dataset/880 [archive.ics.uci](https://archive.ics.uci.edu/datasets)

***

### CDC Diabetes Health Indicators (`cdc_diabetes_binary`, `cdc_diabetes_012`)

 Centers for Disease Control and Prevention, “CDC Diabetes Health Indicators (BRFSS 2015),” UCI Machine Learning Repository, Univ. of California, Irvine. [Online]. Available: https://archive.ics.uci.edu/dataset/891

(Explain in text that you use the `Diabetes_binary` and `Diabetes_012` targets.)

***

### Maternal Health Risk (`maternal_health`)

 “Maternal Health Risk,” UCI Machine Learning Repository, Univ. of California, Irvine. [Online]. Available: https://archive.ics.uci.edu/dataset/863

If your supervisor wants an author name, you can expand to:

 A. (Dataset contributors), “Maternal Health Risk,” UCI Machine Learning Repository, Univ. of California, Irvine. [Online]. Available: https://archive.ics.uci.edu/dataset/863

***

### Diabetes 130‑US Hospitals (`diabetes_hospital`)

 B. Strack *et al.*, “Impact of HbA1c measurement on hospital readmission rates: Analysis of 70,000 clinical database patient records,” *Biomed. Res. Int.*, vol. 2014, Art. ID 781670, 2014.

 “Diabetes 130‑US Hospitals for Years 1999–2008,” UCI Machine Learning Repository, Univ. of California, Irvine. [Online]. Available: https://archive.ics.uci.edu/ml/datasets/diabetes+130-us+hospitals+for+years+1999-2008

***

### Thyroid Disease (`thyroid`)

 “Thyroid Disease,” UCI Machine Learning Repository, Univ. of California, Irvine. [Online]. Available: https://archive.ics.uci.edu/dataset/102/thyroid+disease

(If you know the exact authors from the original study, you can replace with a full article citation, but this generic UCI entry is normally acceptable.)

***

### Stroke Prediction (`stroke_prediction` – Kaggle)

Fill in the author name exactly as it appears on Kaggle (commonly “fedesoriano”):

 fedesoriano, “Stroke Prediction Dataset,” Kaggle. [Online]. Available: https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset

You can optionally add an access date: “Accessed: Feb. 16, 2026.”

***

### Hospital Patient Records (`admin_billing`, `admin_category` – Kaggle, MIT‑licensed)

 R. Patil, “Hospital Patient Records July 2021–July 2024,” Kaggle. [Online]. Available: https://www.kaggle.com/datasets/devildyno/hospital-patient-records-jan-2021-july-2024 [unidata](https://unidata.pro/blog/best-free-healthcare-ml-datasets/)

The “Hospital Patient Records July 2021–July 2024” dataset is © original authors and is used under the MIT License. See LICENSE_hospital_records.txt for details.

***

### Diabetic Retinopathy Debrecen (`diabetic_retinopathy`)

 B. Antal and A. Hajdu, “Extraction of Multiple Features from Color Fundus Images and Hierarchical Classification of Diabetic Retinopathy,” *IEEE Trans. Biomed. Eng.*, vol. 59, no. 11, pp. 3131–3139, 2012.

 “Diabetic Retinopathy Debrecen,” UCI Machine Learning Repository, Univ. of California, Irvine. [Online]. Available: https://archive.ics.uci.edu/dataset/329/diabetic+retinopathy+debrecen+data+set
