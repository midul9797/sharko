# cmr_monthly_sss_downloader.py
import os
import time
import math
import json
import requests
import pandas as pd
from netrc import netrc
from datetime import datetime
from dateutil.relativedelta import relativedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# -------- CONFIG --------
SHORT_NAME = "SMAP_RSS_L3_SSS_SMI_8DAY-RUNNINGMEAN_V5"  # adjust if you use V6
PROVIDER = "POCLOUD"
START = "2024-01-01T00:00:00Z"
END   = "2025-09-10T23:59:59Z"
DOWNLOAD_DIR = "data_sss"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

CMR_GRANULES = "https://cmr.earthdata.nasa.gov/search/granules.json"
OUT_INDEX = "granules_index.csv"   # will store href, granule_id, time_start, time_end, local_path

# -------- session with retries/backoff --------
def make_session(user=None, pwd=None):
    sess = requests.Session()
    retries = Retry(total=6, backoff_factor=1.0,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["GET", "POST"])
    adapter = HTTPAdapter(max_retries=retries)
    sess.mount("https://", adapter)
    sess.mount("http://", adapter)
    sess.headers.update({"User-Agent": "Sharko-SSS-Downloader/1.0"})
    if user and pwd:
        sess.auth = (user, pwd)
    return sess

# load credentials from .netrc if present
try:
    auth = netrc().authenticators("urs.earthdata.nasa.gov")
    if auth:
        USER, _, PWD = auth
    else:
        USER = PWD = None
except Exception:
    USER = PWD = None

session = make_session(USER, PWD)

# -------- helper: generate monthly windows --------
def month_windows(start_iso, end_iso):
    start = pd.to_datetime(start_iso)
    end = pd.to_datetime(end_iso)
    windows = []
    cur = start.replace(day=1)
    while cur <= end:
        next_month = cur + relativedelta(months=1)
        # define ISO strings with Z
        s = cur.strftime("%Y-%m-%dT00:00:00Z")
        e = (next_month - pd.Timedelta(seconds=1)).strftime("%Y-%m-%dT23:59:59Z")
        if pd.to_datetime(e) > pd.to_datetime(end_iso):
            e = pd.to_datetime(end_iso).strftime("%Y-%m-%dT%H:%M:%SZ")
        windows.append((s, e))
        cur = next_month
    return windows

# -------- fetch granules for a single temporal window (with pagination) --------
def fetch_granules_for_window(short_name, start, end, provider=PROVIDER, page_size=200):
    found = []
    page_num = 1
    print(f"  Querying CMR: {start} -> {end}")
    while True:
        params = {
            "short_name": short_name,
            "temporal": f"{start},{end}",
            "provider": provider,
            "page_size": page_size,
            "page_num": page_num
        }
        try:
            r = session.get(CMR_GRANULES, params=params, timeout=120)  # generous timeout
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print("    ERROR querying CMR:", e)
            # return what we have so far, caller can retry
            return found
        js = r.json()
        entries = js.get("feed", {}).get("entry", [])
        if not entries:
            break
        for item in entries:
            gran_id = item.get("title")
            t0 = item.get("time_start")
            t1 = item.get("time_end")
            links = item.get("links", [])
            for L in links:
                href = L.get("href")
                ltype = (L.get("type") or "").lower()
                if not href: 
                    continue
                # consider netcdf links or ones that look like data (not metadata)
                if href.lower().endswith(".nc") or "netcdf" in ltype or "application/x-netcdf" in ltype:
                    found.append({"granule_id": gran_id, "href": href, "time_start": t0, "time_end": t1})
        page_num += 1
        # stop if fewer than page_size entries
        if len(entries) < page_size:
            break
    return found

# -------- download helper (stream + retries handled by session adapter) --------
def download_href(href, save_dir=DOWNLOAD_DIR):
    fname = os.path.basename(href.split("?")[0])
    save_path = os.path.join(save_dir, fname)
    if os.path.exists(save_path):
        return save_path
    try:
        r = session.get(href, stream=True, timeout=180)
        ct = r.headers.get("Content-Type","")
        if r.status_code == 200 and (fname.lower().endswith(".nc") or "netcdf" in ct or "application" in ct):
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return save_path
        else:
            # save debug snippet if it's not a netcdf
            sample = r.content[:1024]
            dbg = save_path + ".debug"
            with open(dbg, "wb") as f:
                f.write(sample)
            print("    Download returned non-netcdf content; saved debug snippet:", dbg)
            return None
    except requests.exceptions.RequestException as e:
        print("    Download error:", e)
        return None

# -------- main: iterate windows, collect and download granules --------
windows = month_windows(START, END)
print(f"Will query {len(windows)} monthly windows.")

# load existing index if present (resume)
if os.path.exists(OUT_INDEX):
    index_df = pd.read_csv(OUT_INDEX)
else:
    index_df = pd.DataFrame(columns=["granule_id","href","time_start","time_end","local_path"])

all_new = []
for (s,e) in windows:
    g_list = fetch_granules_for_window(SHORT_NAME, s, e)
    if not g_list:
        print("  No granules found or query failed for window", s, e)
        continue
    # dedupe by href with index and existing
    for g in g_list:
        if ((index_df["href"] == g["href"]).any()) or any(x.get("href")==g["href"] for x in all_new):
            continue
        all_new.append(g)
    # optional short sleep to be polite to CMR
    time.sleep(1)

print(f"Total new granule links found: {len(all_new)}")

# Download the granules (can be restarted)
for g in all_new:
    href = g["href"]
    print("Downloading:", href)
    local = download_href(href)
    row = { "granule_id": g["granule_id"], "href": href, "time_start": g["time_start"], "time_end": g["time_end"], "local_path": local }
    index_df = index_df.append(row, ignore_index=True)
    # persist index after each download
    index_df.to_csv(OUT_INDEX, index=False)
    # tiny pause
    time.sleep(0.5)

print("Done. See", OUT_INDEX, "and folder", DOWNLOAD_DIR)
