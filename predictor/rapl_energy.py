import subprocess
import statistics
import pyRAPL


def measure_single_run(app_cmd):
    """
    Measures the energy and power of a single command execution using pyRAPL.

    Returns:
        A tuple of (energy_microjoules, power_watts) or (None, None) on failure.
    """
    pyRAPL.setup()
    meter = pyRAPL.Measurement(label="app_run")

    meter.begin()
    # Run the command. We capture output to prevent it from cluttering our
    # script's console.

    subprocess.run(app_cmd, shell=True, check=True,
                   capture_output=True, text=True)
    meter.end()

    result = meter.result

    # Check if the measurement was successful
    if not result or not result.pkg:
        print("[WARN] pyRAPL measurement failed for this run.")
        return None, None

    # Sum energy from all CPU sockets (for multi-socket systems)
    total_pkg_energy = sum(result.pkg)
    duration_sec = result.duration / 1_000_000  # Duration is in microseconds

    # Calculate average power in Watts (Joules/second)
    # Power = (Energy in µJ / 1,000,000) / Duration in sec
    power_watts = (total_pkg_energy / 1_000_000) / \
        duration_sec if duration_sec > 0 else 0

    return total_pkg_energy, power_watts


def measure_energy_stats(app_cmd, num_runs=5):
    """
    Runs a command multiple times to measure and calculate statistics
    for its energy and power consumption.

    Returns:
        A dictionary with min, max, and average for energy (µJ) and power (W).
    """
    print(f"\n[INFO] Starting RAPL energy measurement for {num_runs} runs...")

    energies = []
    powers = []

    for i in range(num_runs):
        print(f"[INFO] RAPL measurement run {i+1}/{num_runs}...")
        energy, power = measure_single_run(app_cmd)

        if energy is not None and power is not None:
            energies.append(energy)
            powers.append(power)
        else:
            # Allow the function to continue even if one run fails
            continue

    if not energies:
        print("[ERROR] All RAPL measurements failed. Unable to calculate stats.")
        return None

    stats = {
        'avg_energy_uj': statistics.mean(energies),
        'min_energy_uj': min(energies),
        'max_energy_uj': max(energies),
        'avg_power_w': statistics.mean(powers),
        'min_power_w': min(powers),
        'max_power_w': max(powers),
        'successful_runs': len(energies)
    }

    return stats
