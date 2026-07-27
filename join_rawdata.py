import os
import numpy as np
import pandas as pd
pd.set_option('future.no_silent_downcasting', True)

def compute_circular_distance(val1, val2, max_val=6, fill_na=None):
    """Calculate the shortest distance between two points on a circular scale."""
    abs_diff = abs(val1 - val2)
    dist = min(abs_diff, max_val - abs_diff)

    if fill_na is not None and np.isnan(dist):
        dist = fill_na
    return dist


def compute_circular_distance_series(series1, series2, max_val=6):
    """Calculate circular distance element-wise for two pandas Series."""
    abs_diff = (series1 - series2).abs()
    # np.minimum compares each element of the two series and picks the smaller one
    dist = np.minimum(abs_diff, max_val - abs_diff)
    return dist

# this script takes the raw data files from the psychopy experiment and combines them into a single CSV file, 
# while also performing some data cleaning and transformation. This output can be found on the OSF page

# File Path Configurations 
data_directory = r"C:\Users\milan\OneDrive - UGent\UGent OneDrive\SingletonContext_2026\data"
output_file_path = r"C:\Users\milan\OneDrive - UGent\UGent OneDrive\SingletonContext_2026\CombinedData_n141.csv"
subject_overview_file_path = output_file_path.replace("CombinedData_n141", "SubjectInfo_n141")

# Processing Parameters & Column Configurations 
AT_CHANCE_DISTANCE = 1.5

columns_to_propagate_last_val = [
    "reported_locations_for_zero",
    "reported_locations_for_one",
    "reported_locations_binary",
]

columns_to_drop = [
    ".thisRepN",
    ".thisTrialN",
    ".thisN",
    ".thisIndex",
    "thisRow.t",
    "notes",
    "Unnamed: 36",
]

column_rename_mapping = {
    "Ik ben:": "DominantHand",
    "Leeftijd": "Age",
    "Geslacht": "Gender",
    "Heb je normaal kleurenzicht?": "HasNormColorVision",
    "Heb je normaal of gecorrigeerd naar normaal zicht? (Bril/Lenzen)": "HasNormVision",
    "reported_locations_for_zero": "ReportedInContextZero",
    "reported_locations_for_one": "ReportedInContextOne",
    "reported_locations_binary": "SelfReportedAwareness",
}

value_replacement_mapping = {
    "Ja": 1,
    "Nee": 0,
    "Rechtshandig": "R",
    "Linkshandig": "L",
}

columns_to_drop_subject_summary = [
    "Block",
    "TotalTrials",
    "TrialsWithinBlock",
    "CurrentHFLoc",
    "DistTrial",
    "DistLoc",
    "TargetLoc",
    "Condition",
    "BackgroundContext",
    "ColorSingleton",
    "ShapeSingleton",
    "LineOriTarget",
    "FixationPeriod",
    "PreviousHF",
    "AccuracyMessagerIsUsed",
    "CorrectnessResp",
    "RT",
    "KeyPressed",
    "SwitchBackground",
    "CurrentToHF_Distance",
]


# File Retrieval 
all_files = os.listdir(data_directory)
all_csv_files = [f for f in all_files if f.endswith(".csv")]
print(f"Total files in directory: {len(all_csv_files)}")


subject_counter = 0
processed_dfs = []

for filename in all_csv_files:
    file_path = os.path.join(data_directory, filename)
    df = pd.read_csv(file_path)
    subject_counter += 1
    print(f"Processing file {subject_counter}/{len(all_csv_files)}")

    # 1) Get the last non-empty value from the columns and propagate across all rows
    for col in columns_to_propagate_last_val:
        last_value = df[col].iloc[-1]
        df[col] = last_value

    # Check if last row is NaN in the block column; if so, drop the last row
    if pd.isna(df["Block"].iloc[-1]):
        df = df.drop(df.index[-1])

    # 2) Calculate and add extra derived columns
    # Calculate background context switching flag
    df["SwitchBackground"] = (
        df["BackgroundContext"]
        .diff()
        .abs()
        .fillna(0)
        .astype(int)
        .mask(df["Block"] != 2, np.nan)
    )

    # Calculate new accuracy
    df["Accuracy"] = round(df["CorrectnessResp"].sum() / len(df), 2)

    # Calculate distance between HF location and Distractor location
    dist_values = compute_circular_distance_series(df["CurrentHFLoc"], df["DistLoc"])
    df["CurrentToHF_Distance"] = np.where(np.round(df["DistTrial"]) == 1, dist_values, np.nan)

    # Flag trials with the same background context as the initial trial
    df["SameAsFirstContext"] = (df["BackgroundContext"].iloc[0] == df["BackgroundContext"]).astype(int)

    # Calculate Awareness Score
    # Extract the target HF locations for both background contexts
    hf_loc_zero = df.loc[df["BackgroundContext"] == 0, "CurrentHFLoc"].unique()[0]
    hf_loc_one = df.loc[df["BackgroundContext"] == 1, "CurrentHFLoc"].unique()[0]

    reported_hf_zero = df["reported_locations_for_zero"].unique()[0]
    reported_hf_one = df["reported_locations_for_one"].unique()[0]

    # Handle cases where participants skipped reporting (scored at chance level)
    if np.isnan(reported_hf_zero) and np.isnan(reported_hf_one):
        df["AwarenessScore"] = AT_CHANCE_DISTANCE
    else:
        # Calculate distances; if one context is unrepresented, substitute chance-level value
        dist_zero = compute_circular_distance(
            reported_hf_zero, hf_loc_zero, max_val=6, fill_na=AT_CHANCE_DISTANCE
        )
        dist_one = compute_circular_distance(
            reported_hf_one, hf_loc_one, max_val=6, fill_na=AT_CHANCE_DISTANCE
        )

        awareness_score = (dist_zero + dist_one) / 2
        df["AwarenessScore"] = awareness_score

    processed_dfs.append(df)

# Combine and Post-Process Combined Dataset 
df_combined = pd.concat(processed_dfs, ignore_index=True)

# Rename columns, drop unneeded columns, and standardize response values
df_combined = (
    df_combined.rename(columns=column_rename_mapping)
    .drop(columns=columns_to_drop)
    .replace(value_replacement_mapping)
)

# Filter out erroneous reaction time values caused by consecutive long delays
df_combined["RT"] = df_combined["RT"].mask(~df_combined["RT"].between(1, 3001))

# Export combined dataset
df_combined.to_csv(output_file_path, index=False)
print("Done")

# Generate and Export Subject Overview 
subject_summary_df = (
    df_combined.groupby("Participant")
    .head(1)
    .reset_index(drop=True)
    .drop(columns=columns_to_drop_subject_summary)
)

subject_summary_df.to_csv(subject_overview_file_path, index=False)
