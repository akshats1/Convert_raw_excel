import pandas as pd

# Path to your .txt file
input_file = "LUT_T1_Dev_2.txt"
output_file = "filtered_data_T1.xlsx"

# Read the .txt file into a DataFrame
df = pd.read_csv(input_file)

# Filter out rows where X_Position is -260
filtered_df = df[df["X_Position"] != -190]

# Save the filtered data to an Excel file
filtered_df.to_excel(output_file, index=False)

print(f"Filtered data saved to {output_file}")

