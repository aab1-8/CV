#/bin/bash
source venv/bin/activate
python federated_survival.py --dataset cdc_diabetes_012 --epochs 20 --sample_size 253680 --enable_blockchain True --enable_dp True
