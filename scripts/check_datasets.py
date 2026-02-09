from ucimlrepo import fetch_ucirepo
import pandas as pd

def check_dataset(id, name):
    print(f"\n--- Checking {name} (ID: {id}) ---")
    try:
        ds = fetch_ucirepo(id=id)
        df = ds.data.original
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        target = ds.data.target
        if target is not None:
             print(f"Target column(s): {list(target.columns)}")
             for col in target.columns:
                 print(f"Unique values in {col}: {df[col].nunique()}")
                 print(df[col].value_counts().head())
        else:
            print("No target metadata found.")
    except Exception as e:
        print(f"Error: {e}")

# check_dataset(880, "SUPPORT2")
check_dataset(891, "CDC Diabetes")
check_dataset(296, "Diabetes 130-Hospitals")
# check_dataset(102, "Thyroid")
