import json
import os

nb_path = "MedShare_FINAL_new.ipynb"
if not os.path.exists(nb_path):
    print(f"Notebook {nb_path} not found.")
    exit(1)

with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# The target cell is Phase 1.5, usually cell index 2 (0-indexed)
# Let's find it by id or content
target_cell = None
for cell in nb["cells"]:
    if cell["cell_type"] == "code" and "PHASE 1.5" in "".join(cell["source"]):
        target_cell = cell
        break

if not target_cell:
    print("Could not find patch cell in notebook.")
    exit(1)

# The patch cell contains a python script that writes data.py
# We need to update the lines array inside that python script.
source = "".join(target_cell["source"])

old_block = """        '        if "Class" in df.columns:',
        '            df = df.rename(columns={"Class": "target"})',"""

new_block = """        '        # Standardize column names to match the definitive schema',
        '        df.columns = cols ',"""

if old_block in source:
    new_source = source.replace(old_block, new_block)
    target_cell["source"] = [line + ("\n" if not line.endswith("\n") else "") for line in new_source.splitlines()]
    
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
    print(f"Successfully patched {nb_path} to Gold Standard.")
else:
    print("Patch block not found or already updated.")
