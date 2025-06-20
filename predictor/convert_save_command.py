import subprocess
import sys
import os
import time
import shutil
import pandas as pd
import argparse

# --- Argument parsing ---
parser = argparse.ArgumentParser(description="Run VTune profiling and convert results")
parser.add_argument('-a', '--app', required=True, help='Path to the target application')
args = parser.parse_args()

# --- Set paths based on app location ---
app_path = os.path.abspath(args.app)
working_dir = os.path.dirname(app_path)
result_dir = os.path.abspath("vtune_results_uarch")
report_csv = os.path.abspath("vtune_bottomup.csv")
converted_csv = os.path.abspath("transformed_vtune_output.csv")

# --- VTune CLI path (updated) ---
vtune_cli = r"C:\Program Files (x86)\Intel\oneAPI\vtune\2024.1\bin64\vtune.exe"

# --- Check VTune CLI tool exists ---
if not os.path.exists(vtune_cli):
    print("[ERROR] VTune CLI not found.")
    sys.exit(1)

# --- Clean old results ---
if os.path.exists(result_dir):
    print(f"[INFO] Removing old result directory: {result_dir}")
    shutil.rmtree(result_dir)

# --- Collect profile data ---
cmd_collect = [
    vtune_cli, "-collect", "uarch-exploration", "-result-dir", result_dir,
    "-follow-child", "-app-working-dir", working_dir, "--", app_path
]

print("[INFO] Profiling started...")
proc = subprocess.Popen(cmd_collect)
time.sleep(120)  # Adjust as needed for profiling duration

# --- Stop VTune ---
print("[INFO] Stopping VTune...")
subprocess.run([vtune_cli, "-r", result_dir, "-command", "stop"], check=True)
proc.wait()
print("[INFO] Waiting 60 seconds for VTune to finalize results...")
time.sleep(60)

# --- Export CSV ---
print("[INFO] Exporting report to CSV...")
subprocess.run([
    vtune_cli, "-report", "hotspots", "-result-dir", result_dir,
    "-group-by", "function", "-format", "csv", "-report-output", report_csv
], check=True)
print(f"[INFO] Bottom-up CSV report generated: {report_csv}")

# --- Convert CSV format ---
print("[INFO] Converting CSV format...")
vtune_df = pd.read_csv(report_csv, delimiter='\t', engine='python')
required_columns_mapping = {
    'Function': 'Function / Call Stack',
    'CPU Time': 'CPU Time',
    'Clockticks': 'Clockticks',
    'Instructions Retired': 'Instructions Retired',
    'CPI Rate': 'CPI Rate',
    'Retiring(%)': 'Retiring',
    'Front-End Bound(%)': 'Front-End Bound',
    'Bad Speculation(%)': 'Bad Speculation',
    'Back-End Bound(%)': 'Back-End Bound',
    'Average CPU Frequency': 'Average CPU Frequency',
    'Module': 'Module',
    'Function (Full)': 'Function (Full)',
    'Source File': 'Source File',
    'Start Address': 'Start Address'
}
transformed_df = vtune_df[list(required_columns_mapping.keys())].rename(columns=required_columns_mapping)
transformed_df.to_csv(converted_csv, index=False)
print(f"[INFO] Transformed file saved to: {converted_csv}")

# --- Final message ---
time.sleep(30)
print("[INFO] Ready to predict")
