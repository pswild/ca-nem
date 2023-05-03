# -*- coding: utf-8 -*-
#!/usr/bin/env python3

"""
Analyze the impact of California's NEM policy on DER investment decisions.

Created on Tue Apr 25 2022

@author: pswild
"""

import os
import time
import glob
import requests
import pandas as pd
import zipfile as zp
from functools import reduce
from selenium import webdriver

# API keys. 
NREL_API_KEY = 'yqjUGnkgdH4m8XrGh6OXi8rK7JMLJh6q3PafSMls'
EIA_API_KEY = 'GbKYer2Pz9JS0UttTjwxahbfN5ZzDKE0ZuyjsJQY'

#--- PATH ---# 

# Get path.
here = os.path.dirname(os.path.realpath(__file__))

#--- DATA ---#

# Site file.
site_file = os.path.join(here, 'data/Interconnected_Project_Sites_2023-03-31/CAISO_Interconnected_Project_Sites_2023-03-31.csv')

# CAISO locational marginal price data.
lmp_file = os.path.join(here, 'data/CAISO_LMPs/2022/DLAP_PGAE-APND, DLAP_SCE-APND, DLAP_SDGE-APND/Aggregated_LMPs.csv')

#--- OUTPUT ---# 

# Revenue under flat rate. 
rev_flat_file = os.path.join(here, 'output/rev_flat.csv')

# Revenue under LMPs. 
rev_lmp_file = os.path.join(here, 'output/rev_lmp.csv')

#--- TARIFFS ---#

# Data structures for each utility's version of NEM 1.0 and 2.0.

#--- FUNCTIONS ---#

def get_sites():
     '''Get distributed generation interconnection program (i.e., Rule 21) data from CAISO.'''

     # Columns to keep.
     usecols = [
          'Application Id',
          'Utility',
          'Service City',
          'Service Zip',
          'Service County',
          'Technology Type',
          'System Size DC',
          'System Size AC',
          'Inverter Size (kW AC)',
          'Tilt',
          'Azimuth',
          'Mounting Method',
          'Tracking',
          'Customer Sector',
          'App Approved Date',
          'Total System Cost',
          'Itc Cost Basis',
          'NEM Tariff',
          'Interconnection Program',
          'VNEM, NEM-V, NEM-Agg',
          'Project is VNEM, NEM-V, NEM-Agg?',
          'NEMPV or nonNEMPV'
     ]

     # Utilities. 
     utilities = [
          'PGE',
          'SDGE',
          'SCE'
     ]

     # Technologies in which solar is the sole means of generation.
     # NOTE: should we include sites with storage?
     technologies = [
          'Solar PV',
          'Solar',
          'Solar PV, Storage',
          'Solar PV;Storage',
          'SOLAR PV',
          'Other, Solar PV',
          'Other, Solar PV, Storage'
     ]

     #--- LOAD ---#

     # Distributed generation site data.
     dir = 'data/Interconnected_Project_Sites_2023-03-31/'

     # Dataframe for sites. 
     df = pd.DataFrame()

     # Combine interconnection data from all utilities.
     for file in os.listdir(dir):

          path = os.path.join(dir, file)
          subset = pd.read_csv(path, usecols=usecols)
          df = pd.concat([df, subset])

     #--- FILTER ---#

     # Filter data by utility, customer sector, tariff structure, and technology type.
     df = df.loc[
          (df['Utility'].isin(utilities)) &
          (df['Customer Sector'] == 'Residential') &
          (df['NEMPV or nonNEMPV'] == 'NEMPV') & 
          (df['Technology Type'].isin(technologies))
     ]

     #--- CLEAN ---#

     # Convert to datetime.
     df['App Approved Date'] = pd.to_datetime(df['App Approved Date'])

     # Sort by date.
     df.sort_values(by=['App Approved Date'], ascending=False, inplace=True, ignore_index=True)
     
     # Convert ZIP codes to strings.
     df['Service Zip'] = df['Service Zip'].astype(str).str.zfill(5).str.slice(0, 5)

     # Convert tariff types to strings.
     df['NEM Tariff'] = df['NEM Tariff'].astype(str)

     # Convert strings to uppercase for nonnumeric columns.
     df = df.apply(lambda x: x.str.upper() if x.dtype == "object" else x)

     # Make labels compatible across utilities.
     df.loc[df['Technology Type'] == 'SOLAR', ['Technology Type']] = 'SOLAR PV'
     df.loc[df['Technology Type'] == 'OTHER, SOLAR PV', ['Technology Type']] = 'SOLAR PV'
     df.loc[df['Technology Type'] == 'SOLAR PV;STORAGE', ['Technology Type']] = 'SOLAR PV, STORAGE'
     df.loc[df['Technology Type'] == 'OTHER, SOLAR PV, STORAGE', ['Technology Type']] = 'SOLAR PV, STORAGE'
     df.loc[df['Mounting Method'] == 'MIXED', ['Mounting Method']] = 'MULTIPLE'
     df.loc[df['Tracking'] == 'MIXED', ['Tracking']] = 'MULTIPLE'
     df.loc[df['Tracking'] == 'TRACKING', ['Tracking']] = 'SINGLE-AXIS'

     #--- ASSUMPTIONS ---#

     # If no tilt or azimuth is specified, assign the most common value.
     df['Tilt'].fillna(value=df['Tilt'].value_counts().index[0], inplace=True) # 18.0
     df['Azimuth'].fillna(value=df['Azimuth'].value_counts().index[0], inplace=True) # 180.0

     # For sites with multiple tilts or azimuths, assign most common value.
     df.loc[df['Tilt'] == 'MULTIPLE', ['Tilt']] = df['Tilt'].value_counts().index[0] # 18.0
     df.loc[df['Azimuth'] == 'MULTIPLE', ['Azimuth']] = df['Azimuth'].value_counts().index[0] # 180.0

     # Convert tilt and azimuth to floats (and assign NaNs for tracking systems).
     df['Tilt'] = pd.to_numeric(df['Tilt'], errors='coerce')
     df['Azimuth'] = pd.to_numeric(df['Azimuth'], errors='coerce')

     # If no mounting method or tracking style is specified, assign the most common value.
     df['Mounting Method'].fillna(value=df['Mounting Method'].value_counts().index[0], inplace=True)
     df['Tracking'].fillna(value=df['Tracking'].value_counts().index[0], inplace=True)

     # Replace instances of zero cost with NaNs.
     df.loc[df['Total System Cost'] == 0.0, ['Total System Cost']] = float('NaN')
     df.loc[df['Itc Cost Basis'] == 0.0, ['Itc Cost Basis']] = float('NaN')

     # Correct what are presumably erroneous negative system and inverter sizes.
     df['System Size DC'] = df['System Size DC'].abs()
     df['System Size AC'] = df['System Size AC'].abs()
     df['Inverter Size (kW AC)'] = df['Inverter Size (kW AC)'].abs()

     #--- EXPORT ---#

     # Write dataframe to CSV.
     df.to_csv(site_file, index=False)

     return df

def get_gen():
     '''Get normalized SAM generation profiles for each utility territory in CAISO.'''

     # Normalized SAM generation profile(s). 
     dir = 'data/SAM_Generation_Profiles/'

     # Dictionary for profiles.
     gens = {}

     for file in os.listdir(dir):
          
          path = os.path.join(dir, file)
          profile = pd.read_csv(path, encoding='latin-1')
          gens[file] = profile

     return gens

def get_lmps(year, nodes):
     '''Get hourly locational marginal prices corresponding to each utility territory from the 2022 Day Ahead Market (DAM).'''

     # Columns to keep.
     usecols = [
          'INTERVALSTARTTIME_GMT',
          'INTERVALENDTIME_GMT',
          'OPR_DT',
          'OPR_HR',
          'NODE_ID',
          'MARKET_RUN_ID',
          'LMP_TYPE',
          'XML_DATA_ITEM',
          'MW'
     ]

     # Dates for formatting URLs.
     month_dict = {
          'Jan': ['0101', '0201'],
          'Feb': ['0201', '0301'],
          'Mar': ['0301', '0401'],
          'Apr': ['0401', '0501'],
          'May': ['0501', '0601'],
          'Jun': ['0601', '0701'],
          'Jul': ['0701', '0801'],
          'Aug': ['0801', '0901'],
          'Sep': ['0901', '1001'],
          'Oct': ['1001', '1101'],
          'Nov': ['1101', '1201'],
          'Dec': ['1201', '0101']
     }

     # Default LAP (Load Aggregation Point) nodes corresponding to utility territories.
     lap_node_list = [
          'DLAP_PGAE-APND',
          'DLAP_SCE-APND',
          'DLAP_SDGE-APND',
          'DLAP_VEA-APND'
     ]

     # Format API call.
     node_entry = reduce(lambda x, y: x +','+ y, nodes)
     name_entry = reduce(lambda x, y: x +', '+ y, nodes)

     download_dir = f'/Users/parkerwild/GitHub/ca_nem/data/CAISO_LMPs/{str(year)}/{name_entry}'

     chrome_options = webdriver.ChromeOptions()
     prefs = {'download.default_directory' : download_dir}
     chrome_options.add_experimental_option('prefs', prefs)

     print('Accessing Chrome driver...')

     driver = webdriver.Chrome(options=chrome_options, executable_path='/Users/parkerwild/GitHub/ca_nem/chromedriver_mac64/chromedriver.exe')

     for month in month_dict.keys():

          # Handle daylight savings time.
          t = 'T08'

          if month in ['May', 'Jul', 'Aug', 'Oct']:
               t = 'T07'

          # Handle last day of year.
          start_year = year
          end_year = year

          if month == 'Dec':
               start_year = year
               end_year = year + 1

          # URL.
          api_call = "http://oasis.caiso.com/oasisapi/SingleZip?queryname=PRC_LMP&resultformat=6&" + \
               "startdatetime=" + str(start_year) + month_dict[month][0] + t + ":00-0000&" + \
               "enddatetime=" + str(end_year) + month_dict[month][1] + t + ":00-0000&" + \
               "version=1&market_run_id=DAM&node=" + node_entry
          
          print(f'Downloading data for {month}...')

          # Request.
          driver.get(api_call)

          time.sleep(15)

     print('Closing Chrome driver...')
     
     driver.close()

     print('Unzipping files...')
     
     zip_files = glob.glob(f'{download_dir}/*.zip')

     for zip_filename in zip_files:

          dir_name = os.path.splitext(zip_filename)[0]
          
          if not os.path.isdir(dir_name):
               os.mkdir(dir_name)

          zip_handler = zp.ZipFile(zip_filename, "r")
          zip_handler.extractall(dir_name)

     print('Concatenating CSVs...')

     csv_files = glob.glob(f'{download_dir}/*/*.csv')

     entries = []

     for csv in csv_files:

          df = pd.read_csv(csv)
          entries.append(df)

     lmps = pd.concat(entries)

     print('Cleaning data...')

     # Drop duplicates caused by Daylight Savings Time.
     lmps.drop_duplicates(subset=['OPR_DT', 'OPR_HR', 'NODE', 'XML_DATA_ITEM'], inplace=True, ignore_index=True)

     # Keep subset of columns.
     lmps = lmps[usecols]

     # Sort by interval start time.
     lmps.sort_values(by=['INTERVALSTARTTIME_GMT', 'NODE_ID', 'LMP_TYPE'], inplace=True, ignore_index=True)

     # Export to CSV.    
     lmps.to_csv(f'{download_dir}/Aggregated_LMPs.csv', index=False)

     print('Process complete!')

     return lmps

if __name__ == '__main__':
    
     #--- Solar PV Sites ---#

     sites = None

     if os.path.exists(site_file):
          sites = pd.read_csv(site_file)
     else: 
          sites = get_sites()

     print(sites)

     #--- Generation Profiles ---#

     gens = get_gen()

     print(gens)

     #--- Locational Marginal Prices ---#

     lmps = None

     if os.path.exists(lmp_file):
          lmps = pd.read_csv(lmp_file)
     else: 
          lmps = get_lmps(2022, ['DLAP_PGAE-APND', 'DLAP_SCE-APND', 'DLAP_SDGE-APND'])

     print(lmps)