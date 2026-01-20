#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul  6 13:09:31 2025

@author: stefanoghirlandi
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

#%% 1. Read the comparison sheet
comparison_path = Path(__file__).parent /'Comparison.xlsx'
df = pd.read_excel(comparison_path, sheet_name='planes', index_col=0)

# 2. Plot inflows
plt.figure(figsize=(10, 5))
plt.plot(df.index, df['inflow_LTE'],      label='LTE', color='r')
plt.plot(df.index, df['inflow_baseline'], label='Baseline', color='b')
plt.title('Annual Plane Inflow: Baseline vs. LTE')
plt.xlabel('Year')
plt.ylabel('Number of Planes')
plt.legend()
plt.grid(False)
plt.savefig(Path(__file__).parent /'Inflows comparison.png', dpi=300)
plt.close()

# 3. Plot outflows
plt.figure(figsize=(10, 5))
plt.plot(df.index, df['outflow_LTE'],      label='LTE', color='r')
plt.plot(df.index, df['outflow_baseline'], label='Baseline', color='b')
plt.title('Annual Plane Outflow: Baseline vs. LTE')
plt.xlabel('Year')
plt.ylabel('Number of Planes')
plt.legend()
plt.savefig(Path(__file__).parent /'Outflows comparison.png', dpi=300)
plt.close()

#%% 1. Read the comparison sheet
comparison_path = Path(__file__).parent /'Comparison.xlsx'
titanium = pd.read_excel(comparison_path, sheet_name='titanium', index_col=0)

kt_inflow_baseline = titanium['inflow_baseline'] / 1_000
kt_inflow_LTE      = titanium['inflow_LTE']      / 1_000

kt_outflow_baseline = titanium['outflow_baseline'] / 1_000
kt_outflow_LTE      = titanium['outflow_LTE']      / 1_000

# 2. Plot inflows
plt.figure(figsize=(10, 5))
plt.plot(titanium.index, kt_inflow_baseline, label='Baseline', color='b')
plt.plot(titanium.index, kt_inflow_LTE,      label='LTE', color='r')
plt.title('Annual Titanium Inflow: Baseline vs. LTE')
plt.xlabel('Year')
plt.ylabel('Titanium metal (kt)')
plt.legend()
plt.grid(False)
plt.savefig(Path(__file__).parent / 'Titanium Inflows comparison.png', dpi=300)
plt.close()

# 3. Plot outflows
plt.figure(figsize=(10, 5))
plt.plot(titanium.index, kt_outflow_baseline, label='Baseline', color='b')
plt.plot(titanium.index, kt_outflow_LTE ,      label='LTE', color='r')
plt.title('Annual Titanium Outflow: Baseline vs. LTE')
plt.xlabel('Year')
plt.ylabel('Titanium metal (kt)')
plt.legend()
plt.savefig(Path(__file__).parent /'Titanium Outflows comparison.png', dpi=300)
plt.close()

#%%
fig, axes = plt.subplots(2, 1, figsize=(10, 10), sharex=False)

# --- 1. Inflows ---
axes[0].plot(titanium.index, kt_inflow_baseline, label='Baseline', color='b', alpha=1, zorder=2)
axes[0].plot(titanium.index, kt_inflow_LTE, label='LTE', color='r', alpha=0.8, zorder=1)
axes[0].set_title('Annual Titanium Inflow: Baseline vs. LTE')
axes[0].set_ylabel('Titanium metal (kt)')
axes[0].set_xlabel('Year')
axes[0].legend()
axes[0].grid(False)

# --- 2. Outflows ---
axes[1].plot(titanium.index, kt_outflow_baseline, label='Baseline', color='b', alpha=1, zorder=2)
axes[1].plot(titanium.index, kt_outflow_LTE, label='LTE', color='r', alpha=0.8, zorder=1)
axes[1].set_title('Annual Titanium Outflow: Baseline vs. LTE')
axes[1].set_xlabel('Year')
axes[1].set_ylabel('Titanium metal (kt)')
axes[1].legend()
axes[1].grid(False)

plt.tight_layout()
plt.savefig(Path(__file__).parent / 'Titanium_Flows_Comparison.png', dpi=300)
plt.close()
