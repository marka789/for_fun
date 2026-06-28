"""Configuration for covariance / PCA / RMT analysis."""

from pathlib import Path

# Analysis window
START_DATE = "2020-01-01"
END_DATE = None  # None => through latest available trading day

# Paths
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"

# Universe labels
SP500_LABEL = "sp500"
NASDAQ100_LABEL = "nasdaq100"

# RMT / PCA
N_BINS_EIGENVALUE_HIST = 100
MP_GRID_POINTS = 500
