## Implementation of the FlexPower Cross-Market BESS Optimization Model in Python using pyomo

This repository contains the Cross-Market Optimization model which is also used to calculate the [Flex Index (wip link)](https://flex-power.energy/?page_id=5811). 

The model calculates the optimal charge-discharge-schedule of a BESS (Battery Energy Storage System) by sequentially optimizing over three German markets: The Day-Ahead auction, the intraday auction and the intraday continuous market (approximated as ID1). The logic is explained in more detail [here (wip link)](https://flex-power.energy/?page_id=5811). The optimizer is implemented using Pyomo, an open source optimization modelling package for Python.

Note that you have to install the [GLPK solver](https://www.gnu.org/software/glpk/) on your machine to run the model. 



• The file [flexpower_optimizer.py](flexpower_optimizer.py) includes the implementation of the BESS optimization for the DA Auction, ID Auction and ID Continuous markets. 

• The notebook [example.ipynb](example.ipynb) shows how the optimization works for an example day.

• [bess_optimizer_mathematical.pdf](bess_optimizer_mathematical.pdf) is a document, which includes the mathematical formulation of the optimization problem. It is meant to accompany the code implementation. The model constraints in the code and in the mathematical formulation are numbered accordingly. 

• [LICENSE](LICENSE) is the copyright license of this work.
