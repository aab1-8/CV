import json
import os

notebook_path = 'MedShare_FINAL.ipynb'
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

updated = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code' and any(">>> CRITICAL VERIFICATION: GAS EXPERIMENT <<<" in line for line in cell['source']):
        new_source = []
        for line in cell['source']:
            # Update Gas experiment to 5 epochs
            if '--experiment gas' in line:
                if '--epochs 10' in line: line = line.replace('--epochs 10', '--epochs 5')
                elif '--epochs 3' in line: line = line.replace('--epochs 3', '--epochs 5')
                elif '--epochs 1' in line: line = line.replace('--epochs 1', '--epochs 5')
            
            # Update benchmark loop to 5 epochs
            if '--epochs 10' in line and 'cmd' in line:
                line = line.replace('--epochs 10', '--epochs 5')
            elif '--epochs 3' in line and 'cmd' in line:
                line = line.replace('--epochs 3', '--epochs 5')
            elif '--epochs 1' in line and 'cmd' in line:
                line = line.replace('--epochs 1', '--epochs 5')
            
            new_source.append(line)
        
        cell['source'] = new_source
        updated = True
        print("Updated Cell 5 with High-Performance Epochs (5)")
        break

if updated:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print("✅ MedShare_FINAL.ipynb updated with High-Performance settings!")
else:
    print("❌ Could not find the target cell in the notebook.")
