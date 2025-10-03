import requests

# Define region and time (adjust as needed)
lat_min, lat_max = -10, 10
lon_min, lon_max = 100, 120
start_time = "2020-01-01T00:00:00Z"
end_time   = "2025-09-10T00:00:00Z"

# Build URL
url = (
    "https://harmony.earthdata.nasa.gov/C3309442935-POCLOUD/ogc-api-coverages/1.0.0/collections/all/coverage/rangeset"
    f"?subset=lat({lat_min}:{lat_max})"
    f"&subset=lon({lon_min}:{lon_max})"
    f"&subset=time({start_time}:{end_time})"
    "&format=application/x-netcdf4"
)

# Download
out_file = "SSH_subset.nc"
session = requests.Session()
session.auth = ('sogu7', '@aA123B45C6D7E8')  # you need Earthdata login
resp = session.get(url, stream=True)

with open(out_file, "wb") as f:
    for chunk in resp.iter_content(chunk_size=8192):
        f.write(chunk)

print(f"Downloaded: {out_file}")
