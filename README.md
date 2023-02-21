<a href="https://www.fz-juelich.de/en/iek/iek-3"><img src="https://raw.githubusercontent.com/OfficialCodexplosive/README_Assets/862a93188b61ab4dd0eebde3ab5daad636e129d5/FJZ_IEK-3_logo.svg" alt="FZJ Logo" width="300px"></a>

# HiSim Building Sizer

The HiSim Building Sizer is a tool supporting the choice and sizing of technical equipment of a building. For example the best size for batteries can be chosen via the building sizer or investment decision in electric vehicles or a heat pumps can be supported. The decisions are based on heuristic optimization (evolutionary algorithms), which call upon simulations of the python package [HiSim](https://github.com/FZJ-IEK3-VSA/HiSim), which simulates and evaluates building systems for selected configurations.
All building parameters available in HiSim can be varied in the Building Sizer, e.g., photovoltaic system peak power, battery capacity, the or consideration of electric vehicles and heat pumps or smart control of dish washers and washing machines.
Within the evolutionary algorithm, the distributed job manager [UTSP](https://github.com/FZJ-IEK3-VSA/UTSP_Client) is utilized to calculate all HiSim simulations of a single generation in parallel.


## About Us
<p align="center"><a href="https://www.fz-juelich.de/en/iek/iek-3"><img src="https://github.com/OfficialCodexplosive/README_Assets/blob/master/iek3-wide.png?raw=true" alt="Institut TSA"></a></p>
We are the <a href="https://www.fz-juelich.de/en/iek/iek-3">Institute of Energy and Climate Research - Techno-economic Systems Analysis (IEK-3)</a> belonging to the <a href="https://www.fz-juelich.de/en">Forschungszentrum Jülich</a>. Our interdisciplinary department's research is focusing on energy-related process and systems analyses. Data searches and system simulations are used to determine energy and mass balances, as well as to evaluate performance, emissions and costs of energy systems. The results are used for performing comparative assessment studies between the various systems. Our current priorities include the development of energy strategies, in accordance with the German Federal Government’s greenhouse gas reduction targets, by designing new infrastructures for sustainable and secure energy supply chains and by conducting cost analysis studies for integrating new technologies into future energy market frameworks.
We are owners of the repository and set up the framework of the evolutionary algorithm including the job manager UTSP.

<br>
<p align="center"><a href="https://www.4wardenergy.at/en"><img src="logos/logo_4ER.png" alt="" width="400px"></a></p>
<a href="https://www.4wardenergy.at/en"> 4ward Energy Research GmbH </a> contributes to the building sizer by the implementation of the core functions of the evolutionary algorithm and interfaces to HiSIM calls.

<p align="center"><a href="https://www.deusto.es/en/inicio"><img src="logos/logo_deusto.png" alt=""></a></p>
<a href="https://www.deusto.es/en/inicio"> UDEUSTO </a> supported the building sizer especially when it comes to the design of the optimization approach.


## Acknowledgement
This project has received funding from the European Union’s Horizon 2020 research and innovation programme under grant agreement No 891943. 

<img src="logos/eulogo.png" alt="EU Logo" width="200px" style="float:right"></a>

<a href="https://www.why-h2020.eu/"><img src="logos/whylogo.jpg" alt="WHY Logo" width="200px" style="float:right"></a>