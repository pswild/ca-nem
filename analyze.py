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
NREL_API_KEY = 'yqjUGnkgdH4m8XrGh6OXi8rK7JMLJh6q3PafSMls'
EIA_API_KEY = 'GbKYer2Pz9JS0UttTjwxahbfN5ZzDKE0ZuyjsJQY'

#--- PATH ---# 

# Get path.
here = os.path.dirname(os.path.realpath(__file__))

#--- DATA ---#

# Distributed generation interconnection program data for California.
site_file = os.path.join(here, 'data/Interconnected_Project_Sites_2023-03-31/CAISO_Interconnected_Project_Sites_2023-03-31.csv')

# Directory of representative generation profiles from NREL's System Advisor Model (SAM). 
sam_dir = os.path.join(here, 'data/SAM_Generation_Profiles/')

# Locational marginal prices at default Load Aggregation Points (LAPs) in 2022 from CAISO. 
lmp_file = os.path.join(here, 'data/CAISO_LMPs/2022/DLAP_PGAE-APND, DLAP_SCE-APND, DLAP_SDGE-APND/Aggregated_LMPs.csv')

#--- OUTPUT ---# 

# Revenue under NEM. 
nem_rev_file = os.path.join(here, 'output/nem_rev.csv')

# Revenue under LMPs. 
lmp_rev_file = os.path.join(here, 'output/rev_lmp.csv')

#--- TARIFFS ---#

# TODO: Data structures for each utility's version of NEM 1.0 and 2.0.
nems = {
     'PGE': {},
     'SCE': {},
     'SDGE': {}
}

#--- FUNCTIONS ---#

def nem():
     '''Calculate value under NEM tariffs.'''

     return

def lmp():
     '''Calculate value under LMP.'''
     
     return

if __name__ == '__main__':
    
     #--- Solar PV Sites ---#

     sites = None

     if os.path.exists(site_file):
          sites = pd.read_csv(site_file)
     else: 
          raise Exception('Please get site data using sites.ipynb.')

     print(sites)

     #--- Generation Profiles ---#

     # Dictionary of generation profiles.
     profiles = {}

     for file in os.listdir(sam_dir):
     
          # Read file.
          path = os.path.join(sam_dir, file)
          df = pd.read_csv(path, header=0, names=['Timestamp', 'kW'], encoding='utf-8')

          # Convert to datetime.
          df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%b %d, %I:%M %p')

          # Fix year.
          df['Timestamp'] = df['Timestamp'].apply(lambda dt: dt.replace(year=2022))

          # Add to dictionary.
          profiles[file] = df
     
     print(profiles)

     #--- Locational Marginal Prices ---#

     lmps = None

     if os.path.exists(lmp_file):
          lmps = pd.read_csv(lmp_file)
     else: 
          raise Exception('Please get locational marginal price data using lmps.ipynb.')

     print(lmps)