#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  6 15:44:16 2025

@author: stefanoghirlandi
"""

import pandas as pd
import numpy as np
import mario
from pathlib import Path

#%% 1. Create MARIO database by parsing Exiobase 2019
IOT_2019_ixi = Path(__file__).parent/'IOT_2019_ixi.zip'
print("Exists?", IOT_2019_ixi.exists())

mrio = mario.parse_exiobase_3(path=IOT_2019_ixi, calc_all=True, year=2019, name='IOT_2019')

mrio # check MARIO properties


#%% 2. Get aggregation excel through excel
Aggregation_module = Path(__file__).parent/'Aggregation module.xlsx'
#mrio.get_aggregation_excel(Aggregation_module)

#%% 3. Import aggregation excel
mrio.aggregate(Aggregation_module, ignore_nan=True)

mrio # Check and compare properties

print(mrio.Z)

#%% 4. Export aggregated dataset in txt format

path_txt_aggr = Path(__file__).parent /'IOT aggregated'

mrio.to_txt(path=path_txt_aggr,
            flows= True,
            coefficients= True, 
            #unit=True, # Indicated as arguement in the API, but not in this function
            sep=',')

#%% Export in excel format

path_exc_aggr = Path(__file__).parent / 'IOT_Aggregated_July.xlsx'

mrio.to_excel(path=path_exc_aggr,
            flows= True,
            coefficients= True, 
            #unit=True, # Indicated as arguement in the API, but not in this function
            )