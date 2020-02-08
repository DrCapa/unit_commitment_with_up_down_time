""" instance of the unit commitment """

from model import *
from pyomo.opt import SolverFactory
from pyomo.environ import DataPortal
import numpy as np
import pandas as pd


def run_optimization(path_out):
    # Select Solver
    opt = SolverFactory('cbc')

    # Create DataPortal
    data = DataPortal()

    # Read Timeseries
    data.load(filename='input/timeseries_gas.csv', index='t', param='gas')
    data.load(filename='input/timeseries_heat_demand.csv', index='t', param='dem')
    data.load(filename='input/timeseries_spot.csv', index='t', param='spot')

    # Create Instanz
    instance = m.create_instance(data)

    # Solve Optimization Problem
    results = opt.solve(instance, symbolic_solver_labels=True, tee=True,
                        load_solutions=True)

    # Write Timeseries
    df_output = pd.DataFrame()
    for t in instance.t.value:
        df_output.loc[t, 'gas_chp_old'] = instance.In_chp_old[t].value
        df_output.loc[t, 'power_chp_old'] = instance.Out1_chp_old[t].value
        df_output.loc[t, 'heat_chp_old'] = instance.Out2_chp_old[t].value
        df_output.loc[t, 'on_chp_old'] = instance.on_chp_old[t].value
        df_output.loc[t, 'StartCost_chp_old'] = instance.StartCost_chp_old[t].value

        df_output.loc[t, 'gas_chp_new'] = instance.In_chp_new[t].value
        df_output.loc[t, 'power_chp_new'] = instance.Out1_chp_new[t].value
        df_output.loc[t, 'heat_chp_new'] = instance.Out2_chp_new[t].value
        df_output.loc[t, 'on_chp_new'] = instance.on_chp_new[t].value
        df_output.loc[t, 'StartCost_chp_new'] = instance.StartCost_chp_new[t].value

        df_output.loc[t, 'gas_heat_plant'] = instance.In_heat_plant[t].value
        df_output.loc[t, 'power_heat_plant'] = instance.Out1_heat_plant[t].value
        df_output.loc[t, 'heat_heat_plant'] = instance.Out2_heat_plant[t].value
        df_output.loc[t, 'on_heat_plant'] = instance.on_heat_plant[t].value
        df_output.loc[t, 'StartCost_heat_plant'] = instance.StartCost_heat_plant[t].value

        for j in instance.j_store.value:
            df_output.loc[t, '_'.join([str(j), 'charge'])] = instance.store_charge[j, t].value
            df_output.loc[t, '_'.join([str(j), 'capacity'])] = instance.store_capacity[j, t].value
            df_output.loc[t, '_'.join([str(j), 'discharge'])] = instance.store_discharge[j, t].value
        df_output.loc[t, 'demand'] = instance.dem[t]
        df_output.loc[t, 'spot'] = instance.spot[t]
        df_output.loc[t, 'gas'] = instance.gas[t]

    # Export Timeseries
    df_output.to_csv(path_out+'timeseries.csv')
