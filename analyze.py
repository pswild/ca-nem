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
site_file = os.path.join(here, 'data/Interconnected_Project_Sites_2023-03-31/Aggregated_Sites.csv')

# Representative generation profiles from NREL's System Advisor Model (SAM). 
gen_file = os.path.join(here, 'data/SAM_Generation_Profiles/Aggregated_Profiles.csv')

# Locational marginal prices at default Load Aggregation Points (LAPs) in 2022 from CAISO. 
lmp_file = os.path.join(here, 'data/CAISO_LMPs/2022/DLAP_PGAE-APND, DLAP_SCE-APND, DLAP_SDGE-APND/Aggregated_LMPs.csv')

#--- OUTPUT ---# 

# Value of solar generation under NEM. 
nem_vosg_file = os.path.join(here, 'output/nem_vosg.csv')

# Value of solar under LMPs. 
lmp_vosg_file = os.path.join(here, 'output/lmp_vosg.csv')

#--- TARIFFS ---#

# TODO: Data structures for each utility's version of NEM (1.0 and 2.0).
nems = {
     'PGE': {},
     'SCE': {},
     'SDGE': {}
}

#--- PROFILES ---#

# Profile names. 
profile_names = [
     'PGE_FIXED_ROOFTOP_T18_A180_NORM',
     'SCE_FIXED_ROOFTOP_T18_A180_NORM', 
     'SDGE_FIXED_ROOFTOP_T18_A180_NORM'
]

#--- CROSSWALKS ---#

# From region to node.
region_to_node = {
     'PGE': 'DLAP_PGAE-APND',
     'SCE': 'DLAP_SCE-APND',
     'SDGE': 'DLAP_SDGE-APND'
}

#--- FUNCTIONS ---#

def valuation(sites, profiles, lmps):
     '''Calculate value of solar generation under NEM and LMPs.'''

     # Create values dataframe.
     values = profiles.copy()

     for profile in profile_names: 

          # Region.
          region = profile.split('_')[0]

          # Column names. 
          nem_rate_col = region + ' NEM Rate ($/kW)'
          lmp_rate_col = region + ' LMP Rate ($/kW)'
          nem_val_col = region + ' Normalized NEM Value'
          lmp_val_col = region + ' Normalized LMP Value'

          #--- Add NEM Rate ---#

          # TODO: NEM

          #--- Add LMP Rate ---#

          # Identify nearest node to region.
          node_id = region_to_node[region]
          
          # Get LMPs for nearest node.
          lmp_slice = lmps.loc[(lmps['NODE_ID'] == node_id) & (lmps['LMP_TYPE'] == 'LMP')]

          # Format LMPs. 
          lmp_slice[lmp_rate_col] = lmp_slice['MW'] / 1000

          # Drop unused columns. 
          lmp_slice = lmp_slice[['Timestamp', lmp_rate_col]]

          # Add column for LMPs. 
          values = values.merge(lmp_slice, on='Timestamp')

          #--- Normalized Values ---#

          # TODO: Compute normalized value of solar under NEM.
          # values[nem_val_col] = values[profile] * values[nem_rate_col]

          # Compute normalized value of solar under LMPs.
          values[lmp_val_col] = values[profile] * values[lmp_rate_col]

     return values

if __name__ == '__main__':

     #################
     ### LOAD DATA ###
     #################

     #--- Solar PV Sites ---#

     sites = None

     if os.path.exists(site_file):
          sites = pd.read_csv(site_file)
     else: 
          raise Exception('Please get site data using sites.ipynb.')
     
     #--- Representative Generation Profiles ---#

     profiles = None

     if os.path.exists(gen_file):
          profiles = pd.read_csv(gen_file)
     else:
          raise Exception('Please get generation data using generation.ipynb.')

     #--- Locational Marginal Prices ---#

     lmps = None

     if os.path.exists(lmp_file):
          lmps = pd.read_csv(lmp_file)
     else: 
          raise Exception('Please get pricing data using lmps.ipynb.')
          
     ###########################################
     ### CALCULATE VALUE OF SOLAR GENERATION ###
     ###########################################

     # Calculate value of solar generation.
     values = valuation(sites, profiles, lmps)
     