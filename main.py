import streamlit as st
import pandas as pd
import numpy as np
import os
import glob
import re
from datetime import datetime

def validate_file_data_format(filename):
    # Check if the file has .xlsx extension
    if not filename.endswith('.xlsx'):
        raise ValueError('Invalid file format. Please upload a .xlsx file.')
        
def validate_file_price_format(filename, valid_formats):
    # Check if the file has a valid format
    if not filename.lower().endswith(valid_formats):
        raise ValueError(f'Invalid file format. Please upload a {valid_formats} file.')


def validate_file_data_name(filename):
    # Extract the year and month from the file name
    name_parts = os.path.splitext(filename)[0].split()
    if len(name_parts) != 2:
        raise ValueError('Invalid file name format. Please use "year month" format.')
    year, month = name_parts

def validate_file_price_name(filename, expected_name):
    if filename.lower() != expected_name.lower():
        raise ValueError(f'Invalid file name. Please upload a file named "{expected_name}", instead of "{filename}".')

def validate_file_data_columns(df):
    required_columns = ['Code', 'Description', 'Market Rent', 'Lease From', 'Lease To']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f'The following columns are missing: {", ".join(missing_columns)}')
        
def validate_worksheet_variables(worksheet, expected_variables):
    # Check if the worksheet contains all the expected variables in the third row
    header_row = 2  # Assuming the header row is the third row (index 2)
    headers = worksheet.iloc[header_row].tolist()

    for variable in expected_variables:
        if variable not in headers:
            raise ValueError(f'Variable "{variable}" not found in the worksheet.')


def process_data_file(file):
    validate_file_data_format(file.name)
    validate_file_data_name(file.name)

        
    # Read the file into a DataFrame
    df = pd.read_excel(file)

    # Validate the columns in the DataFrame
    validate_file_data_columns(df)

    # Save the DataFrame as a CSV file with the same name as the original file
    csv_filename = file.name.split()[0] + ' ' + file.name.split()[1][:3] + '.csv'
    df.to_csv(csv_filename, index=False)
    st.success(f'File successfully processed and saved as {csv_filename}.')
    
    
def process_price_file(file, expected_name):
    validate_file_price_format(file.name, '.xlsx')
    validate_file_price_name(file.name, expected_name)
    
    
    # Read the Excel file into a dictionary of DataFrames (one per sheet)
    Parking_Rev = pd.read_excel(file,sheet_name='Parking Rev',skiprows=2)
    Storage_Rev = pd.read_excel(file,sheet_name='Storage Rev',skiprows=1)
    
    # Check columns for required variables in Parking Rev sheet
    expected_columns_parking = ['Average Garage', 'Average Surface']
    missing_columns_parking = [col for col in expected_columns_parking if col not in Parking_Rev.columns]
    if missing_columns_parking:
        raise ValueError(f'Parking Rev sheet is missing the following columns: {", ".join(missing_columns_parking)}')

    # Check columns for required variables in Storage Rev sheet
    expected_columns_storage = ['Average Charge']
    missing_columns_storage = [col for col in expected_columns_storage if col not in Storage_Rev.columns]
    if missing_columns_storage:
        raise ValueError(f'Storage Rev sheet is missing the following columns: {", ".join(missing_columns_storage)}')

    # Save each sheet as a separate CSV file with the original sheet name
    parking_rev_csv_filename = 'Parking Rev.csv'
    storage_rev_csv_filename = 'Storage Rev.csv'
    Parking_Rev.to_csv(parking_rev_csv_filename, index=False)
    Storage_Rev.to_csv(storage_rev_csv_filename, index=False)
    st.success(f'Parking Rev sheet successfully saved as {parking_rev_csv_filename}.')
    st.success(f'Storage Rev sheet successfully saved as {storage_rev_csv_filename}.')

def generate_dataframe(file_path):
    # Read CSV file into a DataFrame
    df = pd.read_csv(file_path)
    return df

def generate_dataframe_name(file_name):
    # Extract year and month from the file name
    year, month = file_name.split()
    dataframe_name = f"{year}_{month}_data"
    return dataframe_name




def combine_csv_files():
    csv_files = [filename for filename in os.listdir() if re.match(r'\d{4}\s\w+\.csv', filename)]
    csv_files = sorted(csv_files, key=lambda x: pd.Timestamp(re.findall(r'\d{4}\s\w+', x)[0]))
    
    if not csv_files:
        raise FileNotFoundError('No CSV files found with the "year_month" format.')
        
    df_combined_indoor = pd.DataFrame()
    df_combined_outdoor = pd.DataFrame()
    df_combined_storage = pd.DataFrame()

    for csv_file in csv_files:
        df1 = pd.read_csv(csv_file)
        df = df1.copy()
        
        nan_rows = df[df['Description'].isna()]
    
        # Iterate over the NaN rows and update the first column based on the string inside parentheses
        for index, row in nan_rows.iterrows():
            first_col_value = str(row.iloc[0])  # Convert the value of the first column to a string
            match = re.search(r'\((.*?)\)', first_col_value)  # Extract the string inside parentheses
    
            if match:
                extracted_string = match.group(1)  # Get the string inside parentheses
                df.at[index, df.columns[0]] = extracted_string  # Update the value in the first column
        df = df[df.iloc[:, 0] != 'Total']
        df = df[df.iloc[:, 0] != 'Total for']
        df = df[df.iloc[:, 0] != 'Start Here']
        df = df[df.iloc[:, 0] != 'Start']
    
        df = df.dropna(subset=[df.columns[0]])
    
        # Reset the index after removing the rows
        df.reset_index(drop=True, inplace=True)
    
        df.dropna(how='all', inplace=True)
        # Reset the index after removing the rows
        df.reset_index(drop=True, inplace=True)
    
        mask = df.iloc[:, 0].notnull() & df.iloc[:, 1:].isnull().all(axis=1)
    
        # Filter the DataFrame using the mask
        filtered_df = df[mask]
    
        # Display the filtered DataFrame
        first_time_index = filtered_df[~filtered_df.duplicated(keep='first')].index
    
        # Get the complete index list of the filtered DataFrame
        complete_index = filtered_df.index
    
        # Get the index list excluding the first-time rows
        index_list = complete_index.difference(first_time_index)
    
        df = df.drop(index_list)
        mask = df.iloc[:, 0].notnull() & df.iloc[:, 1:].isnull().all(axis=1)
        # Filter the DataFrame using the mask
        filtered_df = df[mask]
        #Getting the index of the couumnity
        first_column_list = filtered_df.iloc[:, 0].tolist()
        
        file_date = re.findall(r'\d{4}\s\w+', csv_file)[0]
        date_obj = datetime.strptime(file_date, '%Y %b')
        columns_to_keep = ['Description', 'Lease From', 'Lease To','Market Rent']
        date_columns = ['Lease From', 'Lease To']  # Replace with your actual column names
    
    
    
        for i in range(len(first_column_list)):
            if i < len(first_column_list) - 1:
                a_index = df.index[df.iloc[:, 0] == first_column_list[i]].tolist()[0]
                b_index = df.index[df.iloc[:, 0] == first_column_list[i+1]].tolist()[0]
            else:
                a_index = df.index[df.iloc[:, 0] == first_column_list[i]].tolist()[0]
                b_index = df.shape[0]
    
    
            dataframe_name = f"{first_column_list[i]}_{date_obj.strftime('%Y%b')}"
    
            new_dataframe = df.loc[a_index+1:b_index-1].copy()
            new_dataframe.columns = df.columns  # Copy column names from the original DataFrame
    
            new_dataframe = new_dataframe[columns_to_keep]
    
            new_dataframe.fillna("None", inplace=True)
            new_dataframe.replace({np.nan: "None", pd.NaT: "None"}, inplace=True)
            new_dataframe[date_columns] = new_dataframe[date_columns].apply(lambda x: pd.to_datetime(x, errors='coerce'))
    
            new_dataframe = new_dataframe[~new_dataframe['Description'].str.contains('Bike')]
            new_dataframe.loc[new_dataframe['Description'].str.contains('Indoor|EV'), 'Description'] = 'Indoor Parking'
            new_dataframe.loc[new_dataframe['Description'].str.contains('Outdoor'), 'Description'] = 'Outdoor Parking'
            new_dataframe.loc[new_dataframe['Description'].str.contains('Storage'), 'Description'] = 'Storage'
    
            # mask = new_dataframe['Lease From'].notna() & new_dataframe['Lease To'].isna()
            # new_dataframe.loc[mask, 'Lease To'] = pd.to_datetime('2099-01-01')
            new_dataframe['Time_Difference'] = (date_obj - pd.to_datetime(new_dataframe['Lease From'])).dt.days / 30.4
            new_dataframe['Move in advanced'] = new_dataframe['Time_Difference'].apply(lambda x: 1 if x < 0 else 0)
            new_dataframe['Going to move in'] = new_dataframe['Time_Difference'].apply(lambda x: 1 if x < 0 and x > -1.5 else 0)
            new_dataframe['Recent move in'] = new_dataframe['Time_Difference'].apply(lambda x: 1 if x <= 1 and x > 0 else 0)
            new_dataframe = new_dataframe.drop('Time_Difference', axis=1)
    
            new_dataframe['Time_Difference'] = (pd.to_datetime(new_dataframe['Lease To'])-date_obj ).dt.days / 30.4
            new_dataframe['Moving out'] = new_dataframe['Time_Difference'].apply(lambda x: 1 if x <= 3 else 0)
            new_dataframe = new_dataframe.drop('Time_Difference', axis=1)
    
    
            new_dataframe['Lease time'] = (pd.to_datetime(new_dataframe['Lease To']) - pd.to_datetime(new_dataframe['Lease From'])).dt.days / 30.4
    
            globals()[dataframe_name] = new_dataframe
                
        Final_df = pd.DataFrame(first_column_list, columns=['Property Code'])    
            
        for property_code in first_column_list:
            # Get the dataframe name based on the property code
            dataframe_name = f"{property_code}_{date_obj.strftime('%Y%b')}"
        
            # Load the corresponding dataframe using the dynamic variable name
            df_temp = globals()[dataframe_name]
        
            # Separate dataframes for each description
            df_indoor = df_temp[df_temp['Description'] == 'Indoor Parking']
            df_outdoor = df_temp[df_temp['Description'] == 'Outdoor Parking']
            df_storage = df_temp[df_temp['Description'] == 'Storage']
            
            # Calculate the count of "Indoor Parking"
            count1_indoor = df_indoor.shape[0]  # Total Units
            count2_indoor = df_indoor[(df_indoor['Lease time'] != 0) & (df_indoor['Lease time'].notna())].shape[0]
            if count1_indoor == 0:
                count3_indoor = 0
            else:
                count3_indoor = round((count2_indoor / count1_indoor) * 100, 2)
            count4_indoor = df_indoor[df_indoor['Recent move in'] == 1].shape[0]
            count5_indoor = df_indoor[df_indoor['Moving out'] == 1].shape[0]
            count6_indoor_series = df_indoor[df_indoor['Market Rent'] != 0]['Market Rent'].mode()
            count6_indoor = count6_indoor_series.iloc[0] if not count6_indoor_series.empty else 0
    
            count1_outdoor = df_outdoor.shape[0]  # Total Units
            count2_outdoor = df_outdoor[(df_outdoor['Lease time'] != 0) & (df_outdoor['Lease time'].notna())].shape[0]
            if count1_outdoor == 0:
                count3_outdoor = 0
            else:
                count3_outdoor = round((count2_outdoor / count1_outdoor) * 100, 2)
            count4_outdoor = df_outdoor[df_outdoor['Recent move in'] == 1].shape[0]
            count5_outdoor = df_outdoor[df_outdoor['Moving out'] == 1].shape[0]
            count6_outdoor_series = df_outdoor[df_outdoor['Market Rent'] != 0]['Market Rent'].mode()
            count6_outdoor = count6_outdoor_series.iloc[0] if not count6_outdoor_series.empty else 0
    
            count1_storage = df_storage.shape[0]  # Total Units
            count2_storage = df_storage[(df_storage['Lease time'] != 0) & (df_storage['Lease time'].notna())].shape[0]
            if count1_storage == 0:
                count3_storage = 0
            else:
                count3_storage = round((count2_storage / count1_storage) * 100, 2)
            count4_storage = df_storage[df_storage['Recent move in'] == 1].shape[0]
            count5_storage = df_storage[df_storage['Moving out'] == 1].shape[0]
            count6_storage_series = df_storage[df_storage['Market Rent'] != 0]['Market Rent'].mode()
            count6_storage = count6_storage_series.iloc[0] if not count6_storage_series.empty else 0
    
            Final_df.loc[Final_df['Property Code'] == property_code, f'Total Units ({date_obj.strftime("%Y%b")}) (Indoor Parking)'] = count1_indoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Occupied ({date_obj.strftime("%Y%b")}) (Indoor Parking)'] = count2_indoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Percentage ({date_obj.strftime("%Y%b")}) (Indoor Parking)'] = count3_indoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'New Lease ({date_obj.strftime("%Y%b")}) (Indoor Parking)'] = count4_indoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Ending Lease ({date_obj.strftime("%Y%b")}) (Indoor Parking)'] = count5_indoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Price ({date_obj.strftime("%Y%b")}) (Indoor Parking)'] = count6_indoor
            
            Final_df.loc[Final_df['Property Code'] == property_code, f'Total Units ({date_obj.strftime("%Y%b")}) (Outdoor Parking)'] = count1_outdoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Occupied ({date_obj.strftime("%Y%b")}) (Outdoor Parking)'] = count2_outdoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Percentage ({date_obj.strftime("%Y%b")}) (Outdoor Parking)'] = count3_outdoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'New Lease ({date_obj.strftime("%Y%b")}) (Outdoor Parking)'] = count4_outdoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Ending Lease ({date_obj.strftime("%Y%b")}) (Outdoor Parking)'] = count5_outdoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Price ({date_obj.strftime("%Y%b")}) (Outdoor Parking)'] = count6_outdoor
            
            Final_df.loc[Final_df['Property Code'] == property_code, f'Total Units ({date_obj.strftime("%Y%b")}) (Storage)'] = count1_storage
            Final_df.loc[Final_df['Property Code'] == property_code, f'Occupied ({date_obj.strftime("%Y%b")}) (Storage)'] = count2_storage
            Final_df.loc[Final_df['Property Code'] == property_code, f'Percentage ({date_obj.strftime("%Y%b")}) (Storage)'] = count3_storage
            Final_df.loc[Final_df['Property Code'] == property_code, f'New Lease ({date_obj.strftime("%Y%b")}) (Storage)'] = count4_storage
            Final_df.loc[Final_df['Property Code'] == property_code, f'Ending Lease ({date_obj.strftime("%Y%b")}) (Storage)'] = count5_storage
            Final_df.loc[Final_df['Property Code'] == property_code, f'Price ({date_obj.strftime("%Y%b")}) (Storage)'] = count6_storage
            
        df_indoor_parking = Final_df[['Property Code'] + [f'Total Units ({date_obj.strftime("%Y%b")}) (Indoor Parking)',
                                                         f'Occupied ({date_obj.strftime("%Y%b")}) (Indoor Parking)',
                                                         f'Percentage ({date_obj.strftime("%Y%b")}) (Indoor Parking)',
                                                         f'New Lease ({date_obj.strftime("%Y%b")}) (Indoor Parking)',
                                                         f'Ending Lease ({date_obj.strftime("%Y%b")}) (Indoor Parking)',
                                                         f'Price ({date_obj.strftime("%Y%b")}) (Indoor Parking)']].copy()
        
        df_outdoor_parking = Final_df[['Property Code'] + [f'Total Units ({date_obj.strftime("%Y%b")}) (Outdoor Parking)',
                                                          f'Occupied ({date_obj.strftime("%Y%b")}) (Outdoor Parking)',
                                                          f'Percentage ({date_obj.strftime("%Y%b")}) (Outdoor Parking)',
                                                          f'New Lease ({date_obj.strftime("%Y%b")}) (Outdoor Parking)',
                                                          f'Ending Lease ({date_obj.strftime("%Y%b")}) (Outdoor Parking)',
                                                          f'Price ({date_obj.strftime("%Y%b")}) (Outdoor Parking)']].copy()
        
        df_storage = Final_df[['Property Code'] + [f'Total Units ({date_obj.strftime("%Y%b")}) (Storage)',
                                                   f'Occupied ({date_obj.strftime("%Y%b")}) (Storage)',
                                                   f'Percentage ({date_obj.strftime("%Y%b")}) (Storage)',
                                                   f'New Lease ({date_obj.strftime("%Y%b")}) (Storage)',
                                                   f'Ending Lease ({date_obj.strftime("%Y%b")}) (Storage)',
                                                   f'Price ({date_obj.strftime("%Y%b")}) (Storage)']].copy()
                
                        # Concatenate dataframes to combined dataframes
        df_combined_indoor = pd.concat([df_combined_indoor, df_indoor_parking], axis=1)
        df_combined_outdoor = pd.concat([df_combined_outdoor, df_outdoor_parking], axis=1)
        df_combined_storage = pd.concat([df_combined_storage, df_storage], axis=1)
        
        # final_df[f'Price_per_Unit({date_obj.strftime("%Y%b")})'] = final_df['2022July price'] / final_df['Total Units']
        # final_df[f'Occupancy_Rate({date_obj.strftime("%Y%b")})'] = final_df['2022July Occupied'] / final_df['Total Units']
        # final_df[f'Lease_Turnover_Rate({date_obj.strftime("%Y%b")})'] = final_df['2022July New Lease'] / final_df['Total Units']
        # final_df[f'Ending_Lease_Rate({date_obj.strftime("%Y%b")})'] = final_df['2022July Ending Lease'] / final_df['Total Units']
        
        # duplicated_columns = df_combined_indoor.columns[df_combined_indoor.columns.duplicated(keep='first')]
        # df_combined_indoor = df_combined_indoor.drop(columns=duplicated_columns)
        # duplicated_columns = df_combined_outdoor.columns[df_combined_outdoor.columns.duplicated(keep='first')]
        # df_combined_outdoor = df_combined_outdoor.drop(columns=duplicated_columns)
        # duplicated_columns = df_combined_storage.columns[df_combined_storage.columns.duplicated(keep='first')]
        # df_combined_storage = df_combined_storage.drop(columns=duplicated_columns)
            
            
            
        df_combined_indoor.to_csv('indoor_storage.csv', index=False)
        df_combined_outdoor.to_csv('outdoor_storage.csv', index=False)
        df_combined_storage.to_csv('storage.csv', index=False)
        
        st.success("CSV files saved successfully.")


# Streamlit app
def main():
    st.title("File Uploader")

    uploaded_file = st.file_uploader("Upload file(s)", type="xlsx", accept_multiple_files=True)
    specific_file = st.file_uploader("Upload specific file", type="xlsx")

    if uploaded_file is not None:
        for file in uploaded_file:
            try:
                process_data_file(file)
            except ValueError as e:
                st.error(str(e))
    
    if specific_file is not None:
        try:
            process_price_file(specific_file, "Parking Storage Rev Final v1.xlsx")
        except ValueError as e:
            st.error(str(e))
    
    run_code = st.button("Run Code")

    if run_code:
        # Get a list of all CSV files in the current directory
        csv_files = glob.glob("*.csv")

        # Filter CSV files with the format "year month"
        csv_files = [file for file in csv_files if len(file.split()) == 2]

        if not csv_files:
            st.write("No CSV files found with the format 'year month'.")
            return

        for file_path in csv_files:
            dataframe_name = generate_dataframe_name(os.path.splitext(file_path)[0])
            df = generate_dataframe(file_path)

            # Create a dataframe variable dynamically
            globals()[dataframe_name] = df

            st.subheader(f"DataFrame: {dataframe_name}")
            st.write(df)

        # Display the names of all the generated dataframes
        st.subheader("Dataframe Names")
        dataframe_names = [name for name in globals() if name.endswith("_data")]
        st.write(dataframe_names)
        
    combine_button = st.button("Combine CSV Files")
    if combine_button:
        combine_csv_files()



if __name__ == '__main__':
    main()