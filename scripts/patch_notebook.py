import json

notebook_path = 'MedShare_FINAL.ipynb'
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

found = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        for i, line in enumerate(source):
            if 'ganache' in line and '--database.dbPath' in line:
                source[i] = line.replace('--database.dbPath', '--wallet.defaultBalance').replace('./ganache_db', '100')
                found = True

if found:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    print("Notebook patched successfully.")
else:
    print("Ganache startup line not found in notebook.")
