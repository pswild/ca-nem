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

# Site file.
site_file = os.path.join(here, 'data/CAISO_Interconnected_Project_Sites_2023-03-31.csv')

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

def intercon():
     '''Load distributed generation interconnection program data from CAISO.'''

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

     # Directory.
     dir = 'data/Interconnected_Project_Sites_2023-03-31/'

     # Dataframe for sites. 
     df = pd.DataFrame()

     # Combine interconnection data from all utilities.
     for file in os.listdir(dir):

          # Update path.
          path = os.path.join(dir, file)

          # Read data from one utility into dataframe. 
          subset = pd.read_csv(path, usecols=usecols)

          # Append. 
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

     # For sites with  multiple tilts or azimuths, assign most common value.
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

def lmps():
     '''Get real-time locational marginal prices for CAISO in 2022.'''

     return

if __name__ == '__main__':
    
     #--- Distributed Generation Interconnections ---#

     sites = None

     # Load distributed generation interconnction data.
     if os.path.exists(site_file):
          sites = pd.read_csv(site_file)
     else: 
          sites = intercon()

     print(sites)