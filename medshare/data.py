import os, requests, zipfile, io, pandas as pd, numpy as np, torch
from torch.utils.data import DataLoader, TensorDataset

def fetch_support2():
    try:
        from ucimlrepo import fetch_ucirepo
        repo = fetch_ucirepo(id=880)
        return pd.concat([repo.data.features, repo.data.targets], axis=1)
    except:
        r = requests.get("https://archive.ics.uci.edu/static/public/880/support2.zip")
        with zipfile.ZipFile(io.BytesIO(r.content)) as z: return pd.read_csv(z.open('support2.csv'))

def fetch_thyroid():
    import pandas as pd, ssl, urllib.request, io

    cols = [
        "age", "sex", "on_thyroxine", "query_on_thyroxine", "on_antithyroid_medication",
        "sick", "pregnant", "thyroid_surgery", "i131_treatment", "query_hypothyroid",
        "query_hyperthyroid", "lithium", "goitre", "tumor", "hypopituitary", "psych",
        "tsh", "t3", "tt4", "t4u", "fti", "target"
    ]

    # Method 1: ucimlrepo (preferred, no SSL issues)
    try:
        from ucimlrepo import fetch_ucirepo
        print("[Data] Fetching Thyroid via ucimlrepo...")
        repo = fetch_ucirepo(id=102)
        X = repo.data.features
        y = repo.data.targets
        df = pd.concat([X.reset_index(drop=True), y.reset_index(drop=True)], axis=1)
        # Standardize column names to match the definitive schema
        df.columns = cols 
        print(f"[Data] Thyroid loaded via ucimlrepo: {len(df)} rows, {len(df.columns)} cols")
        return df
    except Exception as e:
        print(f"[Data] ucimlrepo failed ({e}), falling back to direct download...")

    # Method 2: Direct URL with SSL verification bypassed (expired cert fallback)
    base_url = "https://archive.ics.uci.edu/ml/machine-learning-databases/thyroid-disease/"
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    def read_url(url):
        with urllib.request.urlopen(url, context=ssl_ctx) as resp:
            return pd.read_csv(io.StringIO(resp.read().decode("utf-8")), sep="\s+", header=None)

    train_df = read_url(f"{base_url}ann-train.data")
    test_df  = read_url(f"{base_url}ann-test.data")
    df = pd.concat([train_df, test_df], axis=0).reset_index(drop=True)
    df.columns = cols
    return df

def fetch_diabetes_hospitals():
    from ucimlrepo import fetch_ucirepo
    repo = fetch_ucirepo(id=296)
    return pd.concat([repo.data.features, repo.data.targets], axis=1)

def fetch_cdc_diabetes():
    from ucimlrepo import fetch_ucirepo
    repo = fetch_ucirepo(id=891)
    return pd.concat([repo.data.features, repo.data.targets], axis=1)

def fetch_cdc_diabetes_multiclass():
    import kagglehub
    path = kagglehub.dataset_download("alexteboul/diabetes-health-indicators-dataset")
    # We use the 2015 version which is the standard 3-class variant
    df = pd.read_csv(os.path.join(path, "diabetes_012_health_indicators_BRFSS2015.csv"))
    return df

def fetch_maternal_health():
    from ucimlrepo import fetch_ucirepo
    repo = fetch_ucirepo(id=863)
    return pd.concat([repo.data.features, repo.data.targets], axis=1)

def fetch_diabetic_retinopathy():
    from ucimlrepo import fetch_ucirepo
    repo = fetch_ucirepo(id=329)
    return pd.concat([repo.data.features, repo.data.targets], axis=1)

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
    if source == "support2": 
        df = fetch_support2()
        # If requested Support2-Disease target, map technical codes to Inventory names
        if target.lower() == "dzgroup" or target.lower() == "disease_group":
            # Exhaustive mapping to reach documented Inventory categories
            support2_map = {
                'ARF/MOSF w/Sepsis': 'Sepsis',
                'MOSF w/Sepsis': 'Sepsis',
                'Lung Cancer': 'Cancer', 
                'MOSF w/Malignancy': 'Cancer',
                'MOSF w/Malig': 'Cancer',
                'Colon Cancer': 'Cancer',
                'CHF': 'CHF', 
                'COPD': 'COPD',
                'Coma': 'Other',
                'Cirrhosis': 'Other',
                'Renal Failure': 'Other'
            }
            # Normalize dzgroup values for mapping
            df['target_disease'] = df['dzgroup'].astype(str).str.strip().map(support2_map).fillna('Other')
            df = df.drop(columns=['dzgroup'])
            target = 'target_disease'
    elif source == "thyroid": 
        df = fetch_thyroid()
        # UCI ID 102 ANNEX targets: 3=Negative (6666), 1=Hyper (166), 2=Hypo (368)
        if 'target' in df.columns:
            df['target'] = df['target'].map({3: 'Negative', 1: 'Hypo/Hyper', 2: 'Hypo/Hyper'})
    elif source == "diabetes_hospital": df = fetch_diabetes_hospitals()
    elif source == "cdc_diabetes": 
        if target == "Diabetes_012":
            df = fetch_cdc_diabetes_multiclass()
        else:
            df = fetch_cdc_diabetes()
    elif source == "maternal_health": df = fetch_maternal_health()
    elif source == "hospital_admin":
        df = fetch_hospital_admin()
        # Custom labeling: If predicting bill, create a median-split binary target (Matches 50/50 split in inventory)
        if target.lower() == "high_bill":
            source_col = next((c for c in df.columns if c.lower() == "bill amount"), "Bill Amount")
            median = df[source_col].median()
            df['high_bill'] = (df[source_col] > median).astype(int)
            df = df.drop(columns=[source_col])
        # Simplified multi-class: Group into 4 clear care-type categories (Matches Admin-Category in inventory)
        elif target.lower() == "condition_category":
            source_col = next((c for c in df.columns if c.lower() == "medical condition"), "Medical Condition")
            condition_map = {
                'Fracture': 'Emergency', 'Sprain': 'Emergency', 'Burns': 'Emergency',
                'Stroke': 'Emergency', 'Heart Disease': 'Emergency',
                'COVID-19': 'Infectious', 'Pneumonia': 'Infectious', 'Influenza': 'Infectious',
                'Common Cold': 'Infectious', 'Bronchitis': 'Infectious', 'Sinusitis': 'Infectious',
                'Urinary Tract Infection': 'Infectious', 'Gastroenteritis': 'Infectious',
                'Skin Infection': 'Infectious',
                'Diabetes': 'Chronic', 'Hypertension': 'Chronic', 'Asthma': 'Chronic',
                'Chronic Obstructive Pulmonary Disease': 'Chronic', 'Chronic Kidney Disease': 'Chronic',
                'Arthritis': 'Chronic', 'Allergies': 'Chronic',
                "Alzheimer's Disease": 'Specialized', "Parkinson's Disease": 'Specialized',
                'Epilepsy': 'Specialized', 'Migraine': 'Specialized', 
                'Multiple Sclerosis': 'Specialized', 'Depression': 'Specialized',
                'Anxiety': 'Specialized', 'Cancer': 'Specialized'
            }
            df['condition_category'] = df[source_col].map(condition_map).fillna('Other')
            df = df.drop(columns=[source_col])
    elif source == "stroke_prediction":
        import kagglehub
        df = pd.read_csv(os.path.join(kagglehub.dataset_download("fedesoriano/stroke-prediction-dataset"), "healthcare-dataset-stroke-data.csv"))
    elif source == "diabetic_retinopathy":
        df = fetch_diabetic_retinopathy()
    else: df = pd.read_csv(source)
    
    # Normalize column names to lowercase for consistency
    df.columns = df.columns.str.lower()
    target = target.lower()
    
    if target in df.columns:
        # --- Intelligent Rebalancing (SMOTE) ---
        apply_rebal = config.get("apply_rebalancing")
        counts = df[target].value_counts()
        if len(counts) > 0:
            minority_size = counts.min()
            majority_size = counts.max()
            ratio = majority_size / minority_size if minority_size > 0 else 100
            
            # Auto-trigger rebalancing if:
            # 1. Explicitly requested: config["apply_rebalancing"] = True
            # 2. Set to 'auto' and ratio > 3
            # 3. Not specified (None) but ratio is severe (> 10)
            should_rebalance = (apply_rebal is True) or \
                              (apply_rebal == "auto" and ratio > 3.0) or \
                              (apply_rebal is None and ratio > 10.0)
            
            if should_rebalance:
                try:
                    # Prefer imbalanced-learn for high-quality synthetic data
                    from imblearn.over_sampling import SMOTE
                    y_raw = df[target]
                    X_raw = df.drop(columns=[target])
                    
                    if y_raw.nunique() <= 10 and minority_size > 1 and len(df) < 50000:
                        # Use SMOTE for small/medium datasets for high-quality synthetic data
                        # 1. Encode all Categoricals
                        X_encoded = pd.get_dummies(X_raw, drop_first=True).fillna(0)
                        
                        # 2. Execute Multi-class SMOTE
                        k = min(5, minority_size - 1)
                        smote = SMOTE(random_state=42, k_neighbors=k)
                        X_resampled, y_resampled = smote.fit_resample(X_encoded, y_raw)
                        
                        # 3. Post-process: Round dummy variables to preserve binary integrity
                        binary_cols = [c for c in X_encoded.columns if X_encoded[c].nunique() <= 2]
                        X_resampled[binary_cols] = X_resampled[binary_cols].round()
                        
                        df = pd.DataFrame(X_resampled, columns=X_encoded.columns)
                        df[target] = y_resampled
                        print(f"[Data] Multi-class SMOTE applied ({y_raw.nunique()} classes, Ratio: {ratio:.1f}:1)")
                    else:
                        # For 100k+ rows (Diabetes-Hospital), use High-Speed Random Oversampling
                        # This avoids the O(N^2) neighbor search that causes vLab hangs.
                        raise ValueError("Large dataset detected: Using High-Speed Oversampling")
                except Exception as e:
                    print(f"[Warning] Multi-class Rebalance Fallback: {e}")
                    # Intelligent Naive Fallback: Oversample EVERY minority class to match majority
                    major_size = counts.max()
                    balanced_df = []
                    for cls in counts.index:
                        cls_df = df[df[target] == cls]
                        if len(cls_df) < major_size:
                            # Sample with replacement to match majority size
                            cls_df = cls_df.sample(major_size, replace=True, random_state=42)
                        balanced_df.append(cls_df)
                    df = pd.concat(balanced_df).sample(frac=1).reset_index(drop=True)
                    print(f"[Data] Balanced {len(counts)} classes via selective oversampling.")

    if config.get("sample_size") and len(df) > config["sample_size"]:
        df = df.sample(n=config["sample_size"], random_state=42).reset_index(drop=True)

    drop_cols = [c.lower() for c in config.get("DROP_COLUMNS", [])]
    # Robust Case-Insensitive Drop: Lowercase everything for comparison but keep target alive
    col_map = {c.lower(): c for c in df.columns}
    cols_to_drop = [col_map[d] for d in drop_cols if d in col_map and col_map[d].lower() != target.lower()]
    df = df.drop(columns=cols_to_drop, errors='ignore').replace('?', np.nan)
    
    # --- Intelligent Garbage Collection (Scientific De-noising) ---
    # 1. Identify Truly Categorical vs Truly Numeric & Drop Dead Weight
    initial_cols = list(df.columns)
    for col in initial_cols:
        if col.lower() == target.lower(): continue
        
        # A. Drop Identifiers (if cardinality == length or it looks like an ID)
        if df[col].nunique() >= (len(df) * 0.95) or "id" in col.lower() or "nbr" in col.lower() or "number" in col.lower():
            df = df.drop(columns=[col])
            continue

        # B. Drop Columns with too much missing data (> 50%)
        if df[col].isnull().sum() > (len(df) * 0.5):
            df = df.drop(columns=[col])
            continue
            
        # C. Drop Zero-Variance Columns (Single values provide no signal)
        if df[col].nunique() <= 1:
            df = df.drop(columns=[col])
            continue

        # D. Convert legitimate numbers
        s = pd.to_numeric(df[col], errors='coerce')
        if s.notnull().sum() > (len(df) * 0.5): # If >50% can be numeric
            df[col] = s
            
    # 2. Robust Imputation
    # Fill numeric with median, categorical with 'Unknown'
    num_cols = df.select_dtypes(include=[np.number]).columns
    cat_cols = df.select_dtypes(exclude=[np.number]).columns
    
    medians = df[num_cols].median().fillna(0)
    df[num_cols] = df[num_cols].fillna(medians)
    df[cat_cols] = df[cat_cols].fillna("Unknown")
    
    # Final safety: any column still entirely NaN (no median) gets zeros
    df = df.fillna(0)
    
    # 3. Handle Partition Column
    partition_col = config.get("PARTITION_COLUMN", "").lower() if config.get("PARTITION_COLUMN") else None
    if partition_col and partition_col in df.columns:
        parts = df[partition_col].astype(str)
        df = df.drop(columns=[partition_col])
        if partition_col in cat_cols: cat_cols = cat_cols.drop(partition_col)
    else:
        parts = pd.Series([f"Hospital_{i+1}" for i in np.random.randint(0, config.get("NUM_PARTITIONS", 5), len(df))], index=df.index)
    
    # Label encode target if it is categorical or not 0-indexed
    # Drop rows where target is NaN (useless for training)
    df = df.dropna(subset=[target])
    
    target_vals = df[target].unique()
    is_not_zero_indexed = df[target].dtype.kind in 'biufc' and (len(target_vals) > 0 and (target_vals.min() != 0 or target_vals.max() != len(target_vals) - 1))
    if df[target].dtype == 'object' or df[target].dtype.name == 'category' or is_not_zero_indexed:
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        df[target] = le.fit_transform(df[target])
        print(f"[Data] Encoded target '{target}' into {len(le.classes_)} classes ({le.classes_} -> range({len(le.classes_)})).")

    # One-hot encode categorical features
    cols_to_encode = [c for c in cat_cols if c not in [partition_col, target]]
    if cols_to_encode:
        df = pd.get_dummies(df, columns=cols_to_encode, drop_first=True)

    X, y = df.drop(columns=[target]).astype(np.float32), df[target].astype(np.float32)
    return X, np.asarray(y), parts, X.shape[1], (1 if y.nunique() <= 2 else int(y.nunique()))

def create_dataloaders(X, y, batch_size=1024):
    """Premium Data Pipeline: Uses optimized workers and memory pinning for GPU throughput."""
    use_gpu = torch.cuda.is_available()
    return DataLoader(
        TensorDataset(
            torch.tensor(X.values if hasattr(X, 'values') else X).float(), 
            torch.tensor(y).float()
        ), 
        batch_size=batch_size, 
        shuffle=True,
        num_workers=0, # Better for small tabular data to avoid process fork overhead
        pin_memory=use_gpu
    )

# --- GLOBAL DATA CACHE ---
_DATA_CACHE = {}

def get_data_cached(config):
    """Prevents redundant disk I/O and SMOTE execution during sweeps."""
    cache_key = f"{config.get('DATA_SOURCE')}_{config.get('TARGET_COLUMN')}_{config.get('sample_size')}_{config.get('apply_rebalancing')}"
    if cache_key in _DATA_CACHE:
        return _DATA_CACHE[cache_key]
    
    data = load_tabular_data(config)
    _DATA_CACHE[cache_key] = data
    return data
