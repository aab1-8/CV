import pandas as pd
import os
import kagglehub

path = kagglehub.dataset_download('devildyno/hospital-patient-records-jan-2021-july-2024')
csv = os.listdir(path)[0]
df = pd.read_csv(os.path.join(path, csv))

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

df['category'] = df['Medical Condition'].map(condition_map).fillna('Other')
print('5-Class Distribution:')
print(df['category'].value_counts())
print(f'\nTotal: {len(df)} patients')
