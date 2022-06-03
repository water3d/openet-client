Getting Started
=================

The OpenET Client Python package provides convenience functions to make it easier to
request and retrieve data from OpenET's API, such as tools to match your spatial
data to OpenET's and send requests for raster data and manage the download process.

Core functionality of the package includes:

 * Automatic matching of any geopandas-compatible dataset (including Shapefiles) with OpenET geodatabase API fields to make downloading timeseries data easier
 * Fully automated retrieval and attachment of ET values back to input datasets - provide the dataset and API parameters and receive the results back as a field on the input data
 * Send multiple requests to the raster API and have the client manage waiting for and downloading the data when it's ready, or have your code continue doing other work and manually trigger a download check later on.


.. note::

    Using this client still requires knowing some information about the OpenET API itself,
    including the API endpoints you wish to use and the parameters you want to send to the API
    endpoints. We recommend familiarizing yourself with the `documentation for the OpenET API <https://open-et.github.io/docs/build/html/index.html>`_ itself
    to use this Python package. While the API documentation expects you to handle everything related to sending requests
    to the API and understanding the response, this package handles those tasks for you, but you need to know which requests you want to send.

    The OpenET API's documentation can be found at https://open-et.github.io/docs/build/html/index.html
