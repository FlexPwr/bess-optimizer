## Implementation of the FlexPower Three Market BESS Optimization Model in Python using pyomo


This repository contains the Three Market Optimization model which is also used to calculate the [FlexIndex](https://flex-power.energy/services/flex-trading/flex-index/). 

The model calculates the optimal charge-discharge-schedule of a BESS (Battery Energy Storage System) by sequentially optimizing over three German markets: The Day-Ahead auction, the intraday auction and the intraday continuous market (approximated as ID1). The logic is explained in more detail [here](https://flex-power.energy/services/flex-trading/flex-index/). The optimizer is implemented using Pyomo, an open source optimization modelling package for Python.

With open-sourcing this, we want to help build a solid public knowledge base for flexbility optimization, which is available to anyone and can help push forward the whole flexibility market. If you build upon this model, or use it in some other way, we would be happy to see you contribute to this common goal as well. 

Note that you have to install the [GLPK solver](https://www.gnu.org/software/glpk/) on your machine to run the model. 

#### Contents 

• The file [optimizer.py](optimizer.py) includes the implementation of the BESS optimization for the DA Auction, ID Auction and ID Continuous markets. 

• The notebook [example.ipynb](example.ipynb) shows how the optimization works for an example day.

• [mathematical_formulation.pdf](mathematical_formulation.pdf) is a document, which includes the mathematical formulation of the optimization problem. It is meant to accompany the code implementation. The model constraints in the code and in the mathematical formulation are numbered accordingly. 

• [LICENSE](LICENSE) is the copyright license of this work.


#### Abbreviations

The formulation includes a number of abbreviations, below is a short list with explanations:

DAA:         Day-ahead Auction. In the German case this is the EPEX Day-ahead auction which takes place at 12:00h on the day before delivery.

IDA:         Intraday Auction. In the German case this is the EPEX Intraday auction which takes place at 15:00h on the day before delivery. 

IDC:         Intraday Continuous Market. Opens at 15:00h on the day before delivery and closes 5 minutes before delivery.

ID1:         The volume-weighted average price of all trades in a specific contract on the Intraday Continuous market.

SOC[q]:      State of Charge of a Battery at quarter q.

CHA[q]:      Charge rate of a Battery at quarter q.

DIS[q]:      Discharge rate of a Battery at quarter q.


