import os

import cdsapi

client = cdsapi.Client()

dataset = "reanalysis-era5-single-levels"

years = [
    "1996", "1997", "1998", "1999", "2000", "2001",
    "2002", "2003", "2004", "2005", "2006", "2007",
    "2008", "2009", "2010", "2011", "2012", "2013",
    "2014", "2015", "2016", "2017", "2018", "2019",
    "2020", "2021", "2022", "2023", "2024"
]
months = ["05", "06", "07", "08", "09", "10"]
days = [f"{d:02d}" for d in range(1, 32)]

time_blocks = [
    ["00:00", "06:00", "12:00", "18:00"],
    ["01:00", "07:00", "13:00", "19:00"],
    ["02:00", "08:00", "14:00", "20:00"],  # Block 3
    ["03:00", "09:00", "15:00", "21:00"],  # Block 4
    ["04:00", "10:00", "16:00", "22:00"],  # Block 5
    ["05:00", "11:00", "17:00", "23:00"],  # Block 6
]

out_dir = "/mnt/drive2/ERA5/GRIB_files"
os.makedirs(out_dir, exist_ok=True)

for block in time_blocks:
    request = {
        "product_type": ["reanalysis"],
        "variable": ["total_column_water_vapour"],
        "year": years,
        "month": months,
        "day": days,
        "time": block,
#        "pressure_level": ["500"],
        "data_format": "grib",
        "download_format": "unarchived"
    }

    # Generate filename, e.g. era5_z500_02081420.grib
    hours = "".join([t[:2] for t in block])
    out_file = os.path.join(out_dir, f"era5_pw_{hours}.grib")

    print(f"Requesting {block} → {out_file}")
    client.retrieve(dataset, request).download(out_file)

print("Remaining downloads complete.")
