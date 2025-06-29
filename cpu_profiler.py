import os
import sys
import argparse
from predictor.convert_save_command import convert_save_command, export_csv, convert_csv_format
from predictor.predict_power import predict_power
from predictor.rapl_energy import measure_energy_stats
from loguru import logger
import datetime


logger.remove()
log_level = "DEBUG"
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level}</level> | "
    "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)
logger.add(
    sys.stderr,
    level=log_level,
    format=log_format,
    colorize=True,
    backtrace=True,
    diagnose=True,
)


def run_convert(args, logger):
    logger.info("Starting convert_save_command.py with arguments: {}", args)
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

    convert_save_command(result_dir, app_path, vtune_cli,
                         working_dir, headless_mode, app_cmd, logger)
    logger.info(
        f"VTune profiling completed, exporting results to CSV: {result_dir}")
#    print(f"[INFO] VTune results will be saved in: {result_dir}")
    export_csv(result_dir, vtune_cli, report_csv, logger)
    logger.info(f"VTune report exported to CSV: {report_csv}")
    # print(f"[INFO] Normalising VTune report: {report_csv}")
    converted_csv_path = convert_csv_format(report_csv, converted_csv, logger)
    return converted_csv_path


def run_predict(csv_file, mode, logger):
    print(
        f"[INFO] Running predict_power.py for mode: {mode} using file: {csv_file}")
    logger.info(
        "Running predict_power.py for mode: {} using file: {}", mode, csv_file)
    prediction_result = predict_power(csv_file, mode, logger)
    return prediction_result
#    subprocess.run([sys.executable, "predictor/predict_power.py", "-m", mode, csv_file], check=True)


def main():
    parser = argparse.ArgumentParser(description="CPU Profiler Tool")
    parser.add_argument(
        "-m", "--mode", choices=["avg", "min", "peak", "all"], required=True, help="Power prediction mode")
    parser.add_argument(
        "-a", "--app", help="Path to application executable for profiling")
    parser.add_argument(
        "-c", "--csv", help="CSV file for power prediction (optional)")
    parser.add_argument('--headless', action='store_true',
                        help='Profile a CLI application"')
    parser.add_argument('-o', '--output-dir',
                        default='vtune_results_uarch',
                        help='Directory to save VTune results and generated CSVs. Default: vtune_results_uarch')
    parser.add_argument('--rapl', action='store_true',
                        help='Measure energy statistics using pyRAPL')
    parser.add_argument('--log-level', default='INFO',
                        help='Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')

    args = parser.parse_args()

    default_csv = os.path.abspath("transformed_vtune_output.csv")

    if args.app:
        converted_csv_path = run_convert(args, logger)
        prediction_result = run_predict(converted_csv_path, args.mode, logger)
        logger.info("Prediction results: {}", prediction_result)
    elif args.csv:
        # run_predict(args.mode, os.path.abspath(args.csv))
        prediction_result = run_predict(
            os.path.abspath(args.csv), args.mode, logger)
        logger.info("Prediction results: {}", prediction_result)
    else:
        run_predict(args.mode, default_csv)

    # Measure energy statistics with pyRAPL
    if args.rapl:
        energy_results = measure_energy_stats(args.app, num_runs=5)
        if energy_results:
            print("\n--- RAPL Energy Analysis Results ---")
            print(
                f"Statistics from {energy_results['successful_runs']} successful runs:")
            print(f"  Energy (Package):")
            print(f"    - Average: {energy_results['avg_energy_uj']:,.2f} µJ")
            print(f"    - Min:     {energy_results['min_energy_uj']:,.2f} µJ")
            print(f"    - Max:     {energy_results['max_energy_uj']:,.2f} µJ")
            print(f"  Power (Package):")
            print(f"    - Average: {energy_results['avg_power_w']:.2f} W")
            print(f"    - Min:     {energy_results['min_power_w']:.2f} W")
            print(f"    - Max:     {energy_results['max_power_w']:.2f} W")
            print("------------------------------------")

    # Save results to a CSV file in the output directory
    now = datetime.datetime.now()
    date_and_time = now.isoformat()
    full_csv_path = os.path.join(args.output_dir, "full_results.csv")
    with open(full_csv_path, 'w', newline='') as csvfile:
        import csv
        fieldnames = [
            'date_and_time', 'ml_power_avg', 'ml_power_min', 'ml_power_peak',
            'rapl_energy_uj_avg', 'rapl_energy_uj_min', 'rapl_energy_uj_max',
            'rapl_power_avg', 'rapl_power_min', 'rapl_power_peak', "cli_app_command"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({
            'date_and_time': date_and_time,
            'ml_power_avg': prediction_result.get('AVG', None),
            'ml_power_min': prediction_result.get('MIN', None),
            'ml_power_peak': prediction_result.get('PEAK', None),
            'rapl_energy_uj_avg': energy_results['avg_energy_uj'] if args.rapl else None,
            'rapl_energy_uj_min': energy_results['min_energy_uj'] if args.rapl else None,
            'rapl_energy_uj_max': energy_results['max_energy_uj'] if args.rapl else None,
            'rapl_power_avg': energy_results['avg_power_w'] if args.rapl else None,
            'rapl_power_min': energy_results['min_power_w'] if args.rapl else None,
            'rapl_power_peak': energy_results['max_power_w'] if args.rapl else None,
            "cli_app_command": args.app if args.app else "N/A"
        })


if __name__ == "__main__":
    main()
