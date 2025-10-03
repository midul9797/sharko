import os
import pandas as pd
import numpy as np
import xarray as xr
from datetime import datetime
import glob
import sys
from scipy.spatial import KDTree

# ==============================================================================
# STEP 1: SETUP (UPDATED)
# ==============================================================================
# --- Configure your file paths and settings here ---

# UPDATED: Define the full time range of your new data
start_date_str = '2020-01-01'
end_date_str = '2025-06-10'

# Define the output directory for the final file
out_dir = "./final_model_data"
os.makedirs(out_dir, exist_ok=True)

# UPDATED: Set the paths to your new 8-day composite data folders
occurrence_file = r'C:\Sharko\Occurrence.tsv'
chl_folder = r'C:\Sharko\chlorophyll_data_8day' # Changed
sst_folder = r'C:\Sharko\sst_data_8day'         # Changed
ssh_folder = r'C:\Sharko\SSHA_New'
sss_folder = r'C:\Sharko\SSS_New'

# ==============================================================================
# STEP 2, 3, 4 (Unchanged)
# ==============================================================================
print("STEP 2: Loading and preparing shark presence data...")
required_columns = ['eventDate', 'decimalLatitude', 'decimalLongitude']
try:
    presence_data = pd.read_csv(
        occurrence_file, sep='\t', usecols=required_columns,
        on_bad_lines='warn', low_memory=False
    )
except (FileNotFoundError, ValueError) as e:
    print(f"Error loading the occurrence file: {e}")
    raise
presence_data.rename(columns={'eventDate': 'time', 'decimalLatitude': 'lat', 'decimalLongitude': 'lon'}, inplace=True)
presence_data['time'] = pd.to_datetime(presence_data['time'], errors='coerce')
presence_data.dropna(inplace=True)
presence_data = presence_data[
    (presence_data['time'] >= pd.to_datetime(start_date_str)) &
    (presence_data['time'] <= pd.to_datetime(end_date_str))
].reset_index(drop=True)
print(f"-> Found {len(presence_data)} valid shark presence records.")

print("STEP 3: Generating pseudo-absence data...")
if len(presence_data) > 0:
    # UPDATED: Generate twice as many pseudo-absence points as presence points (2:1 ratio).
    # This gives the model a richer set of "background" environmental conditions to learn from.
    num_pseudo_points = len(presence_data) * 2
    min_lat, max_lat = presence_data['lat'].min(), presence_data['lat'].max()
    min_lon, max_lon = presence_data['lon'].min(), presence_data['lon'].max()
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    start_ts, end_ts = int(start_date.timestamp()), int(end_date.timestamp())
    pseudo_lats = np.random.uniform(min_lat, max_lat, num_pseudo_points)
    pseudo_lons = np.random.uniform(min_lon, max_lon, num_pseudo_points)
    random_timestamps = np.random.randint(start_ts, end_ts, num_pseudo_points)
    pseudo_times = pd.to_datetime(random_timestamps, unit='s')
    pseudo_absence_data = pd.DataFrame({'time': pseudo_times, 'lat': pseudo_lats, 'lon': pseudo_lons})
    print(f"-> Generated {len(pseudo_absence_data)} pseudo-absence points.")
else:
    pseudo_absence_data = pd.DataFrame(columns=['time', 'lat', 'lon'])

print("STEP 4: Combining presence and absence data...")
presence_data['presence'] = 1
pseudo_absence_data['presence'] = 0
combined_points = pd.concat([presence_data, pseudo_absence_data], ignore_index=True)
print(f"-> Created a combined dataset with {len(combined_points)} total points.")


# ==============================================================================
# STEP 5: LOAD SATELLITE DATA (UPDATED)
# ==============================================================================
print("STEP 5: Loading satellite data functions...")

def _build_time_coordinate_from_filenames(ds, files):
    """
    UPDATED: Manually create a time coordinate from 8-day composite filenames.
    """
    # Assumes filename format like '...YYYYMMDD_YYYYMMDD...'
    try:
        # We parse the START date of the 8-day period from the filename
        times = [pd.to_datetime(os.path.basename(f).split('.')[1].split('_')[0], format='%Y%m%d') for f in files]
        ds = ds.assign_coords(time=times)
        print("      -> Successfully built time coordinate from filenames.")
        return ds
    except Exception:
        print("      ⚠️ WARNING: Could not build time coordinate from filenames.")
        return ds

def open_multifile_dataset(folder_path, lat_bounds, lon_bounds, needs_time_coord=False):
    search_pattern = os.path.join(folder_path, '*.nc')
    file_list = glob.glob(search_pattern)
    if not file_list: raise FileNotFoundError(f"No '.nc' files found in '{folder_path}'.")

    print(f"   Found {len(file_list)} files in {os.path.basename(folder_path)}. Verifying...")
    valid_files = []
    for f in file_list:
        try:
            with xr.open_dataset(f): valid_files.append(f)
        except Exception:
            print(f"   ⚠️ WARNING: Skipping corrupted file: {os.path.basename(f)}")
    if not valid_files: raise ValueError(f"No valid .nc files found in {folder_path}.")

    print(f"   -> Opening {len(valid_files)} valid files...")
    ds = xr.open_mfdataset(valid_files, combine='nested', concat_dim="time", join='override')
    
    if needs_time_coord:
        ds = _build_time_coordinate_from_filenames(ds, valid_files)

    coord_rename_map = {'latitude': 'lat', 'longitude': 'lon'}
    coords_to_rename = {k: v for k, v in coord_rename_map.items() if k in ds.coords}
    if coords_to_rename:
        ds = ds.rename(coords_to_rename)
    
    data_vars = [v for v in ds.data_vars if v not in ds.coords]
    print(f"      Found data variables: {data_vars}")
    
    print("      Cropping dataset (optimization)...")
    try:
        cropped_ds = ds.sel(lat=slice(max(lat_bounds), min(lat_bounds)), lon=slice(min(lon_bounds), max(lon_bounds)))
        if cropped_ds.dims['lat'] == 0 or cropped_ds.dims['lon'] == 0:
            print("      ⚠️ WARNING: The geographic bounds of this dataset do not overlap with your points. This variable will be skipped.")
            return None
        print("      Cropping successful.")
        return cropped_ds
    except KeyError:
        print("      ⚠️ WARNING: Could not pre-crop (expected for track data).")
        return ds

# ==============================================================================
# STEP 6: EXTRACT ENVIRONMENTAL DATA (UNCHANGED LOGIC)
# ==============================================================================
print("\nSTEP 6: Extracting environmental data for each variable...")

def _extract_track_data_with_kdtree(ds, variable, lookup_df):
    """
    Uses a KD-Tree for fast nearest-neighbor search on non-gridded data (like SSHA).
    """
    print(f"   Using specialized KD-Tree for track data...")
    sat_time = ds['time'].values.astype(np.int64) // 10**9 
    sat_lat = ds['lat'].values
    sat_lon = ds['lon'].values
    sat_points = np.vstack([sat_time, sat_lat, sat_lon]).T
    
    lookup_time = lookup_df['time'].values.astype(np.int64) // 10**9
    lookup_lat = lookup_df['lat'].values
    lookup_lon = lookup_df['lon'].values
    lookup_points = np.vstack([lookup_time, lookup_lat, lookup_lon]).T
    
    tree = KDTree(sat_points)
    _, indices = tree.query(lookup_points, k=1)
    
    return ds[variable].values[indices]

if len(combined_points) > 0:
    lat_bounds = (presence_data['lat'].min(), presence_data['lat'].max())
    lon_bounds = (presence_data['lon'].min(), presence_data['lon'].max())
    
    final_dataset = combined_points.copy()
    
    data_sources = {
        'chlor_a': {'folder': chl_folder, 'variable': 'chlor_a', 'is_gridded': True, 'needs_time': True},
        'sst':     {'folder': sst_folder, 'variable': 'sst', 'is_gridded': True, 'needs_time': True},
        'ssha':    {'folder': ssh_folder, 'variable': 'ssha', 'is_gridded': False},
        'sss':     {'folder': sss_folder, 'variable': 'sss_smap', 'is_gridded': True}
    }

    for name, source in data_sources.items():
        print(f"\n-> Processing: {name}")
        try:
            ds = open_multifile_dataset(
                source['folder'], lat_bounds, lon_bounds, 
                needs_time_coord=source.get('needs_time', False)
            )
            
            if ds is None: continue

            print(f"   Extracting '{source['variable']}' values...")
            if source['is_gridded']:
                extracted_values = ds[source['variable']].sel(
                    lat=xr.DataArray(final_dataset['lat'], dims='points'),
                    lon=xr.DataArray(final_dataset['lon'], dims='points'),
                    time=xr.DataArray(final_dataset['time'], dims='points'),
                    method='nearest'
                ).values
            else: 
                extracted_values = _extract_track_data_with_kdtree(ds, source['variable'], final_dataset)
            
            final_dataset[name] = extracted_values
            print(f"   -> Done.")
        except Exception as e:
            print(f"   ❌ ERROR processing {name}. This variable will be skipped. Error: {e}")

    # ==============================================================================
    # STEP 7 & 8 (LOGIC ADJUSTED)
    # ==============================================================================
    print("\nSTEP 7: Finalizing dataset...")
    final_dataset['day_of_year'] = final_dataset['time'].dt.dayofyear
    final_dataset['day_sin'] = np.sin(2 * np.pi * final_dataset['day_of_year'] / 365)
    final_dataset['day_cos'] = np.cos(2 * np.pi * final_dataset['day_of_year'] / 365)
    final_dataset = final_dataset.drop(columns=['day_of_year'])
    
    print(f"   Original rows: {len(final_dataset)}")
    final_dataset.dropna(inplace=True)
    print(f"   Rows with complete data: {len(final_dataset)}")
    print("-> Final dataset prepared.")

    if not final_dataset.empty:
        # --- NEW: Reorder columns to have 'presence' at the end ---
        print("   Reordering columns for clarity...")
        cols = final_dataset.columns.tolist()
        # Move the 'presence' column to the very end of the list
        cols.insert(len(cols), cols.pop(cols.index('presence')))
        final_dataset = final_dataset[cols]
        print("   Columns reordered.")

        # BUG FIX: Ensure filename extension matches compression type
        output_path = os.path.join(out_dir, 'model_training_dataset.csv.gz')
        final_dataset.to_csv(output_path, index=False, compression='gzip')

        print("\n" + "="*60)
        print(f"✅ SUCCESS! Your model-ready dataset is saved to: {output_path}")
        print("="*60)
        print("\nFirst 5 rows of the final dataset:")
        print(final_dataset.head())
    else:
        print("\nWARNING: Final dataset is empty. No file saved.")
else:
    print("\nNo data points found. No output file was created.")

