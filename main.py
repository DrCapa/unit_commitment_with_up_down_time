from analysis import *
from instance import run_optimization
import os

# Make Output Folder
path_out = 'output/'
if not os.path.isdir(path_out):
    os.makedirs(path_out)

# Run Optimization
run_optimization(path_out)

# Read Timeseries From Optimization
df_data = pd.read_csv('output/timeseries.csv')

# Read Unit Costs
df_chp_old_costs = pd.read_csv('input/cost_chp_old.csv', index_col=0)
df_chp_new_costs = pd.read_csv('input/cost_chp_new.csv', index_col=0)
df_heat_plant_costs = pd.read_csv('input/cost_heat_plant.csv', index_col=0)

# Read Market Costs
df_spot = pd.read_csv('input/timeseries_spot.csv', index_col=0)
df_gas = pd.read_csv('input/timeseries_gas.csv', index_col=0)

# Evaluate Units
units = [col.replace('gas_', '') for col in df_data.columns if 'gas_' in col]
kpis = ['gas', 'power', 'heat', 'on']
costs = ['gas', 'start', 'on', 'spot']

# Analysis
kpi_per_unit(df_data, units, kpis, path_out)
costs_per_unit(df_data, units, costs,
               df_chp_old_costs,
               df_chp_new_costs,
               df_heat_plant_costs,
               path_out)

# Plots
plot_timeseries(df_data, 'spot', 'Euro/MW', path_out)
plot_timeseries(df_data, 'demand', 'MW', path_out)
plot_timeseries(df_data, 'heat_chp_old', 'MW', path_out)
plot_timeseries(df_data, 'heat_chp_new', 'MW', path_out)

plot_heat_stack(df_data, path_out)
