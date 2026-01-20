#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  4 16:26:10 2025

@author: stefanoghirlandi
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

#%% Example dataframe

path = Path(__file__).parent / 'trade flows.xlsx'
trade = pd.read_excel(path, sheet_name="Sheet1")

# Define what we want to plot
plot_items = [
    ('wrought', 'import', 'Titanium Wrought Imports'),
    ('unwrought', 'import', 'Titanium Unwrought Imports'),
    ('scrap', 'import', 'Titanium Scrap Imports'),
    ('scrap', 'export', 'Titanium Scrap Exports')
]
#%% Create figure
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
axes = axes.flatten()

# === Global partner ordering & color map ===
partner_totals = trade.groupby('partner')['value'].sum().sort_values(ascending=False)
partner_order = partner_totals.index.tolist()
colors = plt.cm.tab20.colors
color_map = {p: colors[i % len(colors)] for i, p in enumerate(partner_order)}

# === Plot loop ===
for ax, (cat, flow, title) in zip(axes, plot_items):
    subset = trade[(trade['category'] == cat) & (trade['flow'] == flow)]
    if subset.empty:
        ax.axis('off')
        continue

    # Pivot table (year × partner)
    pivot = subset.pivot_table(index='year', columns='partner', values='value', aggfunc='sum', fill_value=0)
    pivot = pivot.reindex(columns=[p for p in partner_order if p in pivot.columns])
    
    # Compute totals
    totals = pivot.sum(axis=1)
    shares = pivot.div(totals, axis=0) * 100

    # Plot stacked bars
    pivot.plot(
        kind='bar',
        stacked=True,
        ax=ax,
        edgecolor='black',
        color=[color_map[p] for p in pivot.columns],
        legend=False
    )

    # --- Add % labels inside segments ---
    for i, year in enumerate(pivot.index):
        y_bottom = 0
        for partner in pivot.columns:
            val = pivot.loc[year, partner]
            pct = shares.loc[year, partner]
            if pct > 10:  # only label big slices
                ax.text(
                    i, y_bottom + val / 2,
                    f"{pct:.0f}%",
                    ha='center', va='center',
                    fontsize=7, color='white', weight='bold'
                )
            y_bottom += val

    # --- Add total labels on top ---
    for i, total in enumerate(totals):
        ax.text(
            i, total * 1.005,  # a bit above the stack
            f"{int(total):,}",
            ha='center', va='bottom',
            fontsize=9, weight='bold'
        )

    # --- Style ---
    ax.set_title(title, fontsize=12, weight='bold', pad=10)
    ax.set_xlabel('')
    ax.set_ylabel('Quantity (kilotonnes)')
    ax.set_xticks(range(len(pivot.index)))
    ax.set_xticklabels(pivot.index.astype(str), fontsize=9)
    #ax.grid(axis='y', linestyle='--', alpha=0.4)

    # --- Legend (outside right) ---
    ax.legend(
        pivot.columns,
        title='Partner',
        bbox_to_anchor=(1.05, 1),
        loc='upper left',
        fontsize=8,
        title_fontsize=9
    )

# === Final layout ===
plt.tight_layout()
plt.subplots_adjust(top=1)
for ax in axes:
    for label in ax.get_xticklabels():
        if label.get_text() in ['2019', '2024']:
            label.set_rotation(45)
            label.set_ha('right')
plt.savefig(Path(__file__).parent /"titanium_trade_structure_final.png", dpi=300, bbox_inches='tight')
plt.show()
plt.close()