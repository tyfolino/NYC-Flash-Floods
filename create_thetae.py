"""
Theta-e Production Script
By: Ty Janoski
Updated: 2/20/26
"""

import os

import metpy.calc as mpcalc
import xarray as xr
from metpy.units import units

# Read in data
path = "/mnt/drive2/ERA5/NC_files/thetae"
out_dir = "/mnt/drive2/ERA5/NC_files/hourly_sliced"

for filename in os.listdir(path):
    if filename.endswith(".nc"):
        out_path = os.path.join(out_dir, filename)

        # Skip if already exists
        if os.path.exists(out_path):
            print(f"Skipping {filename} (already exists)")
            continue

        print(f"Processing {filename}...")

        # Open the dataset
        ds = xr.open_dataset(os.path.join(path, filename)).sel(
            latitude=slice(54, 30), longitude=slice(-100, -60)
        )

        # Extract necessary variables
        t = ds["t"].metpy.quantify()
        q = ds["q"].metpy.quantify()
        p = ds["pressure_level"].metpy.quantify() * units.hPa

        # Calculate dewpoint from specific humidity
        dewpoint = mpcalc.dewpoint_from_specific_humidity(p, t, q)

        # Calculate theta-e
        theta_e = mpcalc.equivalent_potential_temperature(p, t, dewpoint)

        # Create new dataset with theta-e
        theta_e_ds = xr.Dataset(
            {
                "theta_e": (
                    ("valid_time", "latitude", "longitude"),
                    theta_e.squeeze().metpy.magnitude,
                )
            },
            coords={
                "valid_time": ds["valid_time"],
                "latitude": ds["latitude"],
                "longitude": ds["longitude"],
            },
        )
        theta_e_ds["theta_e"].attrs["units"] = str(theta_e.metpy.units)

        theta_e_ds.to_netcdf(out_path)
        print(f"Saved {filename}")
