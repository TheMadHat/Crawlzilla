import csv

input_file = 'input.csv'
output_file = 'output.csv'

# Open the input file
with open(input_file, 'r') as infile:
    reader = csv.reader(infile)
    rows = list(reader)

# Prepare the output list with blank rows inserted
output_rows = []
for row in rows:
    output_rows.append(row)
    output_rows.append([''] * len(row))  # Insert a blank row with the same number of columns

# Write the updated data to the output file
with open(output_file, 'w', newline='') as outfile:
    writer = csv.writer(outfile)
    writer.writerows(output_rows)

print(f"Blank rows inserted. The output file is saved as {output_file}.")
