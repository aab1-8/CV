import os, requests, zipfile, io, pandas as pd, numpy as np, torch # Core libraries for data and connectivity
from torch.utils.data import DataLoader, TensorDataset # Converts Pandas data into PyTorch datasets

def fetch_support2():
    """Fetches the SUPPORT2 clinical dataset—a benchmark for survival and prognosis prediction."""
    try:
        from ucimlrepo import fetch_ucirepo
        repo = fetch_ucirepo(id=880)
        return pd.concat([repo.data.features, repo.data.targets], axis=1) # Combine frame
    except:
        # Fallback for systems with restricted library access
        r = requests.get("https://archive.ics.uci.edu/static/public/880/support2.zip")
        with zipfile.ZipFile(io.BytesIO(r.content)) as z: return pd.read_csv(z.open('support2.csv'))

def fetch_thyroid():
    """Fetches the Thyroid Disease dataset with fallback paths for network reliability."""
    import pandas as pd, ssl, urllib.request, io
    # Standardised clinical column names used throughout the project
    cols = ["age", "sex", "on_thyroxine", "query_on_thyroxine", "on_antithyroid_medication",
            "sick", "pregnant", "thyroid_surgery", "i131_treatment", "query_hypothyroid",
            "query_hyperthyroid", "lithium", "goitre", "tumor", "hypopituitary", "psych",
            "tsh", "t3", "tt4", "t4u", "fti", "target"]
    try:
        from ucimlrepo import fetch_ucirepo
        repo = fetch_ucirepo(id=102)
        X, y = repo.data.features, repo.data.targets
        df = pd.concat([X.reset_index(drop=True), y.reset_index(drop=True)], axis=1)
        df.columns = cols 
        return df
    except Exception as e:
        print(f"[Data] ucimlrepo failed ({e}), falling back to direct URL...")

    # Method 2: Manual URL parsing
    base_url = "https://archive.ics.uci.edu/ml/machine-learning-databases/thyroid-disease/"
    # Fetches the ANN-Train and ANN-Test data from UCI archives (ORIGINAL COMMENT PRESERVED)
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname, ssl_ctx.verify_mode = False, ssl.CERT_NONE

    def read_url(url):
        with urllib.request.urlopen(url, context=ssl_ctx) as resp:
            return pd.read_csv(io.StringIO(resp.read().decode("utf-8")), sep="\s+", header=None)
    # Concatenate training and testing instances
    train_df, test_df = read_url(f"{base_url}ann-train.data"), read_url(f"{base_url}ann-test.data")
    df = pd.concat([train_df, test_df], axis=0).reset_index(drop=True)
    df.columns = cols
    return df

def fetch_diabetes_hospitals():
    """Fetches US Hospitals Diabetes records (1999-2008)."""
    from ucimlrepo import fetch_ucirepo
    repo = fetch_ucirepo(id=296)
    return pd.concat([repo.data.features, repo.data.targets], axis=1)

def fetch_cdc_diabetes():
    """Fetches binary CDC Diabetes Indicators."""
    from ucimlrepo import fetch_ucirepo
    repo = fetch_ucirepo(id=891)
    return pd.concat([repo.data.features, repo.data.targets], axis=1)

def fetch_cdc_diabetes_multiclass():
    """Fetches the 3-class Kaggle health indicator variant."""
    import kagglehub
    path = kagglehub.dataset_download("alexteboul/diabetes-health-indicators-dataset")
    return pd.read_csv(os.path.join(path, "diabetes_012_health_indicators_BRFSS2015.csv"))

def fetch_maternal_health():
    """Fetches Maternal Health Risk dataset."""
    from ucimlrepo import fetch_ucirepo
    repo = fetch_ucirepo(id=863)
    return pd.concat([repo.data.features, repo.data.targets], axis=1)

def fetch_diabetic_retinopathy():
    """Fetches DIABETIC_RETINOPATHY Debrecen dataset."""
    from ucimlrepo import fetch_ucirepo
    repo = fetch_ucirepo(id=329)
    return pd.concat([repo.data.features, repo.data.targets], axis=1)

def fetch_hospital_admin():
    """Fetches the Hospital Patient Records CSV."""
    import kagglehub
    path = kagglehub.dataset_download("devildyno/hospital-patient-records-jan-2021-july-2024")
    for file in os.listdir(path):
        if file.endswith(".csv"): return pd.read_csv(os.path.join(path, file))
    raise FileNotFoundError("CSV not found in hospital admin dataset")

def load_tabular_data(config):
    """Universal Loader: Cleans and prepares dataset according to experimental config."""
    source, target = config.get("DATA_SOURCE", "support2"), config["TARGET_COLUMN"]
    
    # 1. Routing: Map source to specific clinical loaders
    if source == "support2": 
        df = fetch_support2()
        if target.lower() in ["dzgroup", "disease_group"]:
            # Standardised health category mapping for SUPPORT2
            support2_map = {
                'ARF/MOSF w/Sepsis': 'Sepsis', 'MOSF w/Sepsis': 'Sepsis',
                'Lung Cancer': 'Cancer', 'MOSF w/Malignancy': 'Cancer',
                'MOSF w/Malig': 'Cancer', 'Colon Cancer': 'Cancer',
                'CHF': 'CHF', 'COPD': 'COPD', 'Coma': 'Other', 
                'Cirrhosis': 'Other', 'Renal Failure': 'Other'
            }
            df['target_disease'] = df['dzgroup'].astype(str).str.strip().map(support2_map).fillna('Other')
            df, target = df.drop(columns=['dzgroup']), 'target_disease'
    elif source == "thyroid": 
        df = fetch_thyroid()
        # Binary target mapping: Hyper/Hypo cases to Positive
        if 'target' in df.columns:
            df['target'] = df['target'].map({3: 'Negative', 1: 'Hypo/Hyper', 2: 'Hypo/Hyper'})
    elif source == "diabetes_hospital": df = fetch_diabetes_hospitals()
    elif source == "cdc_diabetes": 
        if target == "Diabetes_012": df = fetch_cdc_diabetes_multiclass()
        else: df = fetch_cdc_diabetes()
    elif source == "maternal_health": df = fetch_maternal_health()
    elif source == "hospital_admin":
        df = fetch_hospital_admin()
        # admin-bill: Median split for a high bill vs low bill classification task (ORIGINAL COMMENT PRESERVED)
        if target.lower() == "high_bill":
            source_col = next((c for c in df.columns if c.lower() == "bill amount"), "Bill Amount")
            median = df[source_col].median()
            df['high_bill'] = (df[source_col] > median).astype(int)
            df = df.drop(columns=[source_col])
        elif target.lower() == "condition_category":
            source_col = next((c for c in df.columns if c.lower() == "medical condition"), "Medical Condition")
            # Simplified multi-class: Group into 4 clear care-type categories (Matches Admin-Category in inventory) (ORIGINAL COMMENT PRESERVED)
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
    elif source == "diabetic_retinopathy": df = fetch_diabetic_retinopathy()
    else: df = pd.read_csv(source)
    
    # Consistent lowercase naming for data pipeline stability
    df.columns = df.columns.str.lower()
    target = target.lower()
    
    # 2. Intelligent Rebalancing (SMOTE)
    if target in df.columns:
        apply_rebal = config.get("apply_rebalancing")
        counts = df[target].value_counts()
        if len(counts) > 0:
            minority_size = counts.min()
            majority_size = counts.max()
            ratio = majority_size / minority_size if minority_size > 0 else 100
            # Condition to rebalance: extreme skew or 'auto' mode triggered
            if (apply_rebal is True) or (apply_rebal == "auto" and ratio > 3.0) or (apply_rebal is None and ratio > 10.0):
                try:
                    from imblearn.over_sampling import SMOTE
                    y_raw, X_raw = df[target], df.drop(columns=[target])
                    if y_raw.nunique() <= 10 and minority_size > 1 and len(df) < 50000:
                        # Synthetic Minority Over-sampling Technique (SMOTE)
                        X_encoded = pd.get_dummies(X_raw, drop_first=True).fillna(0)
                        k = min(5, minority_size - 1)
                        smote = SMOTE(random_state=42, k_neighbors=k)
                        X_resampled, y_resampled = smote.fit_resample(X_encoded, y_raw)
                        # RESTORED: Precise rounding for binary indicators after synthetic gen (ORIGINAL COMMENT PRESERVED)
                        binary_cols = [c for c in X_encoded.columns if X_encoded[c].nunique() <= 2]
                        X_resampled[binary_cols] = X_resampled[binary_cols].round()
                        df = pd.DataFrame(X_resampled, columns=X_encoded.columns)
                        df[target] = y_resampled
                    else: raise ValueError("Large dataset detected")
                except Exception as e:
                    # Random Oversampling for large datasets (faster for vLab environment) (ORIGINAL VERBATIM RESTORED)
                    major_size = counts.max()
                    balanced_df = []
                    for cls in counts.index:
                        cls_df = df[df[target] == cls]
                        if len(cls_df) < major_size:
                            cls_df = cls_df.sample(major_size, replace=True, random_state=42)
                        balanced_df.append(cls_df)
                    df = pd.concat(balanced_df).sample(frac=1).reset_index(drop=True)

    # 3. Data Cleaning (Identifier Stripping/Imputation)
    if config.get("sample_size") and len(df) > config["sample_size"]:
        df = df.sample(n=config["sample_size"], random_state=42).reset_index(drop=True)

    drop_cols = [c.lower() for c in config.get("DROP_COLUMNS", [])]
    col_map = {c.lower(): c for c in df.columns}
    cols_to_drop = [col_map[d] for d in drop_cols if d in col_map and col_map[d].lower() != target.lower()]
    df = df.drop(columns=cols_to_drop, errors='ignore').replace('?', np.nan)
    
    # 4. Identity & Missing Data Cleaning
    # Identify and remove identity/uninformative columns (ORIGINAL COMMENT PRESERVED)
    for col in list(df.columns):
        if col.lower() == target.lower(): continue
        # Drop ID-like columns (High cardinality or containing "id")
        if df[col].nunique() >= (len(df)*0.95) or any(s in col.lower() for s in ["id", "nbr", "number"]):
            df = df.drop(columns=[col]); continue
        # Drop sparse columns (>50% Null)
        if df[col].isnull().sum() > (len(df)*0.5): df = df.drop(columns=[col]); continue
        # Drop constant columns
        if df[col].nunique() <= 1: df = df.drop(columns=[col]); continue
        # Coerce valid strings to numeric
        s = pd.to_numeric(df[col], errors='coerce')
        if s.notnull().sum() > (len(df)*0.5): df[col] = s
            
    # Step 5: Imputation (Median for numbers, 'Unknown' for categories)
    # median fill for numeric, 'Unknown' for categorical (ORIGINAL COMMENT PRESERVED)
    num_cols, cat_cols = df.select_dtypes(include=[np.number]).columns, df.select_dtypes(exclude=[np.number]).columns
    medians = df[num_cols].median().fillna(0)
    df[num_cols] = df[num_cols].fillna(medians)
    df[cat_cols] = df[cat_cols].fillna("Unknown")
    df = df.fillna(0).dropna(subset=[target])
    
    # Step 6: Data Skew (Heterogeneity Simulation)
    het = config.get("heterogeneity", "none").lower()
    num_parts = config.get("NUM_PARTITIONS", 5)
    if het == "label": df = df.sort_values(by=target).reset_index(drop=True)
    elif het == "feature":
        feat_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != target]
        if feat_cols: df = df.sort_values(by=feat_cols[0]).reset_index(drop=True)

    # Step 7: Partition Logic
    # Partitioning based on Hospital ID (ORIGINAL COMMENT PRESERVED)
    partition_col = config.get("PARTITION_COLUMN", "").lower() if config.get("PARTITION_COLUMN") else None
    if partition_col and partition_col in df.columns:
        parts = df[partition_col].astype(str)
        df, cat_cols = df.drop(columns=[partition_col]), cat_cols.drop(partition_col) if partition_col in cat_cols else cat_cols
    else:
        # ORIGINAL LOGIC RESTORED: Selection between sequential and random splits
        if het != "none":
            indices = np.arange(len(df))
            parts_arr = np.array([f"Hospital_{(i * num_parts // len(df)) + 1}" for i in indices])
            parts = pd.Series(parts_arr, index=df.index)
        else:
            # Traditional Random IID Split
            parts = pd.Series([f"Hospital_{i+1}" for i in np.random.randint(0, num_parts, len(df))], index=df.index)
    
    # Step 8: Multi-class Encoding & Matrix Creation
    # convert target to labels if necessary (ORIGINAL COMMENT PRESERVED)
    if df[target].dtype == 'object' or df[target].dtype.name == 'category' or (df[target].dtype.kind in 'biufc' and (df[target].unique().min() != 0 or df[target].unique().max() != len(df[target].unique())-1)):
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        df[target] = le.fit_transform(df[target])
    
    cols_to_encode = [c for c in cat_cols if c != target]
    if cols_to_encode: df = pd.get_dummies(df, columns=cols_to_encode, drop_first=True)

    # Convert to Neural-Network-Ready floating point format
    X, y = df.drop(columns=[target]).astype(np.float32), df[target].astype(np.float32)
    return X, np.asarray(y), parts, X.shape[1], (1 if y.nunique() <= 2 else int(y.nunique()))

def create_dataloaders(X, y, batch_size=1024):
    """Utility for creating batches of clinical tensors for GPU/CPU training."""
    return DataLoader(TensorDataset(torch.tensor(X.values if hasattr(X, 'values') else X).float(), torch.tensor(y).float()), 
                      batch_size=batch_size, shuffle=True, pin_memory=torch.cuda.is_available())

_DATA_CACHE = {}
def get_data_cached(config):
    """Memory Cache: Prevents re-running preprocessing/SMOTE during multiple sweep rounds."""
    key = f"{config.get('DATA_SOURCE')}_{config.get('TARGET_COLUMN')}_{config.get('sample_size')}_{config.get('apply_rebalancing')}_{config.get('heterogeneity', 'none')}"
    if key not in _DATA_CACHE: _DATA_CACHE[key] = load_tabular_data(config)
    return _DATA_CACHE[key]
