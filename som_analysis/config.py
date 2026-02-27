"""
Shared configuration for the NYC flash flood SOM analysis.

Centralises moisture-variable metadata, path builders, and constants
used by train_som.py, plot_som.py, and node_statistics.py.
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import scienceplots  # noqa: F401

# ── Shared paths ──────────────────────────────────────────────────────────────

SOM_INTERMEDIATE_PATH = "/mnt/drive2/SOM_intermediate_files/"
STAGEIV_NC = "/mnt/drive2/StageIV/stageiv_tristate_hourly.nc"
ERA5_TP_DIR = "/mnt/drive2/ERA5/NC_files/tp"

# Relative to the project root (one level up from this file)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRECIP_DATA_DIR = os.path.join(_PROJECT_ROOT, "precip_data_and_tc_association_code")
IBTRACS_PATH = os.path.join(
    PRECIP_DATA_DIR, "ibtracs.NA.list.v04r01.processed_6hrly.statslp3.csv"
)
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
FIGS_DIR = os.path.join(_PROJECT_ROOT, "figs")

# ── Station coordinates (for ASOS precipitation) ─────────────────────────────

STATION_COORDS = {
    "JFK": (40.6413, -73.7781),
    "LGA": (40.7769, -73.8740),
    "Central Park": (40.7829, -73.9654),
    "EWR": (40.6895, -74.1745),
}

STATION_NPY_FILES = {
    "JFK": os.path.join(PRECIP_DATA_DIR, "jfk7_14_25.npy"),
    "LGA": os.path.join(PRECIP_DATA_DIR, "lga7_14_25.npy"),
    "Central Park": os.path.join(PRECIP_DATA_DIR, "cp7_14_25.npy"),
    "EWR": os.path.join(PRECIP_DATA_DIR, "zewr_14_25.npy"),
}

# ── Moisture-variable configuration ──────────────────────────────────────────

MOISTURE_CONFIGS = {
    "IVT": dict(
        file_prefix="era5_ivt",
        var_name="ivt",
        time_dim="valid_time",
        lat_dim="latitude",
        lon_dim="longitude",
        label="|IVT|",
        label_short="IVT",
        file_label="ivt",
        units_raw=r"kg m$^{-1}$ s$^{-1}$",
        fig_subdir="Z500-and-ivt-SOM",
        levels_weights=np.arange(-1.8, 1.81, 0.2),
        levels_anom=np.arange(-2.5, 2.6, 0.5),
        levels_raw=np.arange(0, 701, 100),
        levels_indiv=np.arange(0, 1001, 100),
        cmap_raw="BuPu",
    ),
    "tcwv": dict(
        file_prefix="era5_tcwv",
        var_name="tcwv",
        time_dim="time",
        lat_dim="lat",
        lon_dim="lon",
        label="TCWV",
        label_short="TCWV",
        file_label="tcwv",
        units_raw=r"kg m$^{-2}$",
        fig_subdir="Z500-and-tcwv-SOM",
        levels_weights=np.arange(-1.8, 1.81, 0.2),
        levels_anom=np.arange(-2.5, 2.6, 0.5),
        levels_raw=np.arange(20, 56, 5),
        levels_indiv=np.arange(10, 71, 5),
        cmap_raw="BuPu",
    ),
    "thetae": dict(
        file_prefix="era5_thetae",
        var_name="theta_e",
        time_dim="valid_time",
        lat_dim="latitude",
        lon_dim="longitude",
        label=r"850-hPa $\theta_e$",
        label_short=r"$\theta_e$",
        file_label="theta_e",
        units_raw="K",
        fig_subdir="Z500-and-thetae-SOM",
        levels_weights=np.arange(-1.8, 1.81, 0.2),
        levels_anom=np.arange(-2.5, 2.6, 0.5),
        levels_raw=np.arange(285, 341, 5),
        levels_indiv=np.arange(270, 381, 10),
        cmap_raw="BuPu",
    ),
}


def get_paths(moisture_var, moisture_weight=1):
    """Build output paths for a given moisture variable and weight.

    Returns a dict with keys: fig_dir, bmu_csv_path, file_label.
    """
    cfg = MOISTURE_CONFIGS[moisture_var]
    file_label = cfg["file_label"]

    # Weight prefix (empty when weight == 1)
    if moisture_weight == 1:
        w_prefix = ""
    elif moisture_weight == int(moisture_weight):
        w_prefix = str(int(moisture_weight))
    else:
        w_prefix = str(moisture_weight)

    if w_prefix == "":
        fig_dir = os.path.join(FIGS_DIR, cfg["fig_subdir"])
        bmu_csv = os.path.join(DATA_DIR, f"som_2x2_bmus_{moisture_var}.csv")
    else:
        fig_dir = os.path.join(
            FIGS_DIR, f"Z500-and-{w_prefix}{moisture_var.lower()}-SOM"
        )
        bmu_csv = os.path.join(DATA_DIR, f"som_2x2_bmus_{w_prefix}{moisture_var}.csv")

    return {
        "fig_dir": fig_dir,
        "bmu_csv_path": bmu_csv,
        "file_label": file_label,
    }


def setup_plotting():
    """Apply the shared matplotlib style."""
    plt.style.use(["science", "nature", "grid"])
    plt.rcParams["text.usetex"] = True
