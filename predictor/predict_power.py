import sys
import os
import argparse
import joblib
from predictor.l2_extractor import process_file


def predict_power(csv_file, mode, logger):
    model_files = {
        'avg': ('cpu_power_model_avg.joblib', 'AVG'),
        'min': ('cpu_power_model_min.joblib', 'MIN'),
        'peak': ('cpu_power_model_peak.joblib', 'PEAK')
    }

    l2_df = process_file(csv_file, 1)
    selected_features = [
    'CPU Time',
    'Clockticks',
    'Instructions Retired',
    'CPI Rate',
    'Retiring',
    'Front-End Bound',
    'Bad Speculation',
    'Back-End Bound',
    'Average CPU Frequency'
]

    features = l2_df[selected_features]
    prediction_result = {}

    if mode == 'all':
        for key, (model_file, label) in model_files.items():
            model_path = os.path.join(os.path.dirname(__file__), model_file)
            model = joblib.load(model_path)
            prediction = model.predict(features)[0]
            prediction_result[label] = prediction
            logger.info(f"🔋 Predicted {label} Power: {prediction:.2f} watts")
    elif mode in model_files:
        model_file, label = model_files[mode]
        model_path = os.path.join(os.path.dirname(__file__), model_file)
        model = joblib.load(model_path)
        prediction = model.predict(features)[0]
        prediction_result = {label: prediction}
        logger.info(f"🔋 Predicted {label} Power: {prediction:.2f} watts")
    else:
        logger.error("Invalid mode. Choose from: avg, min, peak, all.")
    return prediction_result


def main():
    parser = argparse.ArgumentParser(
        description='Predict CPU Power Consumption')
    parser.add_argument(
        '-m', '--mode', choices=['avg', 'min', 'peak', 'all'], required=True, help='Power prediction mode')
    parser.add_argument('csv_file', help='Input CSV file with CPU metrics')
    args = parser.parse_args()

    predict_power(args.csv_file, args.mode)


if __name__ == '__main__':
    main()
