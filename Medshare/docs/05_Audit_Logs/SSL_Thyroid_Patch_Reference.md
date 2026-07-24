# UCI ML Repository SSL Certificate Fallback Patch

*Created: March 18, 2026*

This snippet was originally used in the `MedShare_FINAL_new.ipynb` Google Colab notebook as **Phase 1.5**. 
It is a "Self-Healing Patch" designed specifically to replace the `fetch_thyroid()` function in `medshare/data.py` on the fly. 

It is maintained here for reference in case the Medical Dataset Repository at UCI experiences future SSL Certificate Expirations during tests involving the `Thyroid` dataset.

---

### Python Script (Colab Cell)

```python
## 🔧 PHASE 1.5: SELF-HEALING PATCH (SSL Certificate Fix)
# Directly patches fetch_thyroid() by writing the fixed function into data.py.
# Uses string find/replace to locate the old function — no regex, no escape issues.
import sys

data_py_path = 'medshare/data.py'
with open(data_py_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find start and end of the old fetch_thyroid function
start_marker = 'def fetch_thyroid():'
end_marker = '\ndef fetch_diabetes_hospitals():'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print('⚠️  Could not locate fetch_thyroid block — skipping patch.')
else:
    # Build the replacement using a list of lines to avoid any escape issues
    lines = [
        'def fetch_thyroid():',
        '    import pandas as pd, ssl, urllib.request, io',
        '',
        '    cols = [',
        '        "age", "sex", "on_thyroxine", "query_on_thyroxine", "on_antithyroid_medication",',
        '        "sick", "pregnant", "thyroid_surgery", "i131_treatment", "query_hypothyroid",',
        '        "query_hyperthyroid", "lithium", "goitre", "tumor", "hypopituitary", "psych",',
        '        "tsh", "t3", "tt4", "t4u", "fti", "target"',
        '    ]',
        '',
        '    # Method 1: ucimlrepo (preferred, no SSL issues)',
        '    try:',
        '        from ucimlrepo import fetch_ucirepo',
        '        print("[Data] Fetching Thyroid via ucimlrepo...")',
        '        repo = fetch_ucirepo(id=102)',
        '        X = repo.data.features',
        '        y = repo.data.targets',
        '        df = pd.concat([X.reset_index(drop=True), y.reset_index(drop=True)], axis=1)',
        '        # Standardize column names to match the definitive schema',
        '        df.columns = cols ',
        '        print(f"[Data] Thyroid loaded via ucimlrepo: {len(df)} rows, {len(df.columns)} cols")',
        '        return df',
        '    except Exception as e:',
        '        print(f"[Data] ucimlrepo failed ({e}), falling back to direct download...")',
        '',
        '    # Method 2: Direct URL with SSL verification bypassed (expired cert fallback)',
        '    base_url = "https://archive.ics.uci.edu/ml/machine-learning-databases/thyroid-disease/"',
        '    ssl_ctx = ssl.create_default_context()',
        '    ssl_ctx.check_hostname = False',
        '    ssl_ctx.verify_mode = ssl.CERT_NONE',
        '',
        '    def read_url(url):',
        '        with urllib.request.urlopen(url, context=ssl_ctx) as resp:',
        '            return pd.read_csv(io.StringIO(resp.read().decode("utf-8")), sep="\\s+", header=None)',
        '',
        '    train_df = read_url(f"{base_url}ann-train.data")',
        '    test_df  = read_url(f"{base_url}ann-test.data")',
        '    df = pd.concat([train_df, test_df], axis=0).reset_index(drop=True)',
        '    df.columns = cols',
        '    return df',
    ]
    new_fn = '\n'.join(lines)

    patched = content[:start_idx] + new_fn + '\n' + content[end_idx:]

    with open(data_py_path, 'w', encoding='utf-8') as f:
        f.write(patched)
    print('✅ PATCH APPLIED: fetch_thyroid() now uses ucimlrepo (SSL-safe)')

# Clear any cached medshare imports so the subprocess picks up fresh .py files
for mod in list(sys.modules.keys()):
    if 'medshare' in mod:
        del sys.modules[mod]
print('✅ Module cache cleared')
```
