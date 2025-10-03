import os
import requests
import pandas as pd
from netrc import netrc
import time

# ==============================================================================
# STEP 1: CONFIGURATION
# ==============================================================================
# --- Configure your file paths and settings here ---

# Save data to a new folder to keep it separate from the old daily data
DATA_DIR = "sst_data_8day"
os.makedirs(DATA_DIR, exist_ok=True)

MISSING_LOG = os.path.join(DATA_DIR, "missing_files.txt")

# --- DATE RANGE FOR 8-DAY COMPOSITES ---
# Define the overall start and end of your analysis period
overall_start_date = pd.to_datetime("2020-01-01")
overall_end_date = pd.to_datetime("2025-06-30")

BASE_URL = "https://oceandata.sci.gsfc.nasa.gov/ob/getfile/"

# --- AUTHENTICATION ---
# Read credentials from ~/.netrc file in your home directory
try:
    auth = netrc().authenticators("urs.earthdata.nasa.gov")
    USERNAME, _, PASSWORD = auth
    print("✅ Successfully loaded Earthdata credentials from ~/.netrc file.")
except (FileNotFoundError, TypeError):
    print("❌ ERROR: Could not find or read the ~/.netrc file.")
    print("   Please ensure the file exists and is formatted correctly with your Earthdata login.")
    exit()

session = requests.Session()
session.auth = (USERNAME, PASSWORD)

# ==============================================================================
# STEP 2: DOWNLOAD FUNCTION
# ==============================================================================
def download_nc_file(start_date, retries=3):
    """
    Downloads a single 8-day composite NetCDF file for a given start date.
    """
    # 1. Calculate the end date of the 8-day period
    end_date = start_date + pd.Timedelta(days=7)

    # If the calculated end date is in the next year, cap it at Dec 31st of the start year.
    if end_date.year > start_date.year:
        end_date = pd.Timestamp(f"{start_date.year}-12-31")

    # 2. Format both dates as YYYYMMDD strings
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')

    # 3. Construct the correct filename for 8-Day SST data
    fname = f"AQUA_MODIS.{start_date_str}_{end_date_str}.L3m.8D.SST.sst.4km.nc"
    
    url = BASE_URL + fname
    save_path = os.path.join(DATA_DIR, fname)

    # Check if a valid file already exists
    if os.path.exists(save_path) and os.path.getsize(save_path) > 10000:
        print(f"✅ Already exists and is valid: {fname}")
        return save_path

    # Attempt to download the file with retries
    for attempt in range(1, retries + 1):
        print(f"⬇️  Downloading {fname} (attempt {attempt}) ...")
        try:
            r = session.get(url, stream=True, timeout=90)

            content_type = r.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                print(f"❌ ERROR: Received an HTML page for {fname}. Filename may be incorrect.")
                return None

            if r.status_code == 200:
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                
                if os.path.getsize(save_path) > 10000:
                    print(f"✅ Download complete: {fname}")
                    return save_path
                else:
                    print(f"❌ ERROR: Downloaded file for {fname} is too small. Deleting.")
                    os.remove(save_path)
                    return None

            elif r.status_code == 404:
                print(f"⚠️ File not found on server: {fname} (skipping)")
                with open(MISSING_LOG, "a") as log:
                    log.write(f"{fname} (404 Not Found)\n")
                return None

            else:
                print(f"⚠️ Failed: {fname} | Status {r.status_code} | Reason: {r.reason}")

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Network error for {fname}: {e}")

        time.sleep(5)

    print(f"❌ All download attempts failed for {fname}")
    with open(MISSING_LOG, "a") as log:
        log.write(f"{fname} (Max retries reached)\n")
    return None

# ==============================================================================
# STEP 3: MAIN DOWNLOAD LOOP (CORRECTED DATE GENERATION)
# ==============================================================================

# --- Robustly generate the list of start dates for each 8-day period ---
print("-> Generating correct list of 8-day period start dates...")
all_start_dates = []
for year in range(overall_start_date.year, overall_end_date.year + 1):
    # For each year, generate the sequence of 8-day periods starting from Jan 1st
    year_dates = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="8D")
    all_start_dates.extend(year_dates)

# Filter the complete list to only include periods within our overall date range
dates_to_download = [
    d for d in all_start_dates 
    if d >= overall_start_date and d <= overall_end_date
]
print(f"   Generated {len(dates_to_download)} periods to download.")


print(f"\n--- Starting Download Process for {len(dates_to_download)} 8-Day Periods ---")
nc_files = []
for i, d in enumerate(dates_to_download, start=1):
    print(f"\n--- Processing Period {i}/{len(dates_to_download)}: Starting {d.date()} ---")
    file_path = download_nc_file(d)
    if file_path:
        nc_files.append(file_path)

print("\n\n✅ All downloads processed!")
print(f"Successfully downloaded: {len(nc_files)} files.")
print(f"Data saved to the '{DATA_DIR}' folder.")
if len(nc_files) < len(dates_to_download):
    print(f"Any missing or failed files have been logged to: {MISSING_LOG}")
