import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

# Step 1: Read the input file (assumed to be in Excel format)
input_file = 'highest_variance_Dev2_25_Nov_test3.xlsx'
df = pd.read_excel(input_file, header=None)

# Initialize variables
grouped_data = []
current_group = []
previous_y = df.iloc[0, 1]  # Start with the first y value

# Step 2: Group data by Y values
for _, row in df.iterrows():
    x, y, z, fom = row[0], row[1], row[2], row[3]
    
    # Combine x, y, z into one cell with line breaks
    cell_value = f"{x}\n{y}\n{z}"
    
    # Check if y value changes
    if y != previous_y:
        # Append the current group to the main list and start a new group
        grouped_data.append(current_group)
        current_group = []
        previous_y = y
    
    current_group.append(cell_value)

# Append the last group to the list
if current_group:
    grouped_data.append(current_group)

# Step 3: Create a new Excel workbook
wb = Workbook()
ws = wb.active

# Define fonts for color coding
font_x = Font(color="000000")  # Blue for X
font_y = Font(color="000000")  # Green for Y
font_z = Font(color="000000")  # Black for Z
#LUT_dev_2raw
# Step 4: Populate the Excel sheet with the grouped data
for row_idx, group in enumerate(grouped_data, start=1):
    for col_idx, cell_value in enumerate(group, start=1):
        cell = ws.cell(row=row_idx, column=col_idx, value=cell_value)
        
        # Apply font color and alignment (unified for the whole cell)
        if row_idx % 3 == 1:
            cell.font = font_x  # Blue for X
        elif row_idx % 3 == 2:
            cell.font = font_y  # Green for Y
        else:
            cell.font = font_z  # Black for Z
        
        cell.alignment = Alignment(wrap_text=True)

# Step 5: Save the formatted output to a new Excel file
output_file = 'output_grouped_coordinates_25_Nov_test3.xlsx'
wb.save(output_file)

print(f"Processed and formatted data has been saved to {output_file}.")

