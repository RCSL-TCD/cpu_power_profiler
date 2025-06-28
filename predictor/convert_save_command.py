import subprocess
import sys
import os
import time
import shutil
import pandas as pd
import argparse
import shlex


def convert_save_command(result_dir, app_path, vtune_cli, working_dir, headless_mode, app_cmd):
    """
    Run the convert_save_command.py script to process the application path.
    """

    # --- Check VTune CLI tool exists ---
    if not os.path.exists(vtune_cli):
        print("[ERROR] VTune CLI not found.")
        sys.exit(1)

    # --- Clean old results ---
    if os.path.exists(result_dir):
        print(f"[INFO] Removing old result directory: {result_dir}")
        shutil.rmtree(result_dir)
    os.makedirs(result_dir, exist_ok=True)

    # --- Collect profile data ---
    if headless_mode:
        app_command_list = shlex.split(app_cmd)
        cmd_collect = [
        vtune_cli,
        "-collect", "uarch-exploration",
        "-result-dir", result_dir,
        "-follow-child",
        "-app-working-dir", os.getcwd(),
    ] + app_command_list
        print("[INFO] Profiling in the 'headless' mode, ")
        proc = subprocess.run(cmd_collect, check=True)
        print("[INFO] Profiling finished.")
    else:
        cmd_collect = [
        vtune_cli,
        "-collect", "uarch-exploration", "-result-dir", result_dir,
        "-follow-child", "-app-working-dir", working_dir, "--", app_path
        ]
        print("[INFO] Profiling in the 'interactive' mode")
        proc = subprocess.Popen(cmd_collect)
        time.sleep(120)  # Adjust as needed for profiling duration
        # --- Stop VTune ---
        print("[INFO] Stopping VTune...")
        subprocess.run([vtune_cli, "-r", result_dir, "-command", "stop"], check=True)
        proc.wait()
        print("[INFO] Waiting 60 seconds for VTune to finalize results...")
        time.sleep(60)


def export_csv(result_dir, vtune_cli, report_csv):
    """
    Export the VTune report to CSV format.
    """
    print("[INFO] Exporting report to CSV...")
    subprocess.run([
        vtune_cli, "-report", "hotspots", "-result-dir", result_dir,
        "-group-by", "function", "-format", "csv", "-report-output", report_csv
    ], check=True)
    print(f"[INFO] Bottom-up CSV report generated: {report_csv}")

def convert_csv_format(report_csv, converted_csv):
    """
    Convert the raw CSV report to the required format.
    """
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
