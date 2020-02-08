from pyomo.environ import *
import pandas as pd 



def define_T1In2Out(m, name, param, cost):
    """ Transformer with 1 Input and 2 Outputs
        Input: Gas
        Output 1: Power
        Output 2: Heat
        on: Online Status (0 - offline, 1 - online)
        StartCosts: Start costs
        l_ut: Up time
        l_dt: Down time 
        """
        
    # Binary Variables
    m.__setattr__('on_'+name, Var(m.t, within=Binary, doc='online'))
        
    # Non Negative Real Variables
    m.__setattr__('In_'+name, Var(m.t, domain=NonNegativeReals,
                                  doc='fuel consumption'))
    m.__setattr__('Out1_'+name, Var(m.t, domain=NonNegativeReals,
                                    doc='power production'))
    m.__setattr__('Out2_'+name, Var(m.t, domain=NonNegativeReals,
                                    doc='heat production'))
    m.__setattr__('StartCost_'+name, Var(m.t, domain=NonNegativeReals,
                                         doc='start costs'))

    # Set up time and down time
    m.__setattr__('l_ut_'+name, Set(initialize=list(range(param.loc[name, 'up']+1)),
                                    doc='up time'))
    m.__setattr__('l_dt_'+name, Set(initialize=list(range(param.loc[name, 'down']+1)),
                                    doc='down tim'))
    # Constraints    
    def max_In(m, t):
        """ Maximal Input if unit is online """

        value = param.loc[name, 'Inmax']
        return m.__getattribute__('In_'+name)[t] <= value*m.__getattribute__('on_'+name)[t]


    def min_In(m, t):
        """ Minimal Input if unit is online """

        value = param.loc[name, 'Inmin']
        return value*m.__getattribute__('on_'+name)[t] <= m.__getattribute__('In_'+name)[t]


    def max_Out1(m, t):
        """ Maximal Output 1 if unit is online """

        value = param.loc[name, 'Out1max']
        return m.__getattribute__('Out1_'+name)[t] <= value*m.__getattribute__('on_'+name)[t]


    def min_Out1(m, t):
        """ Minimal Output 1 if unit is online """

        value = param.loc[name, 'Out1min']
        return value*m.__getattribute__('on_'+name)[t] <= m.__getattribute__('Out1_'+name)[t]


    def max_Out2(m, t):
        """ Maximal Output 2 if unit is online """
        value = param.loc[name, 'Out2max']
        return m.__getattribute__('Out2_'+name)[t] <= value*m.__getattribute__('on_'+name)[t]


    def min_Out2(m, t):
        """ Minimal Output 2 if unit is online """
        value = param.loc[name, 'Out2min']
        return value*m.__getattribute__('on_'+name)[t] <= m.__getattribute__('Out2_'+name)[t]


    def Out1vsOut2(m, t):
        """ Output 1 depends linear on Output 2 """

        value_Out2max = param.loc[name, 'Out2max']
        value_Out2min = param.loc[name, 'Out2min']
        value_Out1max = param.loc[name, 'Out1max']
        value_Out1min = param.loc[name, 'Out1min']
        if(value_Out2max-value_Out2min == 0): 
            return Constraint.Skip
        elif(value_Out1max-value_Out1min == 0):
            return Constraint.Skip
        else:
            a = (value_Out1max-value_Out1min)/(value_Out2max-value_Out2min)
            b = value_Out1min-a*value_Out2min
            return (m.__getattribute__('Out1_'+name)[t] == 
                    a*m.__getattribute__('Out2_'+name)[t]+
                    b*m.__getattribute__('on_'+name)[t])


    def Input_demand(m, t):
        """ Input depends linear on Outputs """

        value_Out2max = param.loc[name, 'Out2max']
        value_Out2min = param.loc[name, 'Out2min']
        value_Out1max = param.loc[name, 'Out1max']
        value_Out1min = param.loc[name, 'Out1min']
        value_Inmax = param.loc[name, 'Inmax']
        value_Inmin = param.loc[name, 'Inmin']
        if(value_Out1max-value_Out1min == 0 and value_Out2max-value_Out2min == 0):
            return Constraint.Skip
        elif(value_Out1max - value_Out1min == 0):
            a = (value_Inmax-value_Inmin)/(value_Out2max-value_Out2min)
            b = value_Inmin-a*value_Out2min
            return (m.__getattribute__('In_'+name)[t] ==
                    a*m.__getattribute__('Out2_'+name)[t]+
                    b*m.__getattribute__('on_'+name)[t])
        else:
            a = (value_Inmax-value_Inmin)/(value_Out1max-value_Out1min)
            b = value_Inmin-a*value_Out1min
            return (m.__getattribute__('In_'+name)[t] ==
                    a*m.__getattribute__('Out1_'+name)[t]+
                    b*m.__getattribute__('on_'+name)[t])


    def up_time(m, t, l):
        """ Minimal up time """

        l_hat = t+l-1
        if((t == m.t.first()) or (t == m.t.last()) or
            (l_hat > m.t.last() or (l_hat < t+1))):
            return Constraint.Skip
        else:
            return (m.__getattribute__('on_'+name)[t]-m.__getattribute__('on_'+name)[t-1] <=
                    m.__getattribute__('on_'+name)[l_hat])


    def down_time(m, t, l):
        """ Minimal down time """

        l_hat = t+l-1
        if((t == m.t.first()) or (t == m.t.last()) or
            (l_hat > m.t.last() or (l_hat < t+1))):
            return Constraint.Skip
        else:
            return (m.__getattribute__('on_'+name)[t-1]-m.__getattribute__('on_'+name)[t] <=
                    1-m.__getattribute__('on_'+name)[l_hat])


    def start_costs(m, t):
        """ Start costs """

        if t == m.t.first():
            return Constraint.Skip
        else:
            return (m.__getattribute__('StartCost_'+name)[t] >=
                    -cost.loc[name, 'start']*(m.__getattribute__('on_'+name)[t-1]-m.__getattribute__('on_'+name)[t]))


    def costs(m):
        """ Total unit costs """

        return sum(m.__getattribute__('on_'+name)[t]*cost.loc[name, 'oh']+
                   m.__getattribute__('StartCost_'+name)[t] for t in m.t)


    def heat_balance(m, t):
        """ Output 2 is heat output """

        return m.__getattribute__('Out2_'+name)[t]


    # Instance Transformer
    m.__setattr__('maxIn_'+name, Constraint(m.t, rule=max_In))
    m.__setattr__('minIn_'+name, Constraint(m.t, rule=min_In))
    m.__setattr__('maxOut1_'+name, Constraint(m.t, rule=max_Out1))
    m.__setattr__('minOut1_'+name, Constraint(m.t, rule=min_Out1))
    m.__setattr__('maxOut2_'+name, Constraint(m.t, rule=max_Out2))
    m.__setattr__('minOut2_'+name, Constraint(m.t, rule=min_Out2))
    m.__setattr__('Out1vsOut2_'+name, Constraint(m.t, rule=Out1vsOut2))
    m.__setattr__('Input_demand_'+name, Constraint(m.t, rule=Input_demand))
    m.__setattr__('uptime_'+name, Constraint(m.t, m.__getattribute__('l_ut_'+name),
                                             rule=up_time)) 
    m.__setattr__('downtime_'+name, Constraint(m.t, m.__getattribute__('l_dt_'+name),
                                               rule=down_time))
    m.__setattr__('startcosts_'+name, Constraint(m.t, rule=start_costs))
    m.__setattr__('Costs_'+name, Expression(rule=costs))       
    m.__setattr__('HeatBalance_'+name, Expression(m.t, rule=heat_balance))
    
    return m
    