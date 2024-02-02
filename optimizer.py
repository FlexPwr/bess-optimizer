import os
import numpy as np
import math
import pyomo.environ as pyo
import pyomo.opt as po



def set_glpk_solver(solvername,solverpath_exe):

    """
    Sets the solver to be used to the GLPK solver.
    Note that you have to install the GLPK solver on your machine to run the optimization model.
    It is available here: https://www.gnu.org/software/glpk/
    """

    return(pyo.SolverFactory(solvername,executable=solverpath_exe))
    
    

def step1_optimize_daa(n_cycles:int, energy_cap:int, power_cap:int, daa_price_vector:list):

    """
    Calculates optimal charge/discharge schedule on the day-ahead auction (daa) for a given 96-d daa_price_vector.

    Parameters:
    - n_cycles: Maximum number of allowed cycles
    - energy_cap: Energy capacity
    - power_cap: Power capacity
    - daa_price_vector: 96-dimensional daa price vector

    Returns:
    - step1_soc_daa: Resulting state of charge schedule
    - step1_cha_daa: Resulting charge schedule / Positions on DA Auction
    - step1_dis_daa: Resulting discharge schedule / Positions on DA Auction
    - step1_profit_daa: Profit from Day-ahead auction trades
    """
    


    # Initialize pyomo model:

    model = pyo.ConcreteModel()



    # Set parameters:

    # Number of hours
    model.H = pyo.RangeSet(0,23) 

    # Number of quarters
    model.Q = pyo.RangeSet(1,96)         

    # Number of quarters plus 1
    model.Q_plus_1 = pyo.RangeSet(1,97)  

    # Daily discharged energy limit
    volume_limit = energy_cap * n_cycles                    



    # Initialize variables:

    # State of charge
    model.soc = pyo.Var(model.Q_plus_1, domain=pyo.Reals)

    # Charges on the Day-ahead auction
    model.cha_daa = pyo.Var(model.Q, domain=pyo.NonNegativeReals, bounds=(0,1)) 

    # Discharges on the Day-ahead auction
    model.dis_daa = pyo.Var(model.Q, domain=pyo.NonNegativeReals, bounds=(0,1))



    # Define Constraints: 

    # Remark: In some of the constraints, you will notice that the indices [q] and [q-1] are used for the same quarter. This is due to Python lists counting from 0 and Pyomo Variable lists counting from 1.  


    def set_maximum_soc(model, q):
        """
        State of charge can never be higher than Energy Capacity. (Constraint 1.1)
        """
        return model.soc[q] <= energy_cap

    def set_minimum_soc(model, q):
        """
        State of charge can never be less than 0. (Constraint 1.2)
        """
        return model.soc[q] >= 0
    
    def set_first_soc_to_0(model):
        """
        State of charge at the first quarter must be 0. (Constraint 1.3)
        """
        return model.soc[1] == 0

    def set_last_soc_to_0(model):
        """
        State of charge at quarter 97 (i.e., first quarter of next day) must be 0. (Constraint 1.4)
        """
        return model.soc[97] == 0

    def soc_step_constraint(model, q):
        """
        The state of charge of each quarter equals the state if charge of the previous quarter plus charges minus discharges. (Constraint 1.5)
        """
        return model.soc[q + 1] == model.soc[q] + power_cap / 4 * model.cha_daa[q] - power_cap / 4 * model.dis_daa[q]

    def charge_cycle_limit(model):
        """
        Sum of all charges has to be below the daily limit. (Constraint 1.6)
        """
        return sum(model.cha_daa[q] * power_cap / 4 for q in model.Q) <= volume_limit

    def discharge_cycle_limit(model):
        """
        Sum of all discharges has to be below the daily limit. (Constraint 1.7)
        """
        return sum(model.dis_daa[q] * power_cap / 4 for q in model.Q) <= volume_limit

    def cha_daa_quarters_1_2_parity(model, q):
        """
        Set daa positions of quarter 1 and 2 of each hour equal. (Constraint 1.8)
        On the DA Auction, positions in all 4 quarters of the hour have to be identical since trades are taken in hourly blocks. 
        """
        return model.cha_daa[4 * q + 1] == model.cha_daa[4 * q + 2]

    def cha_daa_quarters_2_3_parity(model, q):
        """
        Set daa positions of quarter 2 and 3 of each hour equal. (Constraint 1.8)
        """
        return model.cha_daa[4 * q + 2] == model.cha_daa[4 * q + 3]

    def cha_daa_quarters_3_4_parity(model, q):
        """
        Set daa positions of quarter 3 and 4 of each hour equal. (Constraint 1.8)
        """
        return model.cha_daa[4 * q + 3] == model.cha_daa[4 * q + 4]

    def dis_daa_quarters_1_2_parity(model, q):
        """
        Set daa positions of quarter 1 and 2 of each hour equal. (Constraint 1.9)
        On the DA Auction, positions in all 4 quarters of the hour have to be identical since trades are taken in hourly blocks. 
        """
        return model.cha_daa[4 * q + 1] == model.cha_daa[4 * q + 2]

    def dis_daa_quarters_2_3_parity(model, q):
        """
        Set daa positions of quarter 2 and 3 of each hour equal. (Constraint 1.9)
        """
        return model.cha_daa[4 * q + 2] == model.cha_daa[4 * q + 3]

    def dis_daa_quarters_3_4_parity(model, q):
        """
        Sedaa positions of quarter 3 and 4 of each hour equal. (Constraint 1.9)
        """
        return model.cha_daa[4 * q + 3] == model.cha_daa[4 * q + 4]



    # Apply constraints on the model:

    model.set_maximum_soc = pyo.Constraint(model.Q_plus_1, rule=set_maximum_soc)
    model.set_minimum_soc = pyo.Constraint(model.Q_plus_1, rule=set_minimum_soc)
    model.set_first_soc_to_0 = pyo.Constraint(rule=set_first_soc_to_0)
    model.set_last_soc_to_0 = pyo.Constraint(rule=set_last_soc_to_0)
    model.soc_step_constraint = pyo.Constraint(model.Q, rule=soc_step_constraint)
    model.charge_cycle_limit = pyo.Constraint(rule=charge_cycle_limit)
    model.discharge_cycle_limit = pyo.Constraint(rule=discharge_cycle_limit)
    model.cha_daa_quarters_1_2_parity = pyo.Constraint(model.H, rule=cha_daa_quarters_1_2_parity)
    model.cha_daa_quarters_2_3_parity = pyo.Constraint(model.H, rule=cha_daa_quarters_2_3_parity)
    model.cha_daa_quarters_3_4_parity = pyo.Constraint(model.H, rule=cha_daa_quarters_3_4_parity)
    model.dis_daa_quarters_1_2_parity = pyo.Constraint(model.H, rule=dis_daa_quarters_1_2_parity)
    model.dis_daa_quarters_2_3_parity = pyo.Constraint(model.H, rule=dis_daa_quarters_2_3_parity)
    model.dis_daa_quarters_3_4_parity = pyo.Constraint(model.H, rule=dis_daa_quarters_3_4_parity)



    # Define objective function and solve the optimization problem. 
    # The objective is to maximize revenue from DA Auction trades over all possible charge-discharge schedules.

    model.obj = pyo.Objective(expr=sum(power_cap/4 * daa_price_vector[q-1] * (model.dis_daa[q] - model.cha_daa[q])  for q in model.Q), sense=pyo.maximize)

    solver = set_glpk_solver(solvername='glpk', solverpath_exe='C:\\glpk\\w64\\glpsol')
    solver.solve(model, timelimit=5)



    # Retrieve arrays of resulting optimal soc/charge/discharge schedules after the DA Auction:

    step1_soc_daa = [model.soc[q].value for q in range(1, len(daa_price_vector) + 1)]
    step1_cha_daa = [model.cha_daa[q].value for q in range(1, len(daa_price_vector) + 1)]
    step1_dis_daa = [model.dis_daa[q].value for q in range(1, len(daa_price_vector) + 1)]

    # Calculate profit from Day-ahead auction trades:

    step1_profit_daa = sum([power_cap/4 * daa_price_vector[q] * (step1_dis_daa[q] -  step1_cha_daa[q]) for q in range(len(daa_price_vector))])

    return(step1_soc_daa, step1_cha_daa, step1_dis_daa, step1_profit_daa)





def step2_optimize_ida(n_cycles:int, energy_cap:int, power_cap:int, ida_price_vector:list, step1_cha_daa:list, step1_dis_daa:list):

    """
    Calculates optimal charge/discharge schedule on the intraday auction (ida) for a given 96-d ida_price_vector.

    Parameters:
    - n_cycles: Maximum number of allowed cycles
    - energy_cap: Energy capacity
    - power_cap: Power capacity
    - ida_price_vector: 96-dimensional ida price vector
    - step1_cha_daa: Previous Buys on the Day-Ahead auction
    - step1_dis_daa: Previous Sells on the Day-Ahead auction

    Returns:
    - step2_soc_ida: Resulting state of charge schedule
    - step2_cha_ida: Resulting charges on ID Auction
    - step2_dis_ida: Resulting discharges on ID Auction
    - step2_cha_ida_close: Resulting charges on ID Auction to close previous DA Auction positions
    - step2_dis_ida_close: Resulting discharge on ID Auction to close previous DA Auction positions
    - step2_profit_ida: Profit from Day-ahead auction trades
    - step2_cha_daaida: Combined charges from DA Auction and ID Auction
    - step2_dis_daaida: Combined discharges from DA Auction and ID Auction
    """



    # Initialize pyomo model:

    model = pyo.ConcreteModel()



    # Set parameters:

    # Number of hours
    model.H = pyo.RangeSet(0,len(ida_price_vector)/4-1) 

    # Number of quarters
    model.Q = pyo.RangeSet(1,len(ida_price_vector))         

    # Number of quarters plus 1
    model.Q_plus_1 = pyo.RangeSet(1,len(ida_price_vector)+1)  

    # Daily discharged energy limit
    volume_limit = energy_cap * n_cycles 



    # Initialize variables:

    # State of charge
    model.soc = pyo.Var(model.Q_plus_1, domain=pyo.Reals)

    # Charges on the intraday auction
    model.cha_ida = pyo.Var(model.Q, domain=pyo.NonNegativeReals, bounds=(0,1)) 

    # Discharges on the intraday auction
    model.dis_ida = pyo.Var(model.Q, domain=pyo.NonNegativeReals, bounds=(0,1))

    # Charges on the intraday auction to close previous positions from the day-ahead auction
    model.cha_ida_close = pyo.Var(model.Q, domain=pyo.NonNegativeReals, bounds=(0,1)) 

    # Charges on the intraday auction to close previous positions from the day-ahead auction
    model.dis_ida_close = pyo.Var(model.Q, domain=pyo.NonNegativeReals, bounds=(0,1))



    # Define Constraints: 

    def set_maximum_soc(model, q):
        """
        State of charge can never be higher than Energy Capacity. (Constraint 2.1)
        """
        return model.soc[q] <= energy_cap

    def set_minimum_soc(model, q):
        """
        State of charge can never be less than 0. (Constraint 2.2)
        """
        return model.soc[q] >= 0
    
    def set_first_soc_to_0(model):
        """
        State of charge at the first quarter must be 0. (Constraint 2.3)
        """
        return model.soc[1] == 0

    def set_last_soc_to_0(model):
        """
        State of charge at quarter 97 (i.e., first quarter of next day) must be 0. (Constraint 2.4)
        """
        return model.soc[97] == 0


    def soc_step_constraint(model, q):
        """
        The state of charge of each quarter equals the state if charge of the previous quarter plus charges minus discharges. (Constraint 2.5)
        """
        return model.soc[q+1] == model.soc[q] + power_cap/4  * (model.cha_ida[q] - model.dis_ida[q] + model.cha_ida_close[q] - model.dis_ida_close[q] + step1_cha_daa[q-1] - step1_dis_daa[q-1])


    def charge_cycle_limit(model):
        """
        Sum of all charges has to be below the daily limit. (Constraint 2.6)
        """
        return ((np.sum(step1_cha_daa) + sum(model.cha_ida[q] for q in model.Q) - sum(model.dis_ida_close[q] for q in model.Q)) * power_cap/4 <= volume_limit)


    def discharge_cycle_limit(model):
        """
        Sum of all discharges has to be below the daily limit. (Constraint 2.7)
        """
        return ((np.sum(step1_dis_daa) + sum(model.dis_ida[q] for q in model.Q) - sum(model.cha_ida_close[q] for q in model.Q)) * power_cap/4 <= volume_limit)


    def cha_close_logic(model, q):
        """
        cha_ida_close can only close or reduce existing dis_daa positions. They can only be placed, where dis_daa positions exist. (Constraint 2.8)
        """
        return model.cha_ida_close[q] <= step1_dis_daa[q-1]
    

    def dis_close_logic(model, q):
        """
        dis_ida_close can only close or reduce existing cha_daa positions. They can only be placed, where cha_daa positions exist. (Constraint 2.9)
        """
        return model.dis_ida_close[q] <= step1_cha_daa[q-1]
    

    def charge_rate_limit(model, q):
        """
         Sum of cha_ida[q] and cha_daa[q] has to be less or equal to 1. (Constraint 2.10)
         """
        return model.cha_ida[q] + step1_cha_daa[q-1] <= 1
   

    def discharge_rate_limit(model, q):
        """
         Sum of dis_ida[q] and dis_daa[q] has to be less or equal to 1. (Constraint 2.11)
         """
        return model.dis_ida[q] + step1_dis_daa[q-1] <= 1
    


    # Apply constraints on the model:

    model.set_maximum_soc = pyo.Constraint(model.Q_plus_1, rule=set_maximum_soc)
    model.set_minimum_soc = pyo.Constraint(model.Q_plus_1, rule=set_minimum_soc)
    model.set_first_soc_to_0 = pyo.Constraint(rule=set_first_soc_to_0)
    model.set_last_soc_to_0 = pyo.Constraint(rule=set_last_soc_to_0)
    model.soc_step_constraint = pyo.Constraint(model.Q, rule=soc_step_constraint)
    model.charge_cycle_limit = pyo.Constraint(expr=charge_cycle_limit)
    model.discharge_cycle_limit = pyo.Constraint(expr=discharge_cycle_limit)
    model.cha_close_logic = pyo.Constraint(model.Q, rule=cha_close_logic)
    model.dis_close_logic = pyo.Constraint(model.Q, rule=dis_close_logic)
    model.charge_rate_limit = pyo.Constraint(model.Q, rule=charge_rate_limit)
    model.discharge_rate_limit = pyo.Constraint(model.Q, rule=discharge_rate_limit)



    # Define objective function and solve the optimization problem
    # The objective is to maximize revenue from ID Auction trades over all possible charge-discharge schedules.

    model.obj = pyo.Objective(expr=sum(ida_price_vector[q-1] * power_cap/4 * (model.dis_ida[q] + model.dis_ida_close[q] - model.cha_ida[q] - model.cha_ida_close[q]) for q in model.Q), sense=pyo.maximize)

    solver = set_glpk_solver(solvername='glpk', solverpath_exe='C:\\glpk\\w64\\glpsol')
    solver.solve(model, timelimit=5)



    # Retrieve arrays of resulting optimal soc/charge/discharge schedules after the ID Auction:

    step2_soc_ida = [model.soc[q].value for q in range(1, len(ida_price_vector) + 1)]
    step2_cha_ida = [model.cha_ida[q].value for q in range(1, len(ida_price_vector) + 1)]                   
    step2_dis_ida = [model.dis_ida[q].value for q in range(1, len(ida_price_vector) + 1)]                   
    step2_cha_ida_close = [model.cha_ida_close[q].value for q in range(1, len(ida_price_vector) + 1)]       
    step2_dis_ida_close = [model.dis_ida_close[q].value for q in range(1, len(ida_price_vector) + 1)]       


    # Calculate profit from Day-ahead auction trades: 
      
    step2_profit_ida = np.sum(((np.asarray(step2_dis_ida) + step2_dis_ida_close) - (np.asarray(step2_cha_ida) + step2_cha_ida_close)) * ida_price_vector) * power_cap/4
    

    # Calculate total physical charge discharge schedules of combined day-ahead and intraday auction trades:

    step2_cha_daaida = np.asarray(step1_cha_daa) - step2_dis_ida_close + step2_cha_ida
    step2_dis_daaida = np.asarray(step1_dis_daa) - step2_cha_ida_close + step2_dis_ida

    return(step2_soc_ida, step2_cha_ida, step2_dis_ida, step2_cha_ida_close, step2_dis_ida_close, step2_profit_ida, step2_cha_daaida, step2_dis_daaida)
    




def step3_optimize_idc(n_cycles:int, energy_cap:int, power_cap:int, idc_price_vector:list, step2_cha_daaida:list, step2_dis_daaida:list):
    
    """
    Calculates optimal charge/discharge schedule on the intraday continuous (idc) for a given 96-d idc_price_vector.

    Parameters:
    - n_cycles: Maximum number of allowed cycles
    - energy_cap: Energy capacity
    - power_cap: Power capacity
    - ida_price_vector: 96-dimensional ida price vector
    - step2_cha_daaida: Previous combined Buys on the DA Auction and ID Auction
    - step2_dis_daaida: Previous combined Sells on the DA Auction and ID Auction

    Returns:
    - step3_soc_idc: Resulting state of charge schedule
    - step3_cha_idc: Resulting charges on ID Continuous
    - step3_dis_idc: Resulting discharges on ID Continuous
    - step3_cha_idc_close: Resulting charges on ID Continuous to close previous DA or ID Auction positions
    - step3_dis_idc_close: Resulting discharge on ID Continuous to close previous DA or ID Auction positions
    - step3_profit_idc: Profit from Day-ahead auction trades
    - step3_cha_daaidaidc: Combined charges from DA Auction, ID Auction and ID Continuous
    - step3_dis_daaidaidc: Combined discharges from DA Auction, ID Auction and ID Continuous
    """



    # Initialize pyomo model:

    model = pyo.ConcreteModel()



    # Set parameters:

    # Number of hours
    model.H = pyo.RangeSet(0,len(idc_price_vector)/4-1) 

    # Number of quarters
    model.Q = pyo.RangeSet(1,len(idc_price_vector))         

    # Number of quarters plus 1
    model.Q_plus_1 = pyo.RangeSet(1,len(idc_price_vector)+1)  

    # Daily discharged energy limit
    volume_limit = energy_cap * n_cycles 



    # Initialize variables:

    # State of charge
    model.soc = pyo.Var(model.Q_plus_1, domain=pyo.Reals)

    # Charges on the intraday auction
    model.cha_idc = pyo.Var(model.Q, domain=pyo.NonNegativeReals, bounds=(0,1)) 

    # Discharges on the intraday auction
    model.dis_idc = pyo.Var(model.Q, domain=pyo.NonNegativeReals, bounds=(0,1))

    # Charges on the intraday auction to close previous positions from the day-ahead auction
    model.cha_idc_close = pyo.Var(model.Q, domain=pyo.NonNegativeReals, bounds=(0,1)) 

    # Charges on the intraday auction to close previous positions from the day-ahead auction
    model.dis_idc_close = pyo.Var(model.Q, domain=pyo.NonNegativeReals, bounds=(0,1))



    # Set Constraints: 





    def set_maximum_soc(model, q):
        """
        State of charge can never be higher than Energy Capacity. (Constraint 3.1)
        """
        return model.soc[q] <= energy_cap

    def set_minimum_soc(model, q):
        """
        State of charge can never be less than 0. (Constraint 3.2)
        """
        return model.soc[q] >= 0
    
    def set_first_soc_to_0(model):
        """
        State of charge at the first quarter must be 0. (Constraint 3.3)
        """
        return model.soc[1] == 0

    def set_last_soc_to_0(model):
        """
        State of charge at quarter 97 (i.e., first quarter of next day) must be 0. (Constraint 3.4)
        """
        return model.soc[97] == 0


    def soc_step_constraint(model, q):
        """
        The state of charge of each quarter equals the state if charge of the previous quarter plus charges minus discharges. (Constraint 3.5)
        """
        return model.soc[q+1] == model.soc[q] + power_cap/4  * (model.cha_idc[q] - model.dis_idc[q] + model.cha_idc_close[q] - model.dis_idc_close[q] + step2_cha_daaida[q-1] - step2_dis_daaida[q-1])


    def charge_cycle_limit(model):
        """
        Sum of all charges has to be below the daily limit. (Constraint 3.6)
        """
        return (np.sum(step2_dis_daaida) + sum(model.dis_idc[q] for q in model.Q) - sum(model.cha_idc_close[q] for q in model.Q)) * power_cap/4 <= volume_limit


    def discharge_cycle_limit(model):
        """
        Sum of all discharges has to be below the daily limit. (Constraint 3.7)
        """
        return (np.sum(step2_cha_daaida) + sum(model.cha_idc[q] for q in model.Q) - sum(model.dis_idc_close[q] for q in model.Q)) * power_cap/4 <= volume_limit


    def cha_close_logic(model, q):
        """
        cha_idc_close can only close or reduce existing dis_daaida positions. They can only be placed, where dis_daaida positions exist. (Constraint 3.8)
        """
        return model.cha_idc_close[q] <= step2_dis_daaida[q-1]
    

    def dis_close_logic(model, q):
        """
        dis_idc_close can only close or reduce existing cha_daaida positions. They can only be placed, where cha_daaida positions exist. (Constraint 3.9)
        """
        return model.dis_idc_close[q] <= step2_cha_daaida[q-1]
    

    def charge_rate_limit(model, q):
        """
         Sum of cha_idc[q] and cha_daaida[q] has to be less or equal to 1. (Constraint 3.10)
         """
        return model.cha_idc[q] + step2_cha_daaida[q-1] <= 1
   

    def discharge_rate_limit(model, q):
        """
         Sum of dis_idc[q] and dis_daaida[q] has to be less or equal to 1. (Constraint 3.11)
         """
        return model.dis_idc[q] + step2_dis_daaida[q-1] <= 1
    

    
    # Apply constraints on the model:

    model.set_maximum_soc = pyo.Constraint(model.Q_plus_1, rule=set_maximum_soc)
    model.set_minimum_soc = pyo.Constraint(model.Q_plus_1, rule=set_minimum_soc)
    model.set_first_soc_to_0 = pyo.Constraint(rule=set_first_soc_to_0)
    model.set_last_soc_to_0 = pyo.Constraint(rule=set_last_soc_to_0)
    model.soc_step_constraint = pyo.Constraint(model.Q, rule=soc_step_constraint)
    model.charge_cycle_limit = pyo.Constraint(rule=charge_cycle_limit)
    model.discharge_cycle_limit = pyo.Constraint(rule=discharge_cycle_limit)

    model.cha_close_logic = pyo.Constraint(model.Q, rule=cha_close_logic)
    model.dis_close_logic = pyo.Constraint(model.Q, rule=dis_close_logic)
    model.charge_rate_limit = pyo.Constraint(model.Q, rule=charge_rate_limit)
    model.discharge_rate_limit = pyo.Constraint(model.Q, rule=discharge_rate_limit)



    # Define objective function and solve the optimization problem
    # The objective is to maximize revenue from ID Continuous trades over all possible charge-discharge schedules.

    model.obj = pyo.Objective(expr=sum([idc_price_vector[q-1] * power_cap/4 * (model.dis_idc[q]+model.dis_idc_close[q]-model.cha_idc[q]-model.cha_idc_close[q]) for q in model.Q]), sense=pyo.maximize) 

    solver = set_glpk_solver(solvername='glpk', solverpath_exe='C:\\glpk\\w64\\glpsol')
    solver.solve(model, timelimit=5)



    # Retrieve arrays of resulting optimal soc/charge/discharge schedules after the ID Auction:

    step3_soc_idc = [model.soc[q].value for q in range(1, len(idc_price_vector) + 1)]
    step3_cha_idc = [model.cha_idc[q].value for q in range(1, len(idc_price_vector) + 1)]                   
    step3_dis_idc = [model.dis_idc[q].value for q in range(1, len(idc_price_vector) + 1)]                   
    step3_cha_idc_close = [model.cha_idc_close[q].value for q in range(1, len(idc_price_vector) + 1)]       
    step3_dis_idc_close = [model.dis_idc_close[q].value for q in range(1, len(idc_price_vector) + 1)]       


    # Calculate profit from Day-ahead auction trades:   

    step3_profit_idc = np.sum(((np.asarray(step3_dis_idc) + step3_dis_idc_close) - (np.asarray(step3_cha_idc) + step3_cha_idc_close)) * idc_price_vector) * power_cap/4
    

    # Calculate total physical charge discharge schedules of combined day-ahead and intraday auction trades:

    step3_cha_daaidaidc = np.asarray(step2_cha_daaida) - step3_dis_idc_close + step3_cha_idc
    step3_dis_daaidaidc = np.asarray(step2_dis_daaida) - step3_cha_idc_close + step3_dis_idc

    return(step3_soc_idc, step3_cha_idc, step3_dis_idc, step3_cha_idc_close, step3_dis_idc_close, step3_profit_idc, step3_cha_daaidaidc, step3_dis_daaidaidc)
    


