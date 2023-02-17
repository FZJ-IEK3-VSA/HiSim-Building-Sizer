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

The `HiSim Building Sizer` is a tool for optimizing the technical equipment of a building. The python package `HiSim <https://github.com/FZJ-IEK3-VSA/HiSim>`_ is used to simulate and evaluate building systems for select configurations. Using an evolutionary algorithm, many possible building configurations are tested to identify the best combination of components.

All building parameters available in HiSim can be varied in the Building Sizer, e.g., photovoltaic system peak power, battery capacity, or consideration of electric vehicles.
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

We are the `Institute of Energy and Climate Research - Techno-economic Systems Analysis (IEK-3) <https://www.fz-juelich.de/iek/iek-3/DE/Home/home_node.html>`_ belonging to the `Forschungszentrum Jülich <https://www.fz-juelich.de>`_. Our interdisciplinary institute's research is focusing on energy-related process and systems analyses. Data searches and system simulations are used to determine energy and mass balances, as well as to evaluate performance, emissions and costs of energy systems. The results are used for performing comparative assessment studies between the various systems. Our current priorities include the development of energy strategies, in accordance with the German Federal Government’s greenhouse gas reduction targets, by designing new infrastructures for sustainable and secure energy supply chains and by conducting cost analysis studies for integrating new technologies into future energy market frameworks.

License
=========================================================
HiSim Building Sizer is distributed under `MIT License <https://github.com/FZJ-IEK3-VSA/HiSim-Building-Sizer/blob/main/LICENSE>`_ .

Copyright (C) 2022 FZ Jülich - IEK 3
