import csv

input_file = 'all_inlinks_ca_yahoo.csv'
output_file = 'parsed.txt'

# Open the input CSV file and output text file
with open(input_file, mode='r', newline='', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file)
    
    # Open the output text file
    with open(output_file, mode='w', encoding='utf-8') as txt_file:
        # Iterate over each row in the CSV
        for row in csv_reader:
            # Write the 'Source' column (second column) to the output file
            if len(row) > 1:  # Ensure there is a second column
                txt_file.write(row[1] + '\n')

print(f"Column 'Source' extracted to {output_file}")
