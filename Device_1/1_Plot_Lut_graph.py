import pandas as pd
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font

def extract_highest_variance_per_x(file_path, output_file):
    # Load the Excel file into a DataFrame
    df = pd.read_excel(file_path)
    
    # Initialize a list to store the results
    results = []

    # Get unique Y positions (rows)
    unique_y_positions = df['Y_Position'].unique()

    # Loop through each unique Y position (row)
    for y_pos in unique_y_positions:
        # Filter data for the current Y_Position
        current_row = df[df['Y_Position'] == y_pos]
        
        # Get unique X positions within this row
        unique_x_positions = current_row['X_Position'].unique()
        
        # For each unique X position, find the point with the highest variance
        for x_pos in unique_x_positions:
            # Filter data for the current X_Position within this row
            x_points = current_row[current_row['X_Position'] == x_pos]
            
            # Find the row with the maximum variance
            max_variance_row = x_points.loc[x_points['Variance'].idxmax()]
            
            # Extract the x, y, z positions and variance
            result = {
                'X_Position': max_variance_row['X_Position'],
                'Y_Position': max_variance_row['Y_Position'],
                'Z_Position': max_variance_row['Z_Position'],
                'Variance': max_variance_row['Variance']
            }
            results.append(result)

    # Convert results into a DataFrame
    result_df = pd.DataFrame(results, columns=['X_Position', 'Y_Position', 'Z_Position', 'Variance'])
    
    # Save the results to an Excel file
    result_df.to_excel(output_file, index=False)
    print(f"Results saved to {output_file}")
    
    # Plotting only the Z_Position
    plot_z_position(result_df)

def plot_z_position(df):
    # Plot the Z_Position as a line graph
    plt.figure(figsize=(10, 6))
    plt.plot(df['Z_Position'], marker='o', linestyle='-', color='b')
    
    # Label axes and title
    plt.title('Z Position Across Extracted Data Points')
    plt.xlabel('Data Point Index')
    plt.ylabel('Z Position')
    plt.grid(True)
    
    # Show the plot
    plt.show()

# Usage example
input_file ='Filtered_data_t11.xlsx'  # Replace with your actual file path
output_file = 'highest_variance_Dev1_22_Nov_test11.xlsx'
extract_highest_variance_per_x(input_file, output_file)

