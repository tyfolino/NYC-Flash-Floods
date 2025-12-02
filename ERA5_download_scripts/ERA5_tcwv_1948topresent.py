import os

import cdsapi

dataset = "reanalysis-era5-single-levels"

# Base request template (month/day/time list covers full month)
request = {
    "product_type": ["reanalysis"],
    # 'year' will be set per-iteration below
    "month": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"],
    "day": [
        "01",
        "02",
        "03",
        "04",
        "05",
        "06",
        "07",
        "08",
        "09",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "20",
        "21",
        "22",
        "23",
        "24",
        "25",
        "26",
        "27",
        "28",
        "29",
        "30",
        "31",
    ],
    "time": [
        "00:00",
        "01:00",
        "02:00",
        "03:00",
        "04:00",
        "05:00",
        "06:00",
        "07:00",
        "08:00",
        "09:00",
        "10:00",
        "11:00",
        "12:00",
        "13:00",
        "14:00",
        "15:00",
        "16:00",
        "17:00",
        "18:00",
        "19:00",
        "20:00",
        "21:00",
        "22:00",
        "23:00",
    ],
    "data_format": "netcdf",
    "download_format": "unarchived",
    "variable": ["total_column_water_vapour"],
}

client = cdsapi.Client()

# Output directory for yearly files
out_dir = "/mnt/drive2/ERA5/tcwv"
os.makedirs(out_dir, exist_ok=True)

# Loop years 1948..2024 inclusive and download each year to a separate NetCDF
for year in range(1948, 2025):
    year_str = str(year)
    request["year"] = [year_str]
    out_file = os.path.join(out_dir, f"era5_tcwv_{year_str}.nc")
    if os.path.exists(out_file):
        print(f"Skipping existing file: {out_file}")
        continue

    print(f"Requesting total_column_water_vapour for year {year_str} -> {out_file}")
    try:
        client.retrieve(dataset, request).download(out_file)
    except Exception as e:
        print(f"Download failed for {year_str}: {e}")
