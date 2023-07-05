# Fleet-Demand-Platform
This repository gives the code for Fleet-Demand platform (FD platform). Full explaination of the FD platform can be found here. The FD platform is an API dedicated to connecting MATSim with external ride-pooling simulators, which enables the collaborative output between the two parts. Currently, the only ride-pooling extension in MATSim is the DRT extension. However, it still has limited functionality. To add a novel ride-pooling service design in MATSim, an external ride-pooling simulator needs to be converted to a new extension, which is illustrated in Figure 1.

<p align="center">
  <img src="https://github.com/BUILTNYU/Fleet-Demand-Platform/blob/main/Figures/Extension%20Conversion.jpg",width="600" height="400">
  <br>
  <em>Figure 1. Extension Conversion.</em>
</p>

By using the API, the extension conversion process can be eliminated. The API directly tranfer the information between MATSim and the external simualtor. The process is illustrated in Figure 2.

<p align="center">
  <img src="https://github.com/BUILTNYU/Fleet-Demand-Platform/blob/main/Figures/API%20structure.jpg",width="600" height="600">
  <br>
  <em>Figure 2. API structure.</em>
</p>

In the case of the FD platform, information on trip legs that involve the studied transportation mode are generated first using the given assumptions. Those trip legs are then extracted and used as input for the external simulator, which generates realized trip leg details. The details are subsequentially used to update the trip leg results previously generated by MATSim. As such, the updated trip itinerary can properly reflect the user experience involving the studied mode.

As illustrated in Figure 3, an agent’s chosen trip involves a public transit ride from home to work, a MOD service trip to have dinner, and another public transit ride back home. The mode choices are made by selecting the plan that maximizes the user’s utility between the 2 perceived trip itineraries. An initial estimation of the MOD trip time is 15 minutes with a given average travel speed of 15 miles/hr. After providing the trip start location and start time, the simulator generates a realized trip time of 20 minutes with a travel speed of 12 miles/hr. The result is then used to update the previous itinerary. The updated itinerary is therefore a combined result of MATSim and the external simulator.

<p align="center">
  <img src="https://github.com/BUILTNYU/Fleet-Demand-Platform/blob/main/Figures/Itinerary_update.jpg",width="600" height="600">
  <br>
  <em>Figure 3. Itinerary Update using the FD Simulator.</em>
</p>

Figure 4 is a detailed flow chart of the FD platform process. In summary, configuration and the initial trip plan file are inputted into MATSim. This process produces a preliminary passenger itinerary. Subsequently, trip details associated with ride-pooling services are extracted from this itinerary and transformed into a trip request log. This log is called by the local simulator to execute the service. The external simulator’s output contains the realized ride-pooling service details. The initial passenger itinerary and configuration file are then modified based on the ride-pooling service outcomes for the subsequent day of MATSim simulation. This process is iterated multiple times until a consistent output is achieved.

<p align="center">
  <img src="https://github.com/BUILTNYU/Fleet-Demand-Platform/blob/main/Figures/Flowchart.jpg",width="300" height="600">
  <br>
  <em>Figure 4. Workflow of the FD simulator process.</em>
</p>

The files provided are using part of New York City (NYC) network for simulation. The network contains Manhattan, Brooklyn, and Queens. The ride-pooling service area locates inside midtown Manhattan. The population file contains 35,000 agents. The subpopulation file describes te group each agent belongs to, which are "Low_Income" and "Not_Low_Income". The value of time (VOT) for “Not_Low_Income” is $9.98/hr, while for “Low_Income”, it is $5.68/hr. The configuration file defines two ride-pooling fleets called "drt_1" and "drt_2". The services provided by the two fleets are identical in this case. However, the parameters can be easily changed to reflect heterogenous services. The cost per trip for both services is $7 per trip. The disutility caused by the cost is reflected in the constant defined in the trip attribute. For all the supplement files (network, population, DVPRT input), please go to the [Zenondo](https://zenodo.org/record/8114990) page.

Files includes:

"FD_platform.py": Full code of the FD platform, which involves MATSim and an external simulator "DVRPT". The "DVRPT" simulator can be found [here](https://github.com/BUILTNYU/ridepooling-with-transfers).<br>
"config-with-mode-vehicles-drt-tele_2_income.xml": Configuration file for MATsim run in cycle 0.<br>
"config-with-mode-vehicles-drt-tele_2_income_updated.xml": Configuration file for MATsim run in following cycles.<br>

## License
The NYU NON-COMMERCIAL RESEARCH LICENSE is applied to Fleet-Demand-Platform (FD Platform). Please contact Joseph Chow (joseph.chow@nyu.edu) for commercial use.

For questions about the code, please contact: Hai Yang (hy1236@nyu.edu).
