import os
import sys
import argparse
import subprocess

def run_convert(app_path):
    print("[INFO] Running convert_save_command.py...")
    subprocess.run([sys.executable, "predictor/convert_save_command.py", "-a", app_path], check=True)

def run_predict(mode, csv_file):
    print(f"[INFO] Running predict_power.py for mode: {mode} using file: {csv_file}")
    subprocess.run([sys.executable, "predictor/predict_power.py", "-m", mode, csv_file], check=True)

def main():
    parser = argparse.ArgumentParser(description="CPU Profiler Tool")
    parser.add_argument("-m", "--mode", choices=["avg", "min", "peak", "all"], required=True, help="Power prediction mode")
    parser.add_argument("-a", "--app", help="Path to application executable for profiling")
    parser.add_argument("-c", "--csv", help="CSV file for power prediction (optional)")
    args = parser.parse_args()

    default_csv = os.path.abspath("transformed_vtune_output.csv")

    if args.app:
        run_convert(args.app)
        run_predict(args.mode, default_csv)
    elif args.csv:
        run_predict(args.mode, os.path.abspath(args.csv))
    else:
        run_predict(args.mode, default_csv)

if __name__ == "__main__":
    main()
