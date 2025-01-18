import pandas as pd

# Load the uploaded CSV file
file_path = 'S&P500.csv'
data = pd.read_csv(file_path)

# Display the first few rows and data types of each column
data_info = {
    "head": data.head(),
    "dtypes": data.dtypes,
    "null_values": data.isnull().sum()
}
data_info

# Correct the data types

# Convert numeric columns (remove commas and convert to float)
for col in ['Adj Close', 'Open', 'High', 'Low']:
    if col in data.columns:
        data[col] = data[col].str.replace(',', '').astype(float)
    else:
        print(f"列 '{col}' は存在しないため処理をスキップしました。")

# Convert Date column to datetime format
data['Date'] = pd.to_datetime(data['Date'])

# Sort data by Date in ascending order
data.sort_values('Date', ascending=True, inplace=True)

# Verify the updated data types and preview the corrected data
corrected_data_info = {
    "head": data.head(),
    "dtypes": data.dtypes,
    "null_values": data.isnull().sum()
}
corrected_data_info

# Save the corrected data to a new CSV file
corrected_file_path = 'S&P500_corrected.csv'
data.to_csv(corrected_file_path, index=False)
corrected_file_path


