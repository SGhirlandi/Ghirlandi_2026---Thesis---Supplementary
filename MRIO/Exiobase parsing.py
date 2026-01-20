#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 19 16:25:28 2025

@author: stefanoghirlandi
"""

import pandas as pd
import mario
from pathlib import Path

#% Create MARIO database through txt 
#IOT_aggregated = Path(__file__).parent /'Baseline.xlsx'
#IOT_aggregated = Path(__file__).parent / 'Recycling' / 'Input recycling - coefficients.xlsx'
IOT_aggregated = Path(__file__).parent /'LTE'/'LTE - coefficients - lower imports.xlsx'

mrio = mario.parse_from_excel(path=str(IOT_aggregated), 
                            table='IOT', 
                            #mode='flows',
                            mode='coefficients',
                            calc_all=True,
                            )

#%
Z = mrio.Z
Y = mrio.Y #Final demand
V = mrio.V
X = mrio.X #Total output
z = mrio.z
w = mrio.w #Leontieff inverse
v = mrio.v #Value added
e = mrio.e #Satellite accounts
f = mrio.f #footprint coefficients

x_EU = X.loc[pd.IndexSlice['EU27', :, :], :] 
x_EU = x_EU.squeeze()

v_EU = v.loc[:, pd.IndexSlice['EU27', :, :]]
v_EU = v_EU.squeeze()

e_EU = e.loc['Employment people', pd.IndexSlice['EU27', :, :]]
e_EU = e_EU.squeeze()

x_EU_total = x_EU.sum()

VA_EU = (v_EU * x_EU).sum()

Emp_EU = (x_EU * e_EU).sum()

print(VA_EU, Emp_EU, x_EU_total)

#%% Find x, v and e corresponding to Titanium in EU27

x_EU_tit = float(X.loc[
    pd.IndexSlice['EU27', 'Sector', 'Manufacturing of Titanium and articles thereof'], :
])

v_EU_tit = float(v.loc[
    :, 
    pd.IndexSlice['EU27', 'Sector', 'Manufacturing of Titanium and articles thereof']
])

e_EU_tit = float(e.loc[
    pd.IndexSlice['Employment people'],
    pd.IndexSlice['EU27', 'Sector', 'Manufacturing of Titanium and articles thereof']
])

w_EU_tit = float(w.loc[
    pd.IndexSlice['EU27', 'Sector', 'Manufacturing of Titanium and articles thereof'], 
    pd.IndexSlice['EU27', 'Sector', 'Manufacturing of Titanium and articles thereof']
])

#%% Value added and employement
value_added = x_EU_tit * v_EU_tit
employment = x_EU_tit * e_EU_tit

print(value_added, employment, x_EU_tit)

#%%
path = Path(__file__).parent / "Baseline scenario - coefficients.xlsx"
mrio.to_excel(path=path,
              coefficients=True,
              )
#%%
Output = Path(__file__).parent / "Flows and coefficients.xlsx"

with pd.ExcelWriter(Output, engine="xlsxwriter") as writer:
    Z.to_excel(writer, sheet_name="Z")
    Y.to_excel(writer, sheet_name="Y")
    V.to_excel(writer, sheet_name="V")   
    X.to_excel(writer, sheet_name="X")
    z.to_excel(writer, sheet_name="Intermediate coeff_z")
    v.to_excel(writer, sheet_name="ValueAdded_v")
    w.to_excel(writer, sheet_name="Leontief_w")
    
#%% Prepare the data
# Convert each emission Series to DataFrame with index as colum

# Optional: also prepare scalar indicators
scalar_df = pd.DataFrame({
    'Metric': ['Output (x)', 'Value Added (v)', 'Employment (e)', 'Total VA for EU', 'Total Emp for EU'],
    'Value': [float(x_EU_tit), float(v_EU_tit), float(e_EU_tit), float(VA_EU), float(Emp_EU)]
})

# Export to Excel
Indicators = Path(__file__).parent / "EU27__Indicators_LTE.xlsx"

with pd.ExcelWriter(Indicators) as writer:
    scalar_df.to_excel(writer, sheet_name='Summary', index=False)