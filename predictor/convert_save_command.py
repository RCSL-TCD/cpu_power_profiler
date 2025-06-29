import subprocess
import sys
import os
import time
import shutil
import pandas as pd
import shlex
import cpuinfo


def get_cpu_brand():
    """Returns the CPU brand string."""
    try:
        return cpuinfo.get_cpu_info().get('brand_raw', 'Unknown CPU')
    except Exception:
        return "Could not determine CPU brand"


def convert_save_command(result_dir, app_path, vtune_cli, working_dir, headless_mode, app_cmd, logger):
    """
    Run the convert_save_command.py script to process the application path.
    """

    # --- Check VTune CLI tool exists ---
    if not os.path.exists(vtune_cli):
        print("[ERROR] VTune CLI not found.")
        sys.exit(1)

    # --- Clean old results ---
    if os.path.exists(result_dir):
        logger.info(f"Removing old result directory: {result_dir}")
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
        logger.info(
            f"Running VTune in headless mode with command: {' '.join(cmd_collect)}")
        proc = subprocess.run(cmd_collect, check=True)
        logger.info(
            f"VTune profiling completed with return code: {proc.returncode}")
    else:
        cmd_collect = [
            vtune_cli,
            "-collect", "uarch-exploration", "-result-dir", result_dir,
            "-follow-child", "-app-working-dir", working_dir, "--", app_path
        ]
        logger.info(
            f"Running VTune in interactive mode with command: {' '.join(cmd_collect)}")
        proc = subprocess.Popen(cmd_collect)
        time.sleep(120)  # Adjust as needed for profiling duration
        # --- Stop VTune ---
        logger.info("Stopping VTune...")
        subprocess.run([vtune_cli, "-r", result_dir,
                       "-command", "stop"], check=True)
        proc.wait()
        logger.info(
            f"VTune profiling completed with return code: {proc.returncode}")
        time.sleep(60)


def export_csv(result_dir, vtune_cli, report_csv, logger):
    """
    Export the VTune report to CSV format.
    """

    logger.info("Exporting VTune report to CSV")
    subprocess.run([
        vtune_cli, "-report", "hotspots", "-result-dir", result_dir,
        "-group-by", "function", "-format", "csv", "-report-output", report_csv
    ], check=True)
    logger.info(f"VTune report exported to CSV: {report_csv}")


def convert_csv_format(report_csv, converted_csv, logger):
    """
    Convert the raw CSV report to the required format.
    """
    cpu_brand = get_cpu_brand()
    hybrid_cpu_keywords = [
        '12th gen', '13th gen', '14th gen', '15th gen',  # Generation numbers
        'alder lake', 'raptor lake', 'meteor lake', 'arrow lake',  # Codenames
        'core ultra'  # New branding for hybrid CPUs
    ]
    is_hybrid_cpu = any(keyword in cpu_brand.lower()
                        for keyword in hybrid_cpu_keywords)
    logger.info(f"CPU Detected: {cpu_brand}, Hybrid CPU: {is_hybrid_cpu}")

    logger.info("Converting CSV format")
    vtune_df = pd.read_csv(report_csv, delimiter='\t', engine='python')

    if is_hybrid_cpu:
        logger.info("Hybrid CPU detected. Summing P-core and E-core metrics.")
        core_specific_metrics = [
            'Retiring(%)',
            'Front-End Bound(%)',
            'Bad Speculation(%)',
            'Back-End Bound(%)',
        ]

        for metric in core_specific_metrics:
            p_col = f'Performance-core (P-core):{metric}'
            e_col = f'Efficient-core (E-core):{metric}'

            # Sum the columns if they exist, otherwise treat as 0
            p_series = vtune_df[p_col].fillna(
                0) if p_col in vtune_df.columns else 0
            e_series = vtune_df[e_col].fillna(
                0) if e_col in vtune_df.columns else 0
            # Create the unified column (e.g., 'Retiring(%)')
            vtune_df[metric] = p_series + e_series
    else:
        logger.info("Non-hybrid CPU detected. Using standard metrics.")

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

    existing_columns = [
        col for col in required_columns_mapping.keys() if col in vtune_df.columns]

    if not existing_columns:
        logger.error(
            "Could not find any of the required columns in the report.")
        logger.info(
            f"Available columns in the report: {vtune_df.columns.tolist()}")
        return None

    transformed_df = vtune_df[existing_columns].rename(
        columns=required_columns_mapping)
    transformed_df.to_csv(converted_csv, index=False)

    logger.info(f"Transformed file saved to: {converted_csv}")

    # --- Final message ---
    time.sleep(5)
    logger.info("VTune report has been successfully transformed and saved.")
    return converted_csv
