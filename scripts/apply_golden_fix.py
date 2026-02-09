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
            # Update Gas experiment
            if '--experiment gas --rounds 50' in line:
                line = line.replace('--rounds 50', '--rounds 20')
                line = line.replace('--epochs 10', '--epochs 3')
            elif '--experiment gas' in line and '--rounds 5' in line: # Catching older versions too
                line = line.replace('--rounds 5', '--rounds 20')
                line = line.replace('--epochs 1', '--epochs 3')
            
            # Update Loop Rounds
            if 'r = 50' in line:
                line = line.replace('r = 50', 'r = 20')
            elif 'r = 7' in line or 'r = 1' in line: # Catching older versions
                line = "        r = 20  # Optimized rounds\n"

            # Update Loop Epochs
            if '--epochs 10' in line and 'cmd' in line:
                line = line.replace('--epochs 10', '--epochs 3')
            elif '--epochs 1' in line and 'cmd' in line: # Catching older versions
                line = line.replace('--epochs 1', '--epochs 3')
            
            new_source.append(line)
        
        cell['source'] = new_source
        updated = True
        print("Updated Cell 5 with Optimized Rounds (20) and Epochs (3)")
        break

if updated:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print("✅ MedShare_FINAL.ipynb updated successfully!")
else:
    print("❌ Could not find the target cell in the notebook.")
