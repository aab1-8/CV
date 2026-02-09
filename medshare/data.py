import os, requests, zipfile, io, pandas as pd, numpy as np, torch
from torch.utils.data import DataLoader, TensorDataset

def fetch_support2():
    try:
        from ucimlrepo import fetch_ucirepo
        return fetch_ucirepo(id=880).data.original
    except:
        r = requests.get("https://archive.ics.uci.edu/static/public/880/support2.zip")
        with zipfile.ZipFile(io.BytesIO(r.content)) as z: return pd.read_csv(z.open('support2.csv'))

def fetch_thyroid():
    from ucimlrepo import fetch_ucirepo
    # Thyroid Disease (ID 102)
    return fetch_ucirepo(id=102).data.original

def fetch_diabetes_hospitals():
    from ucimlrepo import fetch_ucirepo
    # Diabetes 130-Hospitals (ID 296)
    return fetch_ucirepo(id=296).data.original

def fetch_cdc_diabetes():
    from ucimlrepo import fetch_ucirepo
    # CDC Diabetes Health Indicators (ID 891)
    return fetch_ucirepo(id=891).data.original

def fetch_maternal_health():
    from ucimlrepo import fetch_ucirepo
    # Maternal Health Risk (ID 863)
    return fetch_ucirepo(id=863).data.original

def fetch_hospital_admin():
    import kagglehub
    path = kagglehub.dataset_download("devildyno/hospital-patient-records-jan-2021-july-2024")
    # Finding the csv file in the downloaded path
    for file in os.listdir(path):
        if file.endswith(".csv"):
            return pd.read_csv(os.path.join(path, file))
    raise FileNotFoundError("CSV not found in hospital admin dataset")

def load_tabular_data(config):
    source, target = config.get("DATA_SOURCE", "support2"), config["TARGET_COLUMN"]
    if source == "support2": df = fetch_support2()
    elif source == "thyroid": df = fetch_thyroid()
    elif source == "diabetes_hospital": df = fetch_diabetes_hospitals()
    elif source == "cdc_diabetes": df = fetch_cdc_diabetes()
    elif source == "maternal_health": df = fetch_maternal_health()
    elif source == "hospital_admin":
        df = fetch_hospital_admin()
        # Custom labeling: If predicting bill, create a median-split binary target
        if target.lower() == "high_bill":
            median = df['Bill Amount'].median()
            df['high_bill'] = (df['Bill Amount'] > median).astype(int)
        # Simplified multi-class: Group into 4 clear care-type categories
        elif target.lower() == "condition_category":
            condition_map = {
                # Emergency/Trauma (Immediate intervention needed)
                'Fracture': 'Emergency', 'Sprain': 'Emergency', 'Burns': 'Emergency',
                'Stroke': 'Emergency', 'Heart Disease': 'Emergency',
                # Infectious (Contagious, requires isolation protocols)
                'COVID-19': 'Infectious', 'Pneumonia': 'Infectious', 'Influenza': 'Infectious',
                'Common Cold': 'Infectious', 'Bronchitis': 'Infectious', 'Sinusitis': 'Infectious',
                'Urinary Tract Infection': 'Infectious', 'Gastroenteritis': 'Infectious',
                'Skin Infection': 'Infectious',
                # Chronic Care (Long-term management, outpatient focus)
                'Diabetes': 'Chronic', 'Hypertension': 'Chronic', 'Asthma': 'Chronic',
                'Chronic Obstructive Pulmonary Disease': 'Chronic', 'Chronic Kidney Disease': 'Chronic',
                'Arthritis': 'Chronic', 'Allergies': 'Chronic',
                # Specialized (Requires specialist departments)
                "Alzheimer's Disease": 'Specialized', "Parkinson's Disease": 'Specialized',
                'Epilepsy': 'Specialized', 'Migraine': 'Specialized', 
                'Multiple Sclerosis': 'Specialized', 'Depression': 'Specialized',
                'Anxiety': 'Specialized', 'Cancer': 'Specialized'
            }
            df['condition_category'] = df['Medical Condition'].map(condition_map).fillna('Other')
    elif source == "stroke_prediction":
        import kagglehub
        df = pd.read_csv(os.path.join(kagglehub.dataset_download("fedesoriano/stroke-prediction-dataset"), "healthcare-dataset-stroke-data.csv"))
    else: df = pd.read_csv(source)
    
    # Normalize column names to lowercase for consistency
    df.columns = df.columns.str.lower()
    target = target.lower()
    
    if config.get("apply_rebalancing"):
        if target not in df.columns:
            print(f"[Warning] Target column '{target}' not found. Available columns: {list(df.columns)}")
        else:
            # Apply SMOTE for better synthetic minority oversampling
            try:
                from imblearn.over_sampling import SMOTE
                
                # Separate features and target before preprocessing
                y_raw = df[target]
                X_raw = df.drop(columns=[target])
                
                # Only apply SMOTE if it's a binary or small multi-class problem
                min_samples = y_raw.value_counts().min()
                if y_raw.nunique() <= 5 and min_samples > 1:
                    # Encode categorical features temporarily for SMOTE
                    cat_cols_temp = X_raw.select_dtypes(include=['object', 'category']).columns
                    X_encoded = pd.get_dummies(X_raw, columns=cat_cols_temp, drop_first=True)
                    
                    # Fill NaN values before SMOTE (SMOTE doesn't accept NaN)
                    X_encoded = X_encoded.fillna(X_encoded.median(numeric_only=True)).fillna(0)
                    
                    # Apply SMOTE
                    k = min(5, min_samples - 1)
                    smote = SMOTE(random_state=42, k_neighbors=k)
                    X_resampled, y_resampled = smote.fit_resample(X_encoded, y_raw)
                    
                    # Reconstruct dataframe
                    df = pd.DataFrame(X_resampled, columns=X_encoded.columns)
                    df[target] = y_resampled
                    print(f"[Data] Applied SMOTE (k={k}): {len(y_raw)} → {len(y_resampled)} samples")
                else:
                    if min_samples <= 1:
                        print(f"[Data] Skipping SMOTE (minority class has only {min_samples} sample). Falling back.")
                        raise ValueError("Insufficient samples for SMOTE")
                    print(f"[Data] Skipping SMOTE (too many classes: {y_raw.nunique()})")
            except ImportError:
                print("[Warning] imbalanced-learn not installed. Falling back to naive oversampling.")
                min_c = df[target].value_counts().idxmin()
                df = pd.concat([df, df[df[target] == min_c]] * 3).sample(frac=1).reset_index(drop=True)
            except Exception as e:
                print(f"[Warning] SMOTE failed ({e}). Using naive oversampling.")
                min_c = df[target].value_counts().idxmin()
                df = pd.concat([df, df[df[target] == min_c]] * 3).sample(frac=1).reset_index(drop=True)

    if config.get("sample_size") and len(df) > config["sample_size"]:
        df = df.sample(n=config["sample_size"], random_state=42).reset_index(drop=True)

    drop_cols = [c.lower() for c in config.get("DROP_COLUMNS", [])]
    df = df.drop(columns=drop_cols, errors='ignore').fillna(df.median(numeric_only=True))
    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    partition_col = config.get("PARTITION_COLUMN", "").lower() if config.get("PARTITION_COLUMN") else None
    
    if partition_col and partition_col in cat_cols:
        parts = df[partition_col].fillna("Unknown")
        df = df.drop(columns=[partition_col])
    else:
        parts = pd.Series([f"Hospital_{i+1}" for i in np.random.randint(0, config.get("NUM_PARTITIONS", 5), len(df))], index=df.index)
    
    # Label encode target if it is categorical
    if df[target].dtype == 'object' or df[target].dtype.name == 'category':
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        df[target] = le.fit_transform(df[target].astype(str))
        print(f"[Data] Encoded categorical target '{target}' into {len(le.classes_)} classes.")

    # One-hot encode categorical features
    cols_to_encode = [c for c in cat_cols if c not in [partition_col, target]]
    if cols_to_encode:
        df = pd.get_dummies(df, columns=cols_to_encode, drop_first=True)

    X, y = df.drop(columns=[target]).astype(np.float32), df[target].astype(np.float32)
    return X, np.asarray(y), parts, X.shape[1], (1 if y.nunique() <= 2 else int(y.nunique()))

def create_dataloaders(X, y, batch_size=1024):
    return DataLoader(TensorDataset(torch.tensor(X.values if hasattr(X, 'values') else X).float(), torch.tensor(y).float()), batch_size=batch_size, shuffle=True)
