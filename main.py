
import streamlit as st
import pandas as pd
import numpy as np
import os
import glob
import re
import matplotlib.pyplot as plt

from docx import Document
from PIL import Image
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from pyomo.environ import *
import st_aggrid
#from st_aggrid.grid_options_builder import GridOptionsBuilder

def display_manual(path):
    doc = Document(path)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    st.write(text)

@st.cache
def validate_file_data_format(filename):
    # Check if the file has .xlsx extension
    if not filename.endswith('.xlsx'):
        raise ValueError('Invalid file format. Please upload a .xlsx file.')

@st.cache        
def validate_file_price_format(filename, valid_formats):
    # Check if the file has a valid format
    if not filename.lower().endswith(valid_formats):
        raise ValueError(f'Invalid file format. Please upload a {valid_formats} file.')


@st.cache
def validate_file_data_name(filename):
    # Extract the year and month from the file name
    name_parts = os.path.splitext(filename)[0].split()
    if len(name_parts) != 2:
        raise ValueError('Invalid file name format. Please use "year month" format.')
    year, month = name_parts

@st.cache
def validate_file_price_name(filename, expected_name):
    if filename.lower() != expected_name.lower():
        raise ValueError(f'Invalid file name. Please upload a file named "{expected_name}", instead of "{filename}".')

@st.cache
def validate_file_data_columns(df):
    required_columns = ['Code', 'Description', 'Market Rent', 'Lease From', 'Lease To']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f'The following columns are missing: {", ".join(missing_columns)}')
 
@st.cache       
def validate_worksheet_variables(worksheet, expected_variables):
    # Check if the worksheet contains all the expected variables in the third row
    header_row = 2  # Assuming the header row is the third row (index 2)
    headers = worksheet.iloc[header_row].tolist()

    for variable in expected_variables:
        if variable not in headers:
            raise ValueError(f'Variable "{variable}" not found in the worksheet.')


@st.cache
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

def is_valid_year_format(input_str):
    # Regular expression pattern to check if the input is a four-digit year
    year_pattern = r'^\d{4}$'
    return bool(re.match(year_pattern, input_str))    

@st.cache(suppress_st_warning=True)
def process_price_file(file, expected_name,indooryear,outdooryear,storageyear):
    
    if not is_valid_year_format(indooryear) or not is_valid_year_format(outdooryear)or not is_valid_year_format(storageyear):
        raise ValueError("Please enter valid year format for CSV file names.")
    
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
    
    average_indoor_cols = [col for col in Parking_Rev.columns if "Average Garage" in col]
    selected_cols1 = ['Property Code'] + average_indoor_cols
    Indoor_comp = Parking_Rev[selected_cols1].copy()
    for idx, col in enumerate(Indoor_comp.columns[1:], start=int(indooryear)):
        year = str(idx)
        Indoor_comp.rename(columns={col: f"{year} Indoor Comp price"}, inplace=True)
        
    average_outdoor_cols = [col for col in Parking_Rev.columns if "Average Surface" in col]
    selected_cols2 = ['Property Code'] + average_outdoor_cols
    outdoor_comp = Parking_Rev[selected_cols2].copy()
    for idx, col in enumerate(outdoor_comp.columns[1:], start=int(outdooryear)):
        year = str(idx)
        outdoor_comp.rename(columns={col: f"{year} Outdoor Comp price"}, inplace=True)
        
    average_storage_cols = [col for col in Storage_Rev.columns if "Average Charge" in col]
    selected_cols3 = ['Property Code'] + average_storage_cols
    storage_comp = Storage_Rev[selected_cols3].copy()
    for idx, col in enumerate(storage_comp.columns[1:], start=int(storageyear)):
        year = str(idx)
        storage_comp.rename(columns={col: f"{year} Storage Comp price"}, inplace=True)
    # Save each sheet as a separate CSV file with the original sheet name
    parking_rev_csv_filename = 'Parking Rev.csv'
    storage_rev_csv_filename = 'Storage Rev.csv'
    Parking_Rev.to_csv(parking_rev_csv_filename, index=False)
    Storage_Rev.to_csv(storage_rev_csv_filename, index=False)
    Indoor_comp.to_csv("Indoor Comp price.csv", index=False)
    outdoor_comp.to_csv("Outdoor Comp price.csv", index=False)
    storage_comp.to_csv("Storage Comp price.csv", index=False)
    st.success(f'Parking Rev sheet successfully saved as {parking_rev_csv_filename}.')
    st.success(f'Storage Rev sheet successfully saved as {storage_rev_csv_filename}.')

@st.cache
def generate_dataframe(file_path):
    # Read CSV file into a DataFrame
    df = pd.read_csv(file_path)
    return df

@st.cache
def generate_dataframe_name(file_name):
    # Extract year and month from the file name
    year, month = file_name.split()
    dataframe_name = f"{year}_{month}_data"
    return dataframe_name



@st.cache
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
        columns_to_keep = ['Description', 'Lease From', 'Lease To','Market Rent','Current Rent']
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
            count4_indoor = df_indoor[df_indoor['Recent move in'] == 1].shape[0]
            count5_indoor = df_indoor[df_indoor['Moving out'] == 1].shape[0]
            count6_indoor_series = df_indoor[df_indoor['Market Rent'] != 0]['Market Rent'].mode()
            count6_indoor = count6_indoor_series.iloc[0] if not count6_indoor_series.empty else 0
            count7_indoor_series = df_indoor[df_indoor['Current Rent'] != 0]['Current Rent'].mean()
            count7_indoor = count7_indoor_series#.iloc[0] #if not count7_indoor_series.empty else 0
            if count1_indoor == 0:
                count3_indoor = 0                
                count8_indoor = 0
                count9_indoor = 0
            else:
                count3_indoor = round((count2_indoor / count1_indoor) * 100, 2)
                count8_indoor = round((count5_indoor / count1_indoor) * 100, 2)
                count9_indoor = round((count6_indoor / count1_indoor) * 100, 2)
    
            count1_outdoor = df_outdoor.shape[0]  # Total Units
            count2_outdoor = df_outdoor[(df_outdoor['Lease time'] != 0) & (df_outdoor['Lease time'].notna())].shape[0]
            count4_outdoor = df_outdoor[df_outdoor['Recent move in'] == 1].shape[0]
            count5_outdoor = df_outdoor[df_outdoor['Moving out'] == 1].shape[0]
            count6_outdoor_series = df_outdoor[df_outdoor['Market Rent'] != 0]['Market Rent'].mode()
            count6_outdoor = count6_outdoor_series.iloc[0] if not count6_outdoor_series.empty else 0
            count7_outdoor_series = df_outdoor[df_outdoor['Current Rent'] != 0]['Current Rent'].mean()
            count7_outdoor = count7_outdoor_series#.iloc[0] #if not count7_outdoor_series.empty else 0
            if count1_outdoor == 0:
                count3_outdoor = 0
                count8_outdoor = 0
                count9_outdoor = 0
            else:
                count3_outdoor = round((count2_outdoor / count1_outdoor) * 100, 2)
                count8_outdoor = round((count5_outdoor / count1_outdoor) * 100, 2)
                count9_outdoor = round((count6_outdoor / count1_outdoor) * 100, 2)
            
            count1_storage = df_storage.shape[0]  # Total Units
            count2_storage = df_storage[(df_storage['Lease time'] != 0) & (df_storage['Lease time'].notna())].shape[0]
            count4_storage = df_storage[df_storage['Recent move in'] == 1].shape[0]
            count5_storage = df_storage[df_storage['Moving out'] == 1].shape[0]
            count6_storage_series = df_storage[df_storage['Market Rent'] != 0]['Market Rent'].mode()
            count6_storage = count6_storage_series.iloc[0] if not count6_storage_series.empty else 0
            count7_storage_series = df_storage[df_storage['Current Rent'] != 0]['Current Rent'].mean()
            count7_storage = count7_storage_series#.iloc[0] #if not count7_storage_series.empty else 0
            if count1_storage == 0:
                count3_storage = 0
                count8_storage = 0
                count9_storage = 0
            else:
                count3_storage = round((count2_storage / count1_storage) * 100, 2)
                count8_storage = round((count5_storage / count1_storage) * 100, 2)
                count9_storage = round((count6_storage / count1_storage) * 100, 2)  
    
            Final_df.loc[Final_df['Property Code'] == property_code, f'Total Units ({date_obj.strftime("%Y%b")}) (Indoor Parking)'] = count1_indoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Occupied ({date_obj.strftime("%Y%b")}) (Indoor Parking)'] = count2_indoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Percentage% ({date_obj.strftime("%Y%b")}) (Indoor Parking)'] = count3_indoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'New Lease ({date_obj.strftime("%Y%b")}) (Indoor Parking)'] = count4_indoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Ending Lease ({date_obj.strftime("%Y%b")}) (Indoor Parking)'] = count5_indoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Market Price ({date_obj.strftime("%Y%b")}) (Indoor Parking)'] = count6_indoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Current Price ({date_obj.strftime("%Y%b")}) (Indoor Parking)'] = count7_indoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Lease_Turnover_Rate% ({date_obj.strftime("%Y%b")}) (Indoor Parking)'] = count8_indoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Ending_Lease_Rate% ({date_obj.strftime("%Y%b")}) (Indoor Parking)'] = count9_indoor
            
            Final_df.loc[Final_df['Property Code'] == property_code, f'Total Units ({date_obj.strftime("%Y%b")}) (Outdoor Parking)'] = count1_outdoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Occupied ({date_obj.strftime("%Y%b")}) (Outdoor Parking)'] = count2_outdoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Percentage% ({date_obj.strftime("%Y%b")}) (Outdoor Parking)'] = count3_outdoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'New Lease ({date_obj.strftime("%Y%b")}) (Outdoor Parking)'] = count4_outdoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Ending Lease ({date_obj.strftime("%Y%b")}) (Outdoor Parking)'] = count5_outdoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Market Price ({date_obj.strftime("%Y%b")}) (Outdoor Parking)'] = count6_outdoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Current Price ({date_obj.strftime("%Y%b")}) (Outdoor Parking)'] = count7_outdoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Lease_Turnover_Rate% ({date_obj.strftime("%Y%b")}) (Outdoor Parking)'] = count8_outdoor
            Final_df.loc[Final_df['Property Code'] == property_code, f'Ending_Lease_Rate% ({date_obj.strftime("%Y%b")}) (Outdoor Parking)'] = count9_outdoor
            
            Final_df.loc[Final_df['Property Code'] == property_code, f'Total Units ({date_obj.strftime("%Y%b")}) (Storage)'] = count1_storage
            Final_df.loc[Final_df['Property Code'] == property_code, f'Occupied ({date_obj.strftime("%Y%b")}) (Storage)'] = count2_storage
            Final_df.loc[Final_df['Property Code'] == property_code, f'Percentage% ({date_obj.strftime("%Y%b")}) (Storage)'] = count3_storage
            Final_df.loc[Final_df['Property Code'] == property_code, f'New Lease ({date_obj.strftime("%Y%b")}) (Storage)'] = count4_storage
            Final_df.loc[Final_df['Property Code'] == property_code, f'Ending Lease ({date_obj.strftime("%Y%b")}) (Storage)'] = count5_storage
            Final_df.loc[Final_df['Property Code'] == property_code, f'Market Price ({date_obj.strftime("%Y%b")}) (Storage)'] = count6_storage
            Final_df.loc[Final_df['Property Code'] == property_code, f'Current Price ({date_obj.strftime("%Y%b")}) (Storage)'] = count7_storage
            Final_df.loc[Final_df['Property Code'] == property_code, f'Lease_Turnover_Rate% ({date_obj.strftime("%Y%b")}) (Storage)'] = count8_storage
            Final_df.loc[Final_df['Property Code'] == property_code, f'Ending_Lease_Rate% ({date_obj.strftime("%Y%b")}) (Storage)'] = count9_storage
            
        df_indoor_parking = Final_df[['Property Code'] + [f'Total Units ({date_obj.strftime("%Y%b")}) (Indoor Parking)',
                                                         f'Occupied ({date_obj.strftime("%Y%b")}) (Indoor Parking)',
                                                         f'Percentage% ({date_obj.strftime("%Y%b")}) (Indoor Parking)',
                                                         f'New Lease ({date_obj.strftime("%Y%b")}) (Indoor Parking)',
                                                         f'Ending Lease ({date_obj.strftime("%Y%b")}) (Indoor Parking)',
                                                         f'Market Price ({date_obj.strftime("%Y%b")}) (Indoor Parking)',
                                                         f'Current Price ({date_obj.strftime("%Y%b")}) (Indoor Parking)',
                                                         f'Lease_Turnover_Rate% ({date_obj.strftime("%Y%b")}) (Indoor Parking)',
                                                         f'Ending_Lease_Rate% ({date_obj.strftime("%Y%b")}) (Indoor Parking)']].copy()
        
        df_outdoor_parking = Final_df[['Property Code'] + [f'Total Units ({date_obj.strftime("%Y%b")}) (Outdoor Parking)',
                                                          f'Occupied ({date_obj.strftime("%Y%b")}) (Outdoor Parking)',
                                                          f'Percentage% ({date_obj.strftime("%Y%b")}) (Outdoor Parking)',
                                                          f'New Lease ({date_obj.strftime("%Y%b")}) (Outdoor Parking)',
                                                          f'Ending Lease ({date_obj.strftime("%Y%b")}) (Outdoor Parking)',
                                                          f'Market Price ({date_obj.strftime("%Y%b")}) (Outdoor Parking)',
                                                          f'Current Price ({date_obj.strftime("%Y%b")}) (Outdoor Parking)',
                                                          f'Lease_Turnover_Rate% ({date_obj.strftime("%Y%b")}) (Outdoor Parking)',
                                                          f'Ending_Lease_Rate% ({date_obj.strftime("%Y%b")}) (Outdoor Parking)']].copy()
        
        df_storage = Final_df[['Property Code'] + [f'Total Units ({date_obj.strftime("%Y%b")}) (Storage)',
                                                   f'Occupied ({date_obj.strftime("%Y%b")}) (Storage)',
                                                   f'Percentage% ({date_obj.strftime("%Y%b")}) (Storage)',
                                                   f'New Lease ({date_obj.strftime("%Y%b")}) (Storage)',
                                                   f'Ending Lease ({date_obj.strftime("%Y%b")}) (Storage)',
                                                   f'Market Price ({date_obj.strftime("%Y%b")}) (Storage)',
                                                   f'Current Price ({date_obj.strftime("%Y%b")}) (Storage)',
                                                   f'Lease_Turnover_Rate% ({date_obj.strftime("%Y%b")}) (Storage)',
                                                   f'Ending_Lease_Rate% ({date_obj.strftime("%Y%b")}) (Storage)']].copy()
                
                        # Concatenate dataframes to combined dataframes
        df_combined_indoor = pd.concat([df_combined_indoor, df_indoor_parking], axis=1)
        df_combined_outdoor = pd.concat([df_combined_outdoor, df_outdoor_parking], axis=1)
        df_combined_storage = pd.concat([df_combined_storage, df_storage], axis=1)
        
        df_combined_indoor = df_combined_indoor.loc[:,~df_combined_indoor.columns.duplicated()].copy()
        df_combined_outdoor = df_combined_outdoor.loc[:,~df_combined_outdoor.columns.duplicated()].copy()
        df_combined_storage = df_combined_storage.loc[:,~df_combined_storage.columns.duplicated()].copy()  
        
        df_combined_indoor.fillna(0, inplace=True)
        df_combined_outdoor.fillna(0, inplace=True)
        df_combined_storage.fillna(0, inplace=True)
        
        Indoor_comp = pd.read_csv("Indoor Comp price.csv")
        outdoor_comp = pd.read_csv("Outdoor Comp price.csv")
        storage_comp = pd.read_csv("Storage Comp price.csv")
        
        df_combined_indoor = pd.merge(Indoor_comp,df_combined_indoor,how="right")
        df_combined_outdoor = pd.merge(outdoor_comp,df_combined_outdoor,how="right")
        df_combined_storage = pd.merge(storage_comp,df_combined_storage,how="right")
        
        # Check if the "Final datasets" folder exists, and create it if not
        output_folder = "Final datasets"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
    
        indoor_parking_csv_file = os.path.join(output_folder, 'indoor_parking.csv')
        outdoor_parking_csv_file = os.path.join(output_folder, 'outdoor_parking.csv')
        storage_csv_file = os.path.join(output_folder, 'storage.csv')
            
        df_combined_indoor.to_csv(indoor_parking_csv_file, index=False)
        df_combined_outdoor.to_csv(outdoor_parking_csv_file, index=False)
        df_combined_storage.to_csv(storage_csv_file, index=False)
        
        
 
@st.cache       
def Opt(data,upper_limit,lower_limit):
    # Define the month names
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    # Define the function to get the most recent month and year from the dataset
    def get_recent_month_year(df_storage):
        all_months = sorted([col.split(' ')[1][1:-1] for col in df_storage.columns if "Percentage%" in col])
        recent_month = all_months[-1]
        recent_year = int(recent_month[:4])
        recent_month_name = recent_month[4:]
        recent_month_num = month_names.index(recent_month_name) + 1
        return recent_month_num, recent_year
    
    
    # Get the recent month and year
    recent_month, recent_year = get_recent_month_year(data)
    recent_month_str = f'{recent_year}{month_names[recent_month - 1]}'
    # target_month = (recent_month % 12) + 1
    # target_year = recent_year if recent_month != 12 else recent_year + 1
    
    # Get the previous month and year
    previous_month = (recent_month - 2) % 12 + 1
    previous_year = recent_year if previous_month != 12 else recent_year - 1
    
    # Get the column name for the previous month's current prices
    previous_month_prefix =  f'Current Price ({previous_year}{month_names[previous_month - 1]})'
    previous_month_column = [col for col in data.columns if col.startswith(previous_month_prefix)][0]
    
    # Select relevant columns for the regression model
    feature_columns = [col for col in data.columns if col not in ['Property Code'] and not col.startswith(f'Percentage% ({recent_month_str})')]
    #feature_columns = [col for col in df_storage.columns if col not in ['Property Code', f'Percentage% ({recent_month_str}) (Storage)']]
    target_column_prefix = f'Percentage% ({recent_month_str})'
    target_column = [col for col in data.columns if col.startswith(target_column_prefix)][0]

    #target_column = f'Percentage% ({recent_month_str}) (Storage)'

    
    # Prepare the data
    X = data[feature_columns]
    y = data[target_column]
    
    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
     
    # Initialize and train the Random Forest model
    rf = RandomForestRegressor(random_state=42)
    rf.fit(X_train, y_train)
    
    # Get feature importances
    importances = rf.feature_importances_
    features_importances = sorted(zip(importances, X.columns), reverse=True)
    
    # Select the most important features
    important_features = [name for importance, name in features_importances if importance > 0.01]
    
    # Prepare the data with only the most important features
    X = data[important_features]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    rf.fit(X_train, y_train)
    # Predict the target variable for the test data
    y_pred = rf.predict(X_test)
    
    # Bootstrap the residuals to calculate confidence intervals
    n_iterations = 1000
    alpha = 0.05  # 95% confidence interval
    residuals_indoor = y_test - y_pred
    lower_percentile = 100 * alpha / 2
    upper_percentile = 100 * (1 - alpha / 2)
    bootstrap_lower_updated = []
    bootstrap_upper_updated = []
    
    for i in range(n_iterations):
        bootstrap_residuals_updated = np.random.choice(residuals_indoor, size=len(residuals_indoor), replace=True)
        bootstrap_predictions_updated = y_pred + bootstrap_residuals_updated
        bootstrap_lower_updated.append(np.percentile(bootstrap_predictions_updated, lower_percentile))
        bootstrap_upper_updated.append(np.percentile(bootstrap_predictions_updated, upper_percentile))
    
    lower_bound_updated = np.percentile(bootstrap_lower_updated, 50)
    upper_bound_updated = np.percentile(bootstrap_upper_updated, 50)

    
    # Create a concrete model
    model = ConcreteModel()
    
    # Define the decision variables
    model.price = Var(data.index, domain=NonNegativeReals)
    
    # Define the objective function
    def objective_rule(model):
        return sum(data.loc[i, target_column] * model.price[i] for i in data.index)
    model.objective = Objective(rule=objective_rule, sense=maximize)
    
    # Remove the existing constraints from the model
    if hasattr(model, 'price_lower_limit_constraint'):
        model.del_component(model.price_lower_limit_constraint)
    if hasattr(model, 'price_upper_limit_constraint'):
        model.del_component(model.price_upper_limit_constraint)
        
        # Competitor price constraints for Indoor
    for i in data.index:
        year = recent_month_str.split()[0]
        if year in ['2022', '2023']:  # This list can be extended for future years
            constraint_column = [column for column in data.columns if year in column and "Comp price" in column]
            if constraint_column in data.columns:
                model.add_constraint(model.price[i] <= 1.05 * data.loc[i, constraint_column])
    
    # Ask the user for the upper limit percentage (e.g. 1.1 for 110% of market price)
    price_upper_limit = upper_limit #Can be changed
    
    # Define the upper limit constraint for each property's price (must be <= specified percentage of market price)
    def price_upper_limit_constraint_rule(model, i):
        prefix = f'Market Price ({recent_month_str})'
        return model.price[i] <= price_upper_limit * data.loc[i, [col for col in data.columns if col.startswith(prefix)][0]]
    model.price_upper_limit_constraint = Constraint(data.index, rule=price_upper_limit_constraint_rule)
    
    # Ask the user for the lower limit percentage (e.g. 0.9 for 90% of market price)
    price_lower_limit = lower_limit # Can be changed
    
    def price_lower_limit_constraint_rule(model, i):
        prefix = f'Market Price ({recent_month_str})'
        return model.price[i] >= data.loc[i, [col for col in data.columns if col.startswith(prefix)][0]]
    model.price_lower_limit_constraint = Constraint(data.index, rule=price_lower_limit_constraint_rule)
     
    solver = SolverFactory('glpk')
    solver.solve(model)
    
    # After solving the model
    optimal_prices = [model.price[i].value for i in data.index]
    #max_revenue = model.objective()
    
    previous_month_current_prices = data[previous_month_column]
    
    return optimal_prices,previous_month_current_prices,data,y_test,y_pred,lower_bound_updated,upper_bound_updated
    


# Streamlit app
def main():
    st.set_page_config(
      page_title="QuadReal - Parking & Storage Revenue Optimization PILOT",
      page_icon="",
      initial_sidebar_state="collapsed",
      layout="wide"
    )
    
    hide_st_style = '''
      <style>
        # header {visibility: hidden;}
        footer {visibility: hidden;}
        # ul {display: none;}
        # div[data-testid="stSidebarNav"] {display: none;}
        .block-container {
          padding-top: 2rem;
          padding-bottom: 0rem;
          padding-left: 1rem;
          padding-right: 1rem;
        }
      </style>
    '''
    
    st.markdown(hide_st_style, unsafe_allow_html=True)
    
    st.sidebar.info(
      '''
      Add application info here. \n
      Copyright &copy; 2023 - QuadReal Properties Group LP - ED&A Team. All rights reserved.
      ''')
      

    show_manual = st.sidebar.checkbox("Show Manual")
    if show_manual:
        path = "User_Manual.docx"
        display_manual(path)

    
    display = Image.open("img/quadreal-logo.png")
    display = np.array(display)
    
    logo, title = st.columns([1, 5])
    with logo:
      st.image(display, width = 150)
    with title:
      title = st.title("QuadReal | Parking & Storage Revenue Optimization `v.0.1.0`")


    uploaded_file = st.file_uploader("Upload monthly data file(s) Please use the format of 'year month'" , type="xlsx", accept_multiple_files=True)

    if uploaded_file is not None:
        all_files_processed_successfully = True
        
        with st.spinner("Processing..."):
            for file in uploaded_file:
                try:
                    process_data_file(file)
                except ValueError as e:
                    st.error(str(e))
                    all_files_processed_successfully = False
            if all_files_processed_successfully and len(uploaded_file) > 0:
                st.success('Monthly data file(s) successfully processed and saved.')
            elif len(uploaded_file) == 0:
                x = 1
            
        
    indooryear = st.text_input("What year is the first indoor parking comp price?", "")
    outdooryear = st.text_input("What year is the first outdoor parking comp price?", "")
    storageyear = st.text_input("What year is the first storage parking comp price?", "")
    specific_file = st.file_uploader("Upload the file contain comp prices'Parking Storage Rev Final v1.xlsx'", type="xlsx")
    if specific_file is not None: 
        all_files_processed_successfully = True
        
        with st.spinner("Processing..."):
            if not indooryear or not outdooryear or not storageyear:
                st.error("Please enter values for all year inputs.")
                all_files_processed_successfully = False
            else:
                try:
                    process_price_file(specific_file, "Parking Storage Rev Final v1.xlsx",indooryear,outdooryear,storageyear)
    
                except ValueError as e:
                    st.error(str(e))
                    all_files_processed_successfully = False
            if all_files_processed_successfully:
                st.success('Parking Rev sheet successfully saved .')
                st.success('Storage Rev sheet successfully saved .')
    
    run_code = st.button("Show current datasets")

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
        with st.spinner("Combining CSV files..."):
            combine_csv_files()
            st.success("CSV files saved successfully.")

    st.title("Optimization")
    upper_limit = st.number_input("Enter a float number for price upper limit(default = 1.1)", step=0.01)  # Prompt user for input
    lower_limit = st.number_input("Enter a float number for price lower limit(default = 0.9)", step=0.01)  # Prompt user for input
    
    
    if st.button("Run Indoor Parking Optimization"):
        with st.spinner("Running Indoor Parking Optimization on selected CSV file..."):
            data = pd.read_csv("Final datasets\indoor_parking.csv")
            Indoor_optimal_prices,previous_month_current_prices,dataset,y_test,y_pred,lower_bound_updated,upper_bound_updated = Opt(data,upper_limit,lower_limit)
            

            
            plt.figure(figsize=(12, 6))
            plt.plot(dataset.index, Indoor_optimal_prices, label='Optimized Prices')
            plt.plot(dataset.index, previous_month_current_prices, label='Previous Month Current Prices')
            plt.xlabel('Properties')
            plt.ylabel('Prices')
            plt.legend()
            plt.title('Comparison of Optimized Prices and Previous Month Current Prices')            
            st.pyplot(plt)
            plt.show()
            
            Indoor_df = pd.DataFrame({
            'Property Code': dataset['Property Code'],
            'Optimized Prices': Indoor_optimal_prices,
            'Previous Month Current Prices': previous_month_current_prices,
            'Difference': [optimal - previous for optimal, previous in zip(Indoor_optimal_prices, previous_month_current_prices)]})
            st.subheader("Indoor Price for next month")
            ag_grid = st_aggrid.AgGrid(Indoor_df, height=300)
            Indoor_df.to_csv('Indoor_optimal_prices.csv', index=False)
        
        
    if st.button("Run Outdoor Parking Optimization"):
        with st.spinner("Running Outdoor Parking Optimization on selected CSV file..."):
        #user_input = st.number_input("Enter a float number for price upper limit(default = 1.1)", step=0.01)  # Prompt user for input
            data = pd.read_csv("Final datasets\outdoor_parking.csv")
            Outdoor_optimal_prices,previous_month_current_prices,dataset,y_test,y_pred,lower_bound_updated,upper_bound_updated = Opt(data,upper_limit,lower_limit)
 
            
            plt.figure(figsize=(12, 6))
            plt.plot(dataset.index, Outdoor_optimal_prices, label='Optimized Prices')
            plt.plot(dataset.index, previous_month_current_prices, label='Previous Month Current Prices')
            plt.xlabel('Properties')
            plt.ylabel('Prices')
            plt.legend()
            plt.title('Comparison of Optimized Prices and Previous Month Current Prices')
            
            st.pyplot(plt)
            plt.show()
            
            Outdoor_df = pd.DataFrame({
            'Property Code': dataset['Property Code'],
            'Optimized Prices': Outdoor_optimal_prices,
            'Previous Month Current Prices': previous_month_current_prices,
            'Difference': [optimal - previous for optimal, previous in zip(Outdoor_optimal_prices, previous_month_current_prices)]})
            st.subheader("Outdoor Price for next month")
            ag_grid = st_aggrid.AgGrid(Outdoor_df, height=300)
            Outdoor_df.to_csv('Outdoor_optimal_prices.csv', index=False)

    if st.button("Run Storage Optimization"):
        with st.spinner("Running Storage Optimization on selected CSV file..."):
            data = pd.read_csv("Final datasets\storage.csv")
            Storage_optimal_prices,previous_month_current_prices,dataset,y_test,y_pred,lower_bound_updated,upper_bound_updated = Opt(data,upper_limit,lower_limit)
       
            plt.figure(figsize=(12, 6))
            plt.plot(dataset.index, Storage_optimal_prices, label='Optimized Prices')
            plt.plot(dataset.index, previous_month_current_prices, label='Previous Month Current Prices')
            plt.xlabel('Properties')
            plt.ylabel('Prices')
            plt.legend()
            plt.title('Comparison of Optimized Prices and Previous Month Current Prices')
            
            st.pyplot(plt)
            plt.show()
            
            Storage_df = pd.DataFrame({
            'Property Code': dataset['Property Code'],
            'Optimized Prices': Storage_optimal_prices,
            'Previous Month Current Prices': previous_month_current_prices,
            'Difference': [optimal - previous for optimal, previous in zip(Storage_optimal_prices, previous_month_current_prices)]})
            st.subheader("Storage Price for next month")
            ag_grid = st_aggrid.AgGrid(Storage_df, height=300)
            Storage_df.to_csv('Storage_optimal_prices.csv', index=False)
    



if __name__ == '__main__':
    main()