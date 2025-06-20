from setuptools import setup, find_packages

setup(
    name='cpu_power_predictor',
    version='1.1',
    py_modules=["cpu_profiler"],  # Ensures cpu_profiler.py is installed as a module
    packages=find_packages(),
    install_requires=['pandas', 'scikit-learn', 'joblib', 'openpyxl'],
    include_package_data=True,
    package_data={
        'predictor': [
            'cpu_power_model_min.joblib',
            'cpu_power_model_avg.joblib',
            'cpu_power_model_peak.joblib',
        ],
    },
    entry_points={
        'console_scripts': [
            'power_predict=predictor.predict_power:main',
            'cpu_profiler=cpu_profiler:main',
        ],
    },
    description='Predict CPU power consumption (min, avg, peak) from performance metrics',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://yourprojecthomepage.example.com',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
