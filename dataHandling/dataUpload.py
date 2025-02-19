import os
import sys
import pandas as pd
import numpy as np
import subprocess
import json
from scipy import stats

# -------------------------------
# Configuration: Update these paths and thresholds
# -------------------------------
input_file = "FlightsOct25.csv"        # Path to the CSV file you want to upload
output_csv = "Book3.csv"                 # Name for the new CSV file that Tableau will open
summary_excel = "data_summary.xlsx"      # Path where the basic Excel summary will be saved
insights_json = "data_insights.json"     # Path to save the summarized JSON insights file
TABLEAU_PATH = r"C:/Program Files/Tableau/Tableau 2024.3/bin/tableau.exe"  # Tableau Desktop executable

# Thresholds for filtering insights
CORR_THRESHOLD = 0.7     # Only store correlations with |r| >= 0.7
PVAL_THRESHOLD = 0.05    # and with p-value < 0.05
GROUP_DIFF_THRESHOLD = 0.2  # Relative difference (20%) in means to report a group difference

# -------------------------------
# Step 1: Validate the Input File
# -------------------------------
if not input_file.lower().endswith(".csv"):
    print("Error: The input file must be a .csv file.")
    sys.exit(1)

# -------------------------------
# Step 2: Read the CSV File using Pandas
# -------------------------------
try:
    df = pd.read_csv(input_file)
except Exception as e:
    print("Error reading CSV file:", e)
    sys.exit(1)

# -------------------------------
# Step 3: Extract Basic Schema and Role Inference
# -------------------------------
schema_info = []
for col in df.columns:
    dtype = df[col].dtype
    # Determine role: Numeric as Measures; datetime and objects as Dimensions.
    if pd.api.types.is_numeric_dtype(df[col]):
        role = "Measure"
    elif pd.api.types.is_datetime64_any_dtype(df[col]):
        role = "Dimension"
    else:
        role = "Dimension"
    
    schema_info.append({
        "Column": col,
        "Data Type": str(dtype),
        "Role": role,
        "Unique Values": int(df[col].nunique()),
        "Missing Values": int(df[col].isnull().sum()),
        "Sample Values": df[col].dropna().unique()[:5].tolist()
    })

schema_df = pd.DataFrame(schema_info)
print("Basic Schema Summary:")
print(schema_df)

# -------------------------------
# Step 4: Generate Detailed but Summarized Data Insights
# -------------------------------
data_insights = {}
key_insights = {}

for col in df.columns:
    col_series = df[col]
    insights = {}
    insights['data_type'] = str(col_series.dtype)
    non_null_count = int(col_series.count())
    insights['non_null_count'] = non_null_count
    missing_count = int(col_series.isnull().sum())
    insights['missing_values'] = missing_count
    insights['missing_percent'] = round((missing_count / len(col_series)) * 100, 2)
    
    # Flag columns with very high missing percentage
    if insights['missing_percent'] > 50:
        key_insights[col] = key_insights.get(col, []) + ["High missing values (>50%)"]
    
    if pd.api.types.is_numeric_dtype(col_series):
        clean_series = col_series.dropna()
        if clean_series.empty:
            continue
        mean_val = float(clean_series.mean())
        std_val = float(clean_series.std())
        insights['mean'] = mean_val
        insights['std'] = std_val
        insights['min'] = float(clean_series.min())
        insights['median'] = float(clean_series.median())
        insights['max'] = float(clean_series.max())
        insights['skew'] = float(stats.skew(clean_series))
        insights['kurtosis'] = float(stats.kurtosis(clean_series))
        # IQR-based outlier detection
        Q1 = clean_series.quantile(0.25)
        Q3 = clean_series.quantile(0.75)
        IQR = Q3 - Q1
        outliers = clean_series[(clean_series < (Q1 - 1.5 * IQR)) | (clean_series > (Q3 + 1.5 * IQR))]
        outlier_count = int(outliers.count())
        insights['outliers_count'] = outlier_count
        insights['outliers_percent'] = round((outlier_count / clean_series.count()) * 100, 2)
        # Flag high variability or unusual outlier rate
        if std_val > 0 and (std_val / abs(mean_val) > 1):
            key_insights[col] = key_insights.get(col, []) + ["High variability (std/mean > 1)"]
        if insights['outliers_percent'] > 10:
            key_insights[col] = key_insights.get(col, []) + ["High outlier rate (>10%)"]
    elif pd.api.types.is_datetime64_any_dtype(col_series):
        insights['min_date'] = str(col_series.min())
        insights['max_date'] = str(col_series.max())
    else:
        # For categorical/object types: only store unique value count and top 3 frequent values
        insights['unique_values_count'] = int(col_series.nunique())
        top_values = col_series.value_counts().head(3).to_dict()
        insights['top_values'] = top_values
        if insights['unique_values_count'] < 5:
            key_insights[col] = key_insights.get(col, []) + ["Low cardinality - potential categorical grouping"]

    data_insights[col] = insights

# -------------------------------
# Step 5: Compute Summarized Relationship Insights
# -------------------------------
relationship_insights = {}

# 5.1 Pairwise numeric correlation (only significant ones)
numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
significant_corr = {}
if len(numeric_cols) > 1:
    for i, col1 in enumerate(numeric_cols):
        for col2 in numeric_cols[i+1:]:
            clean1 = df[col1].dropna()
            clean2 = df[col2].dropna()
            common_idx = clean1.index.intersection(clean2.index)
            if len(common_idx) > 1:
                try:
                    r, p = stats.pearsonr(clean1.loc[common_idx], clean2.loc[common_idx])
                    if abs(r) >= CORR_THRESHOLD and p < PVAL_THRESHOLD:
                        significant_corr[f"{col1} vs {col2}"] = {"pearson_r": round(r, 4), "p_value": round(p, 4)}
                except Exception as ex:
                    continue
relationship_insights['significant_numeric_correlations'] = significant_corr

# 5.2 Group-by Analysis: Summarize differences for each categorical dimension vs. numeric measure
categorical_cols = [col for col in df.columns if df[col].dtype == 'object']
groupby_summary = {}
for cat in categorical_cols:
    groupby_summary[cat] = {}
    for num in numeric_cols:
        grouped = df.groupby(cat)[num].agg(['mean', 'count']).reset_index()
        if grouped['mean'].dropna().empty:
            continue
        try:
            highest_mean = grouped['mean'].max()
            lowest_mean = grouped['mean'].min()
            diff = highest_mean - lowest_mean
            # Only store if the relative difference is above the threshold
            if lowest_mean != 0 and (diff / abs(lowest_mean)) >= GROUP_DIFF_THRESHOLD:
                highest_group = grouped.loc[grouped['mean'].idxmax()].to_dict()
                lowest_group = grouped.loc[grouped['mean'].idxmin()].to_dict()
                groupby_summary[cat][num] = {
                    "highest_group": highest_group,
                    "lowest_group": lowest_group,
                    "relative_difference": round(diff / abs(lowest_mean), 2)
                }
        except Exception as ex:
            continue
relationship_insights['groupby_summary'] = groupby_summary

# 5.3 Missing Data Correlation (only store if any non-trivial correlations exist)
missing_df = df.isnull().astype(int)
missing_corr_matrix = missing_df.corr()
missing_corr_filtered = missing_corr_matrix.where(lambda x: (abs(x) >= 0.5) & (abs(x) < 1)).dropna(how='all', axis=0).dropna(how='all', axis=1)
relationship_insights['missing_correlation'] = missing_corr_filtered.to_dict()

# 5.4 Additional Relationship Insights (if any)
additional_relationships = {}
for col in numeric_cols:
    if data_insights.get(col, {}).get('skew', 0) > 1 or data_insights.get(col, {}).get('skew', 0) < -1:
        additional_relationships[col] = "Highly skewed distribution; consider transformations."
relationship_insights['additional_relationships'] = additional_relationships

# Add relationship insights to the main insights dictionary
data_insights['relationship_insights'] = relationship_insights

# -------------------------------
# Step 6: Create a Summary of Key Insights
# -------------------------------
data_insights['key_insights'] = key_insights

# -------------------------------
# Step 7: Save Summarized Insights to a JSON File
# -------------------------------
try:
    with open(insights_json, 'w') as json_file:
        json.dump(data_insights, json_file, indent=4)
    print(f"Summarized advanced data insights saved to {insights_json}")
except Exception as e:
    print("Error writing JSON file:", e)

# -------------------------------
# Step 8: Export the Basic Schema Summary to an Excel File
# -------------------------------
try:
    schema_df.to_excel(summary_excel, index=False)
    print(f"Basic schema summary saved to {summary_excel}")
except Exception as e:
    print("Error writing Excel file:", e)

# -------------------------------
# Step 9: Create a New CSV File for Tableau ("Book3.csv")
# -------------------------------
try:
    df.to_csv(output_csv, index=False)
    print(f"New CSV file created: {output_csv}")
except Exception as e:
    print("Error writing CSV file:", e)
    sys.exit(1)

# -------------------------------
# Step 10: Launch Tableau Desktop with the New CSV File using its Absolute Path
# -------------------------------
csv_full_path = os.path.abspath(output_csv)
print("Absolute CSV Path:", csv_full_path)
if os.path.exists(TABLEAU_PATH):
    try:
        subprocess.Popen([TABLEAU_PATH, csv_full_path])
        print("Tableau launched successfully with the file Book3.csv.")
    except Exception as e:
        print("Error launching Tableau:", e)
else:
    print(f"Tableau executable not found at {TABLEAU_PATH}. Please verify your Tableau installation path.")

# -------------------------------
# Requirements Summary
# -------------------------------
print("\nRequired Python packages:")
print(" - pandas")
print(" - numpy")
print(" - openpyxl")
print(" - scipy")
print("\nEnsure that Tableau Desktop is installed and that the TABLEAU_PATH variable is set correctly.")
