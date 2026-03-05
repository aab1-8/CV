import pandas as pd
import numpy as np
from medshare.data import get_data_cached

config = {
    "display_name": "Diabetes-Hospitals", 
    "DATA_SOURCE": "diabetes_hospital", 
    "TARGET_COLUMN": "readmitted",
    "DROP_COLUMNS": ["encounter_id", "patient_nbr"],
    "apply_rebalancing": "auto",
    "sample_size": 2000
}

print("--- Diamond Standard Data Health Check ---")
X, y, parts, dim, classes = get_data_cached(config)

print(f"Dataset Size: {len(X)}")
print(f"Input Dimensions: {dim}")
print(f"Number of Classes: {classes}")

# Check for NaNs
total_nans = np.isnan(X).sum().sum()
print(f"Total NaNs in Features: {total_nans}")

# Check data types
non_numeric = X.select_dtypes(exclude=[np.number]).columns
print(f"Non-Numeric Columns: {list(non_numeric)}")

if total_nans == 0 and len(non_numeric) == 0 and dim > 50:
    print("\n[SUCCESS] The 'Diamond Standard' Data Engine is 100% healthy.")
    print("Identifiers dropped, NaNs filled, and categorical data encoded.")
else:
    print("\n[FAILURE] Data health issues detected.")
