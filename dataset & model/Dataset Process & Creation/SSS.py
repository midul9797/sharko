import os
import subprocess

# Output directory
out_dir = "./data_sss"
os.makedirs(out_dir, exist_ok=True)

# Dataset ID from PO.DAAC
collection = "SMAP_RSS_L3_SSS_SMI_8DAY-RUNNINGMEAN_V5"

# Time range (Note: The end date is in the future)
start_date = "2020-01-01T00:00:00Z"
end_date = "2025-09-10T23:59:59Z"

# Bounding box (lonW, latS, lonE, latN)
lonW, latS, lonE, latN = -180, -90, 180, 90  # Global coverage

# Build podaac-data-downloader command
cmd = [
    "podaac-data-downloader",
    "-c", collection,
    "-d", out_dir,
    "--start-date", start_date,
    "--end-date", end_date,
    "-b", str(lonW), str(latS), str(lonE), str(latN),  # Separate bbox values
    "-e", ".nc"  # Specify the file extension
]

# --- DEBUGGING STEP ---
# Print the command list to see exactly what is being run
print("DEBUG - Command list being executed:", cmd)
print("-" * 30)

# Running the command and handling errors
try:
    print("Running command:", " ".join(cmd))
    result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    print("Command output:", result.stdout)
except subprocess.CalledProcessError as e:
    print(f"Error running command: {e}")
    print(f"Standard Output:\n{e.stdout}")
    print(f"Standard Error:\n{e.stderr}")
