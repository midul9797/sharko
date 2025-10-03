# --- TEMPORARY DEBUGGING CODE ---
import pandas as pd

# Setting this option ensures you see all columns
pd.set_option('display.max_rows', 300) 

df_check = pd.read_csv(r'C:\Users\dasso\OneDrive\Desktop\Sharko\Occurrence.tsv', sep='\t', low_memory=False)
print("Full list of columns:")
print(df_check.columns.to_series()) # Print all columns, one per line

exit()
# --- END OF DEBUGGING CODE ---