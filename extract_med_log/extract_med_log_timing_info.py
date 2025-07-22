import argparse
import re
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import sys

def extract_log_to_df(log_file_path: str):
    with open(log_file_path, "r") as f:
        log_content = f.read()

    pattern = re.compile(
        r"Model Date:\s+([0-9T:-]+)\s+wall clock =\s+([0-9T:-]+)\s+avg dt =\s+([\d.]+)\s+s/day,"
        r"\s+dt =\s+([\d.]+)\s+s/day,\s+rate =\s+([\d.]+)\s+ypd"
    )

    records = []
    for line in log_content.splitlines():
        match = pattern.search(line)
        if match:
            model_date, wall_clock, avg_dt, dt, rate = match.groups()
            records.append({
                "Model Date": datetime.strptime(model_date, "%Y-%m-%dT%H:%M:%S"),
                "Rate (ypd)": float(rate),
            })

    if not records:
        print(f"No valid records found in: {log_file_path}")
        return None

    df = pd.DataFrame(records)
    return df

def plot_multiple_logs(log_paths, figure_path):
    plt.figure(figsize=(12, 6))

    for log_path in log_paths:
        abs_path = os.path.abspath(log_path)
        df = extract_log_to_df(log_path)
        if df is None:
            continue
        plt.plot(df["Model Date"], df["Rate (ypd)"], marker="o", linestyle="-", label=abs_path)

    if not plt.gca().has_data():
        print("No valid data found in any provided logs.")
        sys.exit(1)

    plt.title("Simulation Rate Over Model Time")
    plt.xlabel("Model Date")
    plt.ylabel("Rate (years per day)")
    plt.legend(fontsize=8)
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(figure_path)
    plt.close()
    print(f"Plot saved to {figure_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot simulation rate from multiple logs.")
    parser.add_argument("log_files", nargs="+", help="One or more log files")
    parser.add_argument("figure_path", help="Path to save the output figure")
    args = parser.parse_args()

    plot_multiple_logs(args.log_files, args.figure_path)