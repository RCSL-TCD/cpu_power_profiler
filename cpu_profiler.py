import os
import sys
import argparse
import subprocess
from predictor.convert_save_command import convert_save_command, export_csv, convert_csv_format

def run_convert(args):
    print("[INFO] Running convert_save_command.py...")
    app_path = os.path.abspath(args.app)
    working_dir = os.path.dirname(app_path)
    result_dir = os.path.abspath(args.output_dir)
    report_csv = os.path.join(result_dir, "vtune_report_raw.csv")
    converted_csv = os.path.join(result_dir, "transformed_vtune_output.csv")
    headless_mode = args.headless
    app_cmd = args.app if headless_mode else None
    # Check if it is windows or Linux and set the VTune CLI path accordingly
    if sys.platform.startswith('win'):
            vtune_cli = r"C:\Program Files (x86)\Intel\oneAPI\vtune\2024.1\bin64\vtune.exe"
    elif sys.platform.startswith('linux'):
        vtune_cli = '/opt/intel/oneapi/vtune/2025.4/bin64/vtune'

    convert_save_command(result_dir, app_path, vtune_cli, working_dir, headless_mode, app_cmd)
    print(f"[INFO] VTune results will be saved in: {result_dir}")
    export_csv(result_dir, vtune_cli, report_csv)
    print(f"[INFO] Normalising VTune report: {report_csv}")
    convert_csv_format(report_csv, converted_csv)


def run_predict(mode, csv_file):
    print(f"[INFO] Running predict_power.py for mode: {mode} using file: {csv_file}")
    subprocess.run([sys.executable, "predictor/predict_power.py", "-m", mode, csv_file], check=True)

def main():
    parser = argparse.ArgumentParser(description="CPU Profiler Tool")
    parser.add_argument("-m", "--mode", choices=["avg", "min", "peak", "all"], required=True, help="Power prediction mode")
    parser.add_argument("-a", "--app", help="Path to application executable for profiling")
    parser.add_argument("-c", "--csv", help="CSV file for power prediction (optional)")
    parser.add_argument('--headless', action='store_true', help='Profile a CLI application"')
    parser.add_argument('-o', '--output-dir',
        default='vtune_results_uarch',
        help='Directory to save VTune results and generated CSVs. Default: vtune_results_uarch')

    args = parser.parse_args()

    default_csv = os.path.abspath("transformed_vtune_output.csv")

    if args.app:
        run_convert(args)
        run_predict(args.mode, default_csv)
    elif args.csv:
        run_predict(args.mode, os.path.abspath(args.csv))
    else:
        run_predict(args.mode, default_csv)

if __name__ == "__main__":
    main()
