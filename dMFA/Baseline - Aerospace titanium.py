#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 20:02:24 2025

@author: stefanoghirlandi
"""

import numpy as np
import scipy.stats
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

path = Path(__file__).parent / 'Stock input data.xlsx'
planes = pd.read_excel(path, sheet_name="Stock of planes in EU27")
planes = planes.rename(columns={"Stock (nº of planes)": "stock"}).set_index('Year')
planes.index = planes.index.astype(int)

start_year, end_year = 1970, 2060
full_years = np.arange(start_year, end_year + 1)
n_years = len(full_years)

#%%
planes_projection = pd.DataFrame(index=full_years)

# === Backcast: Stock before 2000 ===
curve_mean, curve_sd = 1985, 10
normal_cdf = scipy.stats.norm.cdf(full_years, loc=curve_mean, scale=curve_sd)
target_stock_2000 = planes.loc[2000, 'stock']
normal_cdf_scaled = normal_cdf / normal_cdf[full_years == 2000][0] * target_stock_2000

planes_projection['stock'] = 0.0
planes_projection.loc[1970:1999, 'stock'] = normal_cdf_scaled[full_years < 2000]
planes_projection.loc[planes.index, 'stock'] = planes['stock']  # use observed stock 2000–2023

# === Forecast: Stock 2023–2040 using scaled normal curve ===
stock_2023 = planes.loc[2023, 'stock']
stock_target = 8000
forecast_years = np.arange(2023, 2061)

# build and scale the CDF
curve_mean_forecast, curve_sd_forecast = 2040, 10
normal_cdf_forecast = scipy.stats.norm.cdf(forecast_years, loc=curve_mean_forecast, scale=curve_sd_forecast)
normal_cdf_scaled_forecast = (normal_cdf_forecast - normal_cdf_forecast[0]) / (normal_cdf_forecast[-1] - normal_cdf_forecast[0])
scaled_stock_forecast = stock_2023 + normal_cdf_scaled_forecast * (stock_target - stock_2023)

planes_projection.loc[forecast_years, 'stock'] = scaled_stock_forecast

# === Flow calculations ===
planes_projection['inflow'] = 0.0
planes_projection['outflow'] = 0.0
planes_projection['nas'] = 0.0

# === Survival function ===
curve_surv_mean, curve_surv_sd = 25, 12.5
curve_surv = scipy.stats.norm.sf(np.arange(n_years), loc=curve_surv_mean, scale=curve_surv_sd)
curve_surv /= curve_surv[0]  # ensure starts at 1.0

#curve_surv_mean, curve_surv_sd = 25, 12.5
#curve_surv = scipy.stats.norm.sf(np.arange(n_years), loc=curve_surv_mean, scale=curve_surv_sd)

# Build survival matrix
survival_matrix = np.zeros((n_years, n_years))
for i in range(n_years):
    survival_matrix[i:, i] = curve_surv[:n_years - i]
survival_matrix_df = pd.DataFrame(survival_matrix, index=full_years, columns=full_years)

# Compute inflows using stock-driven logic
for t, year in enumerate(full_years):
    if t == 0:
        continue

    survivors = survival_matrix_df.loc[year, full_years[:t]].dot(
        planes_projection.loc[full_years[:t], 'inflow']
    )
    stock_required = planes_projection.loc[year, 'stock']
    inflow = max(stock_required - survivors, 0)
    planes_projection.at[year, 'inflow'] = inflow

# Compute NAS and Outflow using continuity identity
planes_projection['nas'] = planes_projection['stock'].diff().fillna(0)
planes_projection['prev_stock'] = planes_projection['stock'].shift(1, fill_value=0)
planes_projection['outflow'] = (
    planes_projection['prev_stock'] + planes_projection['inflow'] - planes_projection['stock']
).clip(lower=0)
planes_projection.drop(columns=['prev_stock'], inplace=True)
#planes_projection['nas-verif'] = planes_projection['nas'] - (planes_projection['inflow'] - planes_projection['outflow'])


planes_projection[['stock']].plot()

#%% Plane stock by vintage (cohort survival matrix in number of planes)

plane_stock_by_vintage = pd.DataFrame(0.0, index=planes_projection.index, columns=planes_projection.index)
for i, year in enumerate(planes_projection.index):
    if planes_projection.loc[year, 'inflow'] > 0:
        plane_stock_by_vintage.loc[year:, year] = curve_surv[:n_years - i] * planes_projection.loc[year, 'inflow']
    elif year == 1970:
        # Special case for 1970: fill based on the stock directly
        plane_stock_by_vintage.loc[year:, year] = curve_surv[:n_years - i] * planes_projection.loc[year, 'stock']

#%%
stock_by_class = pd.read_excel(path, sheet_name="Stock by class", index_col=0)
stock_by_class.index = stock_by_class.index.astype(int)
if stock_by_class.dtypes[0] == object:
    stock_by_class = stock_by_class.replace({',': '.'}, regex=True).astype(float) / 100

stock_by_class_past = pd.DataFrame(
    [stock_by_class.loc[2000].values] * 30,
    index=np.arange(1970, 2000),
    columns=stock_by_class.columns
)

stock_by_class_full = pd.concat([stock_by_class_past, stock_by_class]).reindex(planes_projection.index)
stock_by_class_full = stock_by_class_full.div(stock_by_class_full.sum(axis=1), axis=0)
stock_by_class_absolute = stock_by_class_full.multiply(planes_projection['stock'], axis=0)

#%%
weight_by_class = pd.read_excel(path, sheet_name="Weight by class", index_col=0).squeeze()
weight_by_class = weight_by_class.reindex(stock_by_class_absolute.columns)

stock_weight_by_class = stock_by_class_absolute.multiply(weight_by_class, axis=1)

#%% === Titanium stock-driven model (consistent with planes logic) ===

# Step 1: Inflow of planes by class (based on inflow units and class share)
inflow_by_class = stock_by_class_full.multiply(planes_projection['inflow'], axis=0)

# Step 2: Inflow mass by class (tons)
inflow_weight_by_class = inflow_by_class.multiply(weight_by_class, axis=1)

# Step 3: Import and align titanium share matrix
titanium_share_matrix = pd.read_excel(path, sheet_name="Titanium by vintage", index_col=0)
titanium_share_matrix.index = titanium_share_matrix.index.astype(int)
titanium_share_matrix = titanium_share_matrix.reindex(columns=stock_by_class_full.columns)

# Step 4: Inflow of titanium mass by class
inflow_titanium_by_class = inflow_weight_by_class.multiply(titanium_share_matrix, axis=0)

# Step 5: Total titanium inflow per year (tons)
inflow_titanium_total = inflow_titanium_by_class.sum(axis=1)

# Step 6: Build titanium stock by vintage using same survival logic
titanium_stock_by_vintage = pd.DataFrame(0.0, index=planes_projection.index, columns=planes_projection.index)
for i, year in enumerate(planes_projection.index):
    inflow_ti = inflow_titanium_total.loc[year]
    surv_curve = curve_surv[:n_years - i]
    titanium_stock_by_vintage.iloc[i:, i] = inflow_ti * surv_curve

# Step 7: Calculate stock, NAS, outflow
titanium_projection = pd.DataFrame(index=planes_projection.index)

titanium_projection['stock'] = 0.0
titanium_projection['inflow'] = 0.0
titanium_projection['outflow'] = 0.0

titanium_projection['stock'] = titanium_stock_by_vintage.sum(axis=1)
titanium_projection['inflow'] = inflow_titanium_total
titanium_projection['nas'] = titanium_projection['stock'].diff().fillna(0)
titanium_projection['outflow'] = (titanium_projection['inflow'] - titanium_projection['nas']).clip(lower=0)

# Optional check
#titanium_projection['nas_check'] = titanium_projection['nas'] - (titanium_projection['inflow'] - titanium_projection['outflow'])

#%%# --- Plotting ---

this_folder = Path(__file__).parent/'Plots'

# 1. Inflow, Outflow, NAS for planes
planes_projection[['inflow', 'outflow', 'nas']].plot(figsize=(12, 6))
plt.title('Aircraft Inflow, Outflow, and NAS')
plt.xlabel('Year')
plt.ylabel('Number of Planes')
plt.tight_layout()
plt.savefig(this_folder / '1. Baseline 2040 - planes_inflow_outflow_nas.png', dpi=300)
plt.close()

# 2. Stock for planes 
planes_projection['stock'].plot(figsize=(12, 6))

plt.axvline(x=1970, color='k', linestyle='--', linewidth=1, label='Backcast')
plt.axvline(x=2000, color='k', linestyle='--', linewidth=1, label='Observed data')
plt.axvline(x=2023, color='k', linestyle='--', linewidth=1, label='Forecast')

plt.text(1970 + 0.3, plt.ylim()[1]*0.95, 'Backcast', rotation=90, verticalalignment='top', fontsize=9)
plt.text(2000 + 0.3, plt.ylim()[1]*0.95, 'Observed', rotation=90, verticalalignment='top', fontsize=9)
plt.text(2023 + 0.3, plt.ylim()[1]*0.95, 'Forecast', rotation=90, verticalalignment='top', fontsize=9)

plt.title('Aircraft Stock Over Time')
plt.xlabel('Year')
plt.ylabel('Number of Planes')
plt.tight_layout()
#plt.show()
plt.savefig(this_folder / '2. Baseline 2040 - planes_stock_over_time.png', dpi=300)
plt.close()

# 3. Survival Matrix Area Plot for planes
plane_stock_by_vintage.plot(
    kind="area",
    stacked=True,
    legend=False,
    figsize=(12, 6)
)

plt.axvline(x=1970, color='k', linestyle='--', linewidth=1, label='Backcast')
plt.axvline(x=2000, color='k', linestyle='--', linewidth=1, label='Observed data')
plt.axvline(x=2023, color='k', linestyle='--', linewidth=1, label='Forecast')

plt.text(1970 + 0.3, plt.ylim()[1]*0.95, 'Backcast', rotation=0, verticalalignment='top', fontsize=9)
plt.text(2000 + 0.3, plt.ylim()[1]*0.95, 'Observed', rotation=0, verticalalignment='top', fontsize=9)
plt.text(2023 + 0.3, plt.ylim()[1]*0.95, 'Forecast', rotation=0, verticalalignment='top', fontsize=9)

#plt.title('Aircraft Survival Matrix')
plt.xlabel('Year')
plt.ylabel('Number of planes')
plt.tight_layout()
plt.savefig(this_folder / '3. Baseline 2040 - aircraft_survival_matrix.png', dpi=600)
plt.close()

#%% 4. Survival Matrix Area Plot for Titanium
titanium_stock_by_vintage.plot(kind="area", stacked=True, legend=False,  figsize=(12, 6))
plt.title('Titanium Survival Matrix')
plt.xlabel('Year')
plt.ylabel('Titanium (tons)')
plt.tight_layout()
#plt.show()
plt.savefig(this_folder / '4. Baseline 2040 - titanium_survival_matrix.png', dpi=300)
plt.close()

# --- Titanium inflow and outflow line plot ---
plt.figure(figsize=(10, 5))
titanium_projection[['inflow', 'outflow']].plot(ax=plt.gca())
plt.title('Titanium Inflow and Outflow Over Time', fontsize=14)
plt.xlabel('Year')
plt.ylabel('Titanium (tons/year)')
plt.legend(['Inflow', 'Outflow'])
plt.grid(False)
plt.tight_layout()
plt.savefig(this_folder / '5. Baseline 2040 - titanium_inflow_outflow.png', dpi=300)
plt.close()


plt.figure(figsize=(10, 5))
titanium_projection['stock'].plot()
plt.title('Total Titanium Stock in Aircraft Over Time', fontsize=14)
plt.xlabel('Year')
plt.ylabel('Titanium in stock (tons)')
plt.grid(False)
plt.tight_layout()
plt.savefig(this_folder / '6. Baseline 2040 - titanium_total_stock.png', dpi=300)
plt.close()

#%%

# Create figure with two subplots
fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=False)

# --- (2) Inflow and Outflow Line Plot ---
titanium_projection[['inflow', 'outflow']].plot(
    ax=axes[0]
)
axes[0].set_title('Titanium inflow and outflow in the EU aircraft fleet (1970–2040)', fontsize=14)
axes[0].set_xlabel('Year')
axes[0].set_ylabel('Titanium (tons/year)')
axes[0].legend(['Inflow', 'Outflow'])
axes[0].grid(False)

# --- (1) Survival Matrix Area Plot ---
titanium_stock_by_vintage.plot(
    kind="area",
    stacked=True,
    legend=False,
    ax=axes[1]
)
axes[1].set_title('Titanium stock evolution by vintage within the EU aircraft fleet (1970–2040)', fontsize=14)
axes[1].set_xlabel('Year')
axes[1].set_ylabel('Titanium (tons)')
axes[1].grid(False)

# Adjust layout and save
plt.tight_layout()
plt.savefig(this_folder / 'Combined_Titanium_Plots.png', dpi=300)
plt.close()

#%% Save all dataframes to a single Excel file with formatting
results_folder = Path(__file__).parent/'Results'

# Round all numbers to integer (no decimals)
rounded_planes_projection = planes_projection.round(0).astype('Int64')
rounded_plane_stock_by_vintage = plane_stock_by_vintage.round(0).astype('Int64')
rounded_stock_by_class_absolute = stock_by_class_absolute.round(0).astype('Int64')
rounded_titanium_projection = titanium_projection.round(0).astype('Int64')
rounded_titanium_stock_by_vintage = titanium_stock_by_vintage.round(0).astype('Int64')

with pd.ExcelWriter(results_folder /'Baseline 2060 - Aircraft fleet and titanium content.xlsx', engine='xlsxwriter') as writer:
     rounded_planes_projection.to_excel(writer, sheet_name='planes_projection')
     rounded_plane_stock_by_vintage.to_excel(writer, sheet_name='plane_stock_by_vintage')
     rounded_stock_by_class_absolute.to_excel(writer, sheet_name='stock_by_class_absolute')
     rounded_titanium_projection.to_excel(writer, sheet_name='titanium_projection')
     rounded_titanium_stock_by_vintage.to_excel(writer, sheet_name='titanium_stock_by_vintage')

     workbook = writer.book

     for sheet_name in ['planes_projection', 'plane_stock_by_vintage', 'stock_by_class_absolute', 'titanium_projection', 'titanium_stock_by_vintage']:
         worksheet = writer.sheets[sheet_name]
         worksheet.freeze_panes(1, 1)
         worksheet.set_zoom(90)
         worksheet.set_column('A:ZZ', 15)

