Installation
================

.. code-block:: shell

    python -m pip install openet-client

If you want support for spatial operations that help with wrapping the geodatabase API, also run

.. code-block:: shell

    python -m pip install openet-client[spatial]

This will attempt to install `geopandas` and `fiona`, which are required for spatial processing. These packages may have trouble (especially on Windows) due to external dependencies. We recommend using a conda environment and the conda packages to simplify that install. In that case, simply use conda to install geopandas to install the necessary dependencies instead of running the above command.

You may also download the repository
and run :code:`python setup.py install` to use the package, replacing
:code:`python` with the full path to your python interpreter, if necessary.