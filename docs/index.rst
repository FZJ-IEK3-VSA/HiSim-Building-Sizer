.. HiSim Building Sizer documentation master file, created by
   sphinx-quickstart on Fri Feb 17 12:50:51 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: http://www.fz-juelich.de/SharedDocs/Bilder/IBG/IBG-3/DE/Plant-soil-atmosphere%20exchange%20processes/INPLAMINT%20(BONARES)/Bild3.jpg?__blob=poster
    :target: http://www.fz-juelich.de/iek/iek-3/EN/Forschung/_Process-and-System-Analysis/_node.html
    :width: 230px
    :alt: Forschungszentrum Juelich Logo
    :align: right

Welcome to HiSim Building Sizer's documentation!
================================================
The 'HiSim Building Sizer' is a tool supporting the choice and sizing of technical equipment of a building. For example the best size for batteries can be chosen via the building sizer or investment decisions in electric vehicles or heat pumps can be supported. The decisions are based on heuristic optimization (evolutionary algorithms), which call upon simulations of the python package `HiSim <https://github.com/FZJ-IEK3-VSA/HiSim>`_. HiSim simulates total energy curves for selected building configurations and evaluates key performance indicators like self consumption rates or autarky rates based on them.

All building parameters available in HiSim can be varied in the Building Sizer, e.g., photovoltaic system peak power, battery capacity, the consideration of electric vehicles and heat pumps or smart control of dish washers and washing machines.
Within the evolutionary algorithm, the distributed job manager `UTSP <https://github.com/FZJ-IEK3-VSA/UTSP_Client>`_ is utilized to calculate all HiSim simulations of a single generation in parallel.



.. toctree::
   :maxdepth: 1
   :caption: Contents:

   tutorial
   modules

Documentation Reference
==============================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

About Us
==================

.. figure:: https://github.com/OfficialCodexplosive/README_Assets/blob/master/iek3-wide.png?raw=true
   :target: https://www.fz-juelich.de/iek/iek-3/DE/Home/home_node.html
   :align: center
   :alt: IEK-3 Team

   Forschungszentrum Jülich IEK-3 Team

We are the `Institute of Energy and Climate Research - Techno-economic Systems Analysis (IEK-3) <https://www.fz-juelich.de/iek/iek-3/DE/Home/home_node.html>`_ belonging to the `Forschungszentrum Jülich <https://www.fz-juelich.de>`_. Our interdisciplinary institute's research is focusing on energy-related process and systems analyses. Data searches and system simulations are used to determine energy and mass balances, as well as to evaluate performance, emissions and costs of energy systems. The results are used for performing comparative assessment studies between the various systems. Our current priorities include the development of energy strategies, in accordance with the German Federal Government’s greenhouse gas reduction targets, by designing new infrastructures for sustainable and secure energy supply chains and by conducting cost analysis studies for integrating new technologies into future energy market frameworks. We are owners of the repository and set up the framework of the evolutionary algorithm including the job manager UTSP.

<p align="center"><a href="https://www.4wardenergy.at/en"><img src="logos/logo_4ER.png" alt="" width="400px"></a></p>

.. figure:: logos/logo_4ER.png
   :target: https://www.4wardenergy.at/en
   :align: center
   :width: 400px

`4ward Energy Research GmbH <https://www.4wardenergy.at/en>`_ contributes to the building sizer by the implementation of the core functions of the evolutionary algorithm and interfaces to HiSIM calls.

.. figure:: logos/logo_deusto.png
   :target: https://www.deusto.es/en/inicio
   :align: center
   :width: 400px

`Universidad de Deusto <https://www.deusto.es/en/inicio>`_ supported the building sizer especially when it comes to the design of the optimization approach.

License
=========================================================
HiSim Building Sizer is distributed under `MIT License <https://github.com/FZJ-IEK3-VSA/HiSim-Building-Sizer/blob/main/LICENSE>`_ .

Copyright (C) 2022 FZ Jülich - IEK 3
