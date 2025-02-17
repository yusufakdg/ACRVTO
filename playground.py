import pandas as pd

# Load the Excel file
excel_file = '/Users/muhammedyusufakdag/Desktop/FİYAT TEKLİFİ ŞABLON.xlsx'

# Read the Excel file
df = pd.read_excel(excel_file)


# Save the DataFrame to a CSV file
csv_file = '/Users/muhammedyusufakdag/Desktop/FİYAT_TEKLİFİ_ŞABLON.csv'
df.to_csv(csv_file, index=False)

print(f"Excel file {excel_file} has been converted to CSV file {csv_file}")