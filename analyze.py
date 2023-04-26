# -*- coding: utf-8 -*-
#!/usr/bin/env python3

"""
Analyze the impact of California's NEM policy on DER investment decisions.

Created on Tue Apr 25 2022

@author: pswild
"""

import os
import pandas as pd

# API keys. 
CAISO_API_KEY = 'AUTHENTICATE MY DAMN REQUEST PLEASE'
NREL_API_KEY = 'yqjUGnkgdH4m8XrGh6OXi8rK7JMLJh6q3PafSMls'
EIA_API_KEY = 'GbKYer2Pz9JS0UttTjwxahbfN5ZzDKE0ZuyjsJQY'

#--- PATH ---# 

# Get path.
here = os.path.dirname(os.path.realpath(__file__))

#--- DATA ---#

# CAISO interconnection data. 
pge_sites_file = os.path.join(here, 'data/Interconnected_Project_Sites_2023-03-31/PGE_Interconnected_Project_Sites_2023-03-31.csv')
sce_sites_file = os.path.join(here, 'data/Interconnected_Project_Sites_2023-03-31/SCE_Interconnected_Project_Sites_2023-03-31.csv')
sdge_sites_file = os.path.join(here, 'data/Interconnected_Project_Sites_2023-03-31/SDGE_Interconnected_Project_Sites_2023-03-31.csv')

# CAISO locational marginal price data.
lmp_file = os.path.join(here, 'data/lmps.csv')

# SAM representative generation profile(s). 
sam_gen_file = os.path.join(here, 'data/pv_gen_profile.csv')

#--- OUTPUT ---# 

# Revenue under flat rate. 
rev_flat_file = os.path.join(here, 'output/rev_flat.csv')

# Revenue under LMPs. 
rev_lmp_file = os.path.join(here, 'output/rev_lmp.csv')

#--- TARIFFS ---#

# Data structures for each utility's version of NEM 1.0 and 2.0.

#--- FUNCTIONS ---#

def sites():
     '''Get distribtued generation interconnection program data from CAISO.'''

     # Directory path. 
     dir = 'data/Interconnected_Project_Sites_2023-03-31/'

     # Dataframe for sites. 
     sites = pd.DataFrame()

     # Combine interconnection data from all utilities.
     for file in os.listdir(dir):

          # Update path.
          path = os.path.join(dir, file)

          # Columns.
          cols = [
               
          ]

          # Read day into dataframe. 
          day = pd.read_csv(path, skiprows=[0,1,2,3,5], index_col=False)

          # Strip extraneous information.
          day.drop(columns=['H'], inplace=True)

          # Append day to year. 
          year = pd.concat([year, day], ignore_index=True)
     
     # Combine to datetime. 
     year['Date'] = pd.to_datetime(year['Date'] + ' ' + year['Time'])

     # Sort by date.
     year.sort_values(by=['Date'], inplace=True, ignore_index=True)
     
     # Floor date to hour.
     year['Date'] = year['Date'].dt.floor(freq='H')
     
     # Format date. 
     year['Date'] = year['Date'].dt.strftime('%m-%d %H:%M')

     # Drop unused columns.
     year = year[['Date', 'Fuel Category', 'Gen Mw', 'Marginal Flag']]

     # Drop NaNs.
     year.dropna(inplace=True)

     # Aggregate by fuel type for each hour. 
     # NOTE: this simply takes the average of generation by fuel type across reporting intervals.
     # NOTE: this simply treats whichever resource was marginal first as that which was marginal throughout the hour.
     year = year.groupby(['Date', 'Fuel Category'], as_index=False).agg({'Gen Mw': 'mean', 'Marginal Flag': 'first'})

     # Rename columns. 
     year.rename({'Gen Mw': 'Generation (MWh)'}, axis='columns', inplace=True)

     # Write dataframe to CSV.
     year.to_csv(iso_gen_file, index=False)

     return year

def lmp():
     '''Get real-time locational marginal prices for CAISO in 2022.'''

     # Directory path. 
     dir = 'data/lmps_2021'

     # Year of data. 
     year = pd.DataFrame()

     # Combine locational marginal price data.
     for file in os.listdir(dir):

          # Update path.
          path = os.path.join(dir, file)

          # Read day into dataframe. 
          day = pd.read_csv(path, skiprows=[0,1,2,3,5], index_col=False)

          # Strip extraneous information.
          day.drop(columns=['H'], inplace=True)

          # Select subset of LMPs for one location. 
          day = day.loc[day['Location ID'] == location_id]

          # Convert hours to numeric type. 
          day['Hour Ending'] = pd.to_numeric(day['Hour Ending'])

          # Append day to year. 
          year = pd.concat([year, day], ignore_index=True)

     # Combine to datetime. 
     year['Date'] = pd.to_datetime(year['Date']) + pd.to_timedelta(year['Hour Ending'] - 1, unit='h')

     # Format date. 
     year['Date'] = year['Date'].dt.strftime('%m-%d %H:%M')

     # Sort by date.
     year.sort_values(by=['Date'], inplace=True, ignore_index=True)
          
     # Drop unused columns.
     year = year[['Date', 'Location ID', 'Location Name', 'Locational Marginal Price']]

     # Drop NaNs.
     year.dropna(inplace=True)

     # Write dataframe to CSV.
     year.to_csv(lmp_file, index=False)

     return year

if __name__ == '__main__':

    # TBD