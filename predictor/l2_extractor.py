
import pandas as pd
import glob
import os
import re

# Global maximum values for each feature (used for normalization)
global_max = {
    'CPU Time': 75.4814,
    'Clockticks': 349650000000,
    'Instructions Retired': 212380000000,
    'CPI Rate': 58.0,
    'Retiring': 1.0,
    'Front-End Bound': 1.0,
    'Bad Speculation': 1.0,
    'Back-End Bound': 1.0,
    'Average CPU Frequency': 29568100000.0,
}

# Use environment variables for paths
base_path = os.getenv("DATA_DIR", "./data")
output_folder = os.getenv("OUTPUT_DIR", "./output")
os.makedirs(output_folder, exist_ok=True)

def extract_index(file_path):
    filename = os.path.basename(file_path)
    match = re.match(r'(\d+)_', filename)
    return int(match.group(1)) if match else float('inf')

def process_file(file_path, index):
    df = pd.read_csv(file_path)

    if df.shape[1] >= 14:
        df_cleaned = df.drop(df.columns[10:14], axis=1)
    else:
        df_cleaned = df.copy()

    df_numeric = df_cleaned.iloc[:, 1:].apply(pd.to_numeric, errors='coerce').fillna(0)

    df_normalized = df_numeric.copy()
    for col in df_normalized.columns:
        if col in global_max and global_max[col] != 0:
            df_normalized[col] = df_normalized[col] / global_max[col] * 100

    l2_norm = (df_normalized**2).sum(axis=0).pow(0.5)
    l2_norm_df = pd.DataFrame([l2_norm])
    file_name = os.path.basename(file_path)
    l2_norm_df.insert(0, 'file_name', file_name)
    l2_norm_df.insert(0, 'index', index)

    return l2_norm_df

final_l2_norm_df = pd.DataFrame()
csv_files = sorted(glob.glob(os.path.join(base_path, '*.csv')), key=extract_index)

for i, file_path in enumerate(csv_files, start=1):
    try:
        l2_df = process_file(file_path, i)

        if final_l2_norm_df.empty:
            columns = ['index', 'file_name'] + l2_df.columns[2:].tolist()
            l2_df.columns = columns
        else:
            l2_df.columns = final_l2_norm_df.columns

        final_l2_norm_df = pd.concat([final_l2_norm_df, l2_df], ignore_index=True)

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
