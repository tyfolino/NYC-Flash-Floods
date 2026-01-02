import os

import cdsapi

years = list(range(1996, 2025))
dataset = "reanalysis-era5-single-levels"

# Output directory
outdir = "/mnt/drive2/ERA5/NC_files/mslp"
os.makedirs(outdir, exist_ok=True)

client = cdsapi.Client()


for year in years:
    print(f"Downloading data for year {year}...")
    request = {
        "product_type": ["reanalysis"],
        "variable": ["mean_sea_level_pressure"],
        "year": str(year),
        "month": ["05", "06", "07", "08", "09", "10"],
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
        "area": [90, -180, 0, 0],
    }

    outfile = os.path.join(outdir, f"era5_mslp_NWHem_{year}.nc")

    client.retrieve(dataset, request).download(outfile)
