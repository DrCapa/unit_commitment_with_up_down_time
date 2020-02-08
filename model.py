""" model of the unit commitment with up and down times for chp units"""

import pandas as pd
from pyomo.environ import *

from model_T1In2Out import define_T1In2Out


# Define abstracte model
m = AbstractModel()

# Define sets
m.t = Set(ordered=True)

# Define parameters
m.gas = Param(m.t)
m.spot = Param(m.t)
m.dem = Param(m.t)

# Read Unit Capacities, Up And Down Times
df_chp_old_param = pd.read_csv('input/param_chp_old.csv', index_col=0)
df_chp_new_param = pd.read_csv('input/param_chp_new.csv', index_col=0)
df_heat_plant_param = pd.read_csv('input/param_heat_plant.csv', index_col=0)
df_store_param = pd.read_csv('input/param_store.csv', index_col=0)

# Read Unit Costs
df_chp_old_costs = pd.read_csv('input/cost_chp_old.csv', index_col=0)
df_chp_new_costs = pd.read_csv('input/cost_chp_new.csv', index_col=0)
df_heat_plant_costs = pd.read_csv('input/cost_heat_plant.csv', index_col=0)

# Define Store Index
m.j_store = Set(initialize=df_store_param.index)

# CHP Transformer
define_T1In2Out(m, 'chp_old', df_chp_old_param, df_chp_old_costs)
define_T1In2Out(m, 'chp_new', df_chp_new_param, df_chp_new_costs)

# Heat plant Transformer
define_T1In2Out(m, 'heat_plant', df_heat_plant_param, df_heat_plant_costs)

# Store equations
m.on_charge_store = Var(m.j_store, m.t, within=Binary)
m.on_discharge_store = Var(m.j_store, m.t, within=Binary)
m.store_charge = Var(m.j_store, m.t, domain=NonNegativeReals)
m.store_discharge = Var(m.j_store, m.t, domain=NonNegativeReals)
m.store_capacity = Var(m.j_store, m.t, domain=NonNegativeReals)


def charge_store(m, j, t):
    return (m.store_charge[j, t] <=
            df_store_param.loc[j, 'charge']*m.on_charge_store[j, t])
m.chargestorer = Constraint(m.j_store, m.t, rule=charge_store)


def discharge_store(m, j, t):
    if t == m.t.first():
        return m.store_discharge[j, t] == 0
    else:
        return (m.store_discharge[j, t] <=
                df_store_param.loc[j, 'discharge']*m.on_discharge_store[j, t])
m.dischargestore = Constraint(m.j_store, m.t, rule=discharge_store)


def capacity_max_store(m, j, t):
    return m.store_capacity[j, t] <= df_store_param.loc[j, 'capacity']
m.capacitymaxstore = Constraint(m.j_store, m.t, rule=capacity_max_store)


def capacity_store(m, j, t):
    if t == m.t.first():
        return m.store_capacity[j, t] == 0
    else:
        return (m.store_capacity[j, t] <=
                m.store_capacity[j, t-1]+m.store_charge[j, t]-m.store_discharge[j, t])
m.capacitystore = Constraint(m.j_store, m.t, rule=capacity_store)


def charge_or_discharge_store(m, j, t):
    return m.on_charge_store[j, t]+m.on_discharge_store[j, t] <= 1
m.chargeordischargestore = Constraint(m.j_store, m.t, rule=charge_or_discharge_store)


# Objective Function
def obj_expression(m):
    return (sum((m.In_chp_old[t]+m.In_chp_new[t]+m.In_heat_plant[t])*m.gas[t]-
                (m.Out1_chp_old[t]+m.Out1_chp_new[t])*m.spot[t]
                for t in m.t)+
            m.Costs_chp_old+
            m.Costs_chp_new+
            m.Costs_heat_plant)
m.obj = Objective(rule=obj_expression, sense=minimize)


# Heat Balance
def balance_rule(m, t):
    return (m.HeatBalance_chp_old[t]+
            m.HeatBalance_chp_new[t]+
            m.HeatBalance_heat_plant[t]+
            sum(m.store_discharge[j, t] for j in m.j_store) ==
            m.dem[t]+sum(m.store_charge[j, t] for j in m.j_store))
m.balance = Constraint(m.t, rule=balance_rule)
