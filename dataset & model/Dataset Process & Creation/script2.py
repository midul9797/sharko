import os
import requests
import pandas as pd
from netrc import netrc
import time

# -----------------------
# CONFIGURATION
# -----------------------
DATA_DIR = "chlorophyll_data"
os.makedirs(DATA_DIR, exist_ok=True)

MISSING_LOG = os.path.join(DATA_DIR, "missing_files.txt")

# Test with a short range first
dates = pd.date_range("2024-01-01", "2025-09-10", freq="W-FRI")  

BASE_URL = "https://oceandata.sci.gsfc.nasa.gov/ob/getfile/"

# Read credentials from ~/.netrc
auth = netrc().authenticators("urs.earthdata.nasa.gov")
USERNAME, ACCOUNT, PASSWORD = auth

session = requests.Session()
session.auth = (USERNAME, PASSWORD)

# -----------------------
# DOWNLOAD FUNCTION
# -----------------------
def download_nc_file(date, retries=3):
    fname = f"AQUA_MODIS.{date.strftime('%Y%m%d')}.L3m.DAY.CHL.chlor_a.4km.nc"
    url = BASE_URL + fname
    save_path = os.path.join(DATA_DIR, fname)

    if os.path.exists(save_path):
        print(f"✅ Already exists: {fname}")
        return save_path

    for attempt in range(1, retries + 1):
        print(f"⬇️  Downloading {fname} (attempt {attempt}) ...")
        try:
            r = session.get(url, stream=True, timeout=60)
            if r.status_code == 200:
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print(f"✅ Download complete: {fname}")
                return save_path
            elif r.status_code == 404:
                print(f"⚠️ File not found: {fname} (skipping)")
                with open(MISSING_LOG, "a") as log:
                    log.write(f"{fname}\n")
                return None
            else:
                print(f"⚠️ Failed: {fname} | Status {r.status_code} | Type {r.headers.get('Content-Type')}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Network error for {fname}: {e}")

        time.sleep(5)  # wait before retry

    print(f"❌ All attempts failed for {fname}")
    with open(MISSING_LOG, "a") as log:
        log.write(f"{fname} (network/error)\n")
    return None

# -----------------------
# DOWNLOAD LOOP
# -----------------------
nc_files = []
for i, d in enumerate(dates, start=1):
    print(f"\n--- Processing {i}/{len(dates)}: {d.date()} ---")
    file_path = download_nc_file(d)
    if file_path:
        nc_files.append(file_path)

print("\n✅ All downloads processed")
print(f"Missing files logged to {MISSING_LOG}")
