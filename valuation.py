# -*- coding: utf-8 -*-
#!/usr/bin/env python3

"""
Investigate how different tariff structures affect the value of distributed solar in California.

Created on Tue Apr 25 2022

@author: pswild
"""

import os
import pandas as pd

# Silence warnings...
pd.options.mode.chained_assignment = None

# API keys. 
NREL_API_KEY = 'yqjUGnkgdH4m8XrGh6OXi8rK7JMLJh6q3PafSMls'
EIA_API_KEY = 'GbKYer2Pz9JS0UttTjwxahbfN5ZzDKE0ZuyjsJQY'

#--- PATH ---# 

# Get path.
here = os.path.dirname(os.path.realpath(__file__))

#--- DATA ---#

# Distributed generation interconnection program data for California.
site_file = os.path.join(here, 'data/Aggregated_Sites.csv')

# Representative generation profiles from NREL's System Advisor Model (SAM). 
gen_file = os.path.join(here, 'data/Aggregated_Gen.csv')

# Time-of-use rate structures for net energy metering tariffs.
tou_file = os.path.join(here, 'data/Aggregated_TOUs.csv')

# Locational marginal prices at default Load Aggregation Points (LAPs) in 2022 from CAISO. 
lmp_file = os.path.join(here, 'data/Aggregated_LMPs.csv')

#--- OUTPUT ---# 

# Normalized value of solar by configuration. 
norm_val_file = os.path.join(here, 'output/Norm_Val_by_Config.csv')

# Annual value of each site. 
site_val_file = os.path.join(here, 'output/Annual_Site_Vals.csv')

#--- GENERATION PROFILES ---#

# Representative generation profile names. 
gen_profile_names = [
     'PGE_FIXED_ROOFTOP_T18_A180_NORM',
     'SCE_FIXED_ROOFTOP_T18_A180_NORM', 
     'SDGE_FIXED_ROOFTOP_T18_A180_NORM'
]

#--- TARIFF MAP ---#

# Hypothetical flat rates based on middle tier of default tariffs (for NEM 1.0).
flat_rates = {
     'PGE': 0.39468,
     'SCE': 0.24623,
     'SDGE': 0.49477
}

# Structure for default time-of-use rates from URDB (for NEM 2.0).
tou_rates = {
     'PGE': 'PGE_14328',
     'SCE': 'SCE_17609',
     'SDGE': 'SDGE_17609'
}

#--- NODE MAP ---#

# From utility to node.
utility_to_node = {
     'PGE': 'DLAP_PGAE-APND',
     'SCE': 'DLAP_SCE-APND',
     'SDGE': 'DLAP_SDGE-APND'
}

#--- FUNCTIONS ---#

def valuation(sites, gens, tous, lmps):
     '''Calculate value of solar generation under flat rates, TOU rates, and LMPs.'''

     norm_vals = gens.copy()

     # Normalized annual value of each configuration based on its tariff structure.
     nav = pd.DataFrame(
          columns=[
               'Utility', 
               'Normalized Value - Flat Rate',
               'Normalized Value - TOU Rate',
               'Normalized Value - LMP'
          ]
     )

     for gen_profile in gen_profile_names: 

          # NOTE: identifier for unique generation profile (in this case, utility suffices).
          utility = gen_profile.split('_')[0]

          # Column names. 
          gen_col = utility + ' Normalized Generation'
          flat_rate_col = utility + ' Flat Rate'
          tou_rate_col = utility + ' TOU Rate'
          lmp_rate_col = utility + ' LMP'
          flat_val_col = utility + ' Normalized Value - Flat Rate'
          tou_val_col = utility + ' Normalized Value - TOU Rate'
          lmp_val_col = utility + ' Normalized Value - LMP'
          flat_v_lmp_val_col = utility + ' Difference in Value of 1 kW Solar - Flat Rate v LMP'
          tou_v_lmp_val_col = utility + ' Difference in Value of 1 kW Solar - TOU Rate v LMP'

          # Rename generation column.
          norm_vals.rename(columns={gen_profile: gen_col}, inplace=True)          

          #--- Add Flat Rate ---#

          # Add column for flat rate. 
          norm_vals[flat_rate_col] = flat_rates[utility]

          #--- Add TOU Rate ---#

          # Identify TOU rate for utility.
          tou_rate_name = tou_rates[utility]

          # Drop unused columns.
          tou_slice = tous[['Timestamp', tou_rate_name]]

          # Rename column. 
          tou_slice.rename(columns={tou_rate_name: tou_rate_col}, inplace=True)

          # Add column for TOU rate.
          norm_vals = norm_vals.merge(tou_slice, on='Timestamp')

          #--- Add LMPs ---#

          # Identify nearest node to utility.
          node_id = utility_to_node[utility]
          
          # Get LMPs for nearest node.
          lmp_slice = lmps.loc[(lmps['NODE_ID'] == node_id) & (lmps['LMP_TYPE'] == 'LMP')]

          # Format LMPs. 
          lmp_slice[lmp_rate_col] = lmp_slice['MW'] / 1000

          # Drop unused columns. 
          lmp_slice = lmp_slice[['Timestamp', lmp_rate_col]]

          # Add column for LMPs. 
          norm_vals = norm_vals.merge(lmp_slice, on='Timestamp')

          #--- Normalized Hourly Valuation ($/kWcap/hour) ---#

          # NOTE: this is essentially the value created in a given hour by a 1 kW system 
          # under each tariff structures, which can then be scaled by system capacity.

          # Compute normalized value of solar for each configuration under flat rate.
          norm_vals[flat_val_col] = norm_vals[gen_col] * norm_vals[flat_rate_col]

          # Compute normalized value of solar for each configuration under TOU rate.
          norm_vals[tou_val_col] = norm_vals[gen_col] * norm_vals[tou_rate_col]

          # Compute normalized value of solar for each configuration under LMPs.
          norm_vals[lmp_val_col] = norm_vals[gen_col] * norm_vals[lmp_rate_col]

          # Compute percentage difference in normalized value of solar between NEM rates and LMPs.
          norm_vals[flat_v_lmp_val_col] = (norm_vals[flat_val_col] - norm_vals[lmp_val_col])/norm_vals[lmp_val_col]
          norm_vals[tou_v_lmp_val_col] = (norm_vals[tou_val_col] - norm_vals[lmp_val_col])/norm_vals[lmp_val_col]

          #--- Normalized Annual Valuation ($/kWcap/year) ---#

          # NOTE: this is just a sum of all hourly value created by a 1 kW system over
          # the course of a year, which can then be scaled by system capacity. 

          # Compute normalized annual value of solar for each configuration and tariff structure. 
          nav = nav.append({
               'Utility': utility, 
               'Normalized Annual Value - Flat Rate': norm_vals[flat_val_col].sum(),
               'Normalized Annual Value - TOU Rate': norm_vals[tou_val_col].sum(),
               'Normalized Annual Value - LMP': norm_vals[lmp_val_col].sum()
          }, ignore_index=True)

     # Write to CSV.
     norm_vals.to_csv(norm_val_file, index=False)

     # Merge normalized annual value data onto sites based on configuration (which is just utility in this case). 
     sites = sites.merge(nav, on='Utility')

     # Combine normalized annual value columns for NEM.
     sites['Normalized Annual Value - NEM'] = None

     sites.loc[sites['NEM Tariff'].astype(str) == '1.0', 'Normalized Annual Value - NEM'] = sites['Normalized Annual Value - Flat Rate']
     sites.loc[sites['NEM Tariff'].astype(str) == '2.0', 'Normalized Annual Value - NEM'] = sites['Normalized Annual Value - TOU Rate']

     # Compute annual values.
     sites['Annual Value - NEM'] = None
     sites['Annual Value - LMP'] = None

     sites.loc[sites['NEM Tariff'].astype(str) == '1.0', 'Annual Value - NEM'] = sites['Normalized Annual Value - Flat Rate'] * sites['System Size AC']
     sites.loc[sites['NEM Tariff'].astype(str) == '2.0', 'Annual Value - NEM'] = sites['Normalized Annual Value - TOU Rate'] * sites['System Size AC']
     sites['Annual Value - LMP'] = sites['Normalized Annual Value - LMP'] * sites['System Size AC']

     # Columns to keep.
     usecols = [
          'Utility',
          'NEM Tariff',
          'System Size AC',
          'Normalized Annual Value - Flat Rate',
          'Normalized Annual Value - TOU Rate',
          'Normalized Annual Value - NEM',          
          'Normalized Annual Value - LMP',
          'Annual Value - NEM',
          'Annual Value - LMP'
     ]

     # Drop unused columns. 
     site_vals = sites[usecols]

     # Write dataframe to CSV.
     site_vals.to_csv(site_val_file, index=False)

     return

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
     
     #--- Generation Profiles ---#

     gens = None

     if os.path.exists(gen_file):
          gens = pd.read_csv(gen_file)
     else:
          raise Exception('Please get generation data using gen.ipynb.')
     
     #--- Time-of-Use Rates ---#

     tous = None

     if os.path.exists(tou_file):
          tous = pd.read_csv(tou_file)
     else:
          raise Exception('Please get rate structures using tous.ipynb.')

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
     valuation(sites, gens, tous, lmps)