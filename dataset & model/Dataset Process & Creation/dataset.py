import os
import requests
import xarray as xr
import pandas as pd

# -----------------------
# CONFIGURATION
# -----------------------
# Folder to store NetCDF files
DATA_DIR = "satellite_data"
os.makedirs(DATA_DIR, exist_ok=True)

# Example: Daily files for Jan 2020 (you can extend this)
dates = pd.date_range("2023-06-24", "2025-09-10", freq="D")

# NASA OceanColor base URL (MODIS Aqua Chlorophyll-a, 4km, daily L3m)
BASE_URL = "https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/"

# -----------------------
# DOWNLOAD FILES
# -----------------------
def download_nc_file(date):
    fname = f"AQUA_MODIS.{date.strftime('%Y%m%d')}.L3m.DAY.CHL.chlor_a.4km.nc"
    url = BASE_URL + fname
    save_path = os.path.join(DATA_DIR, fname)
    
    if not os.path.exists(save_path):
        print(f"Downloading {fname} ...")
        r = requests.get(url)
        if r.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(r.content)
        else:
            print(f"⚠️ Could not download {fname} (status {r.status_code})")
    else:
        print(f"Already exists: {fname}")
    return save_path

nc_files = [download_nc_file(d) for d in dates]

# -----------------------
# BUILD DATASET
# -----------------------
all_data = []

for file in nc_files:
    try:
        ds = xr.open_dataset(file)
        chl = ds['chlor_a']
        lat = ds['lat'].values
        lon = ds['lon'].values
        chl_data = chl.values

        # Flatten into rows
        for i in range(len(lat)):
            for j in range(len(lon)):
                all_data.append([
                    file.split(".")[1],   # date string
                    lat[i],
                    lon[j],
                    chl_data[i, j]
                ])
    except Exception as e:
        print(f"⚠️ Skipping {file}: {e}")

# Convert to dataframe
df = pd.DataFrame(all_data, columns=["date", "lat", "lon", "chlor_a"])

# Save to CSV
df.to_csv("shark_habitat_dataset.csv", index=False)
print("✅ Dataset saved as shark_habitat_dataset.csv")
