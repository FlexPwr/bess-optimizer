## Implementation of the FlexPower Cross-Market BESS Optimization Model in Python using pyomo. 

This repository contains the Cross-Market Optimization model which is also used to calculate the [Flex Index (wip link)](https://flex-power.energy/). 

The model calculates the optimal charge-discharge-schedule of a BESS (Battery Energy Storage System) by sequentially optimizing over three German markets: The Day-Ahead auction, the intraday auction and the intraday continuous market (approximated as ID1). The logic is explained in more detail [here (wip link)](https://flex-power.energy/). The optimizer is implemented using Pyomo, an open source optimization modelling package for Python.

Note that you have to install the [GLPK solver](https://www.gnu.org/software/glpk/) on your machine to run the model. 


[WIP] Also mathematical model supplied. The constraints in the code are numbered and correspond to the mathematical model 




• The file [flexpower_optimizer.py](flexpower_optimizer.py) includes the implementation of the BESS optimization for the DA Auction, ID Auction and ID Continuous markets. 

• The notebook [example.ipynb](example.ipynb) shows the optimization for an example day.
