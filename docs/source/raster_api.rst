Using the Client with the OpenET Raster API
===================================================

Examples
-----------------
One common need is issuing a raster export command and then waiting to proceed until the
image is available and downloaded to the current machine. To do that:

.. warning::
    The current approach will make all exported rasters public in order
    to be able to automatically download them - do not proceed to use this code if that isn't
    acceptable.

.. code-block:: python

    import openet_client

    # arguments are in the form of a dictionary with keys and
    # values conforming to https://open-et.github.io/docs/build/html/ras_export.html
    # In the future, geometry may accept OGR or GEOS objects and create the string itself
    arguments = {
        'start_date': '2016-01-01',
        'end_date': '2016-03-20',
        'geometry': '-120.72612533471566,37.553211935016215,-120.72612533471566,37.474782294423676,-120.59703597924691,37.474782294423676,-120.59703597924691,37.553211935016215',
        'filename_suffix': 'client_test',
        'variable': 'et',
        'model': 'ensemble',
        'units': 'metric'
    }

    client = openet_client.OpenETClient("your_open_et_token_value_here")

    # note that the path matches OpenET's raster export endpoint
    client.raster.export(arguments, synchronous=True)  # synchronous says to wait for it to download before proceeding
    print(client.raster.downloaded_raster_paths)  # get the paths to the downloaded rasters (will be a list, even for a single raster)

Batching it
________________
You may also want to queue up multiple rasters, then wait to download them all. To do that,
run the :code:`raster.export` commands with :code:`synchronous=False` (the default), then
issue a call to :code:`wait_for_rasters`

.. code-block:: python

    import openet_client

    client = openet_client.OpenETClient("your_open_et_token_value_here")
    arguments1 = {}  # some set of arguments, similar to the first example
    arguments2 = {}  # same
    client.raster.export(arguments1)
    client.raster.export(arguments2)
    client.raster.wait_for_rasters()  # this will keep running until all rasters are downloaded - it will wait up to a day by default, but that's configurable by providing a `max_time` argument in seconds
    print(client.raster.downloaded_raster_paths)  # a list with all downloaded rasters
    # or
    rasters = client.raster.registry.values()  # get all the Raster objects including remote URLs and local paths


Doing work while you wait + manual control
++++++++++++++++++++++++++++++++++++++++++++++++++
You might also not want to *wait* around for the rasters to export, but still have control over the process. Here's how
to manually control the flow

.. code-block:: python

    import openet_client

    client = openet_client.OpenETClient("your_open_et_token_value_here")
    arguments = {}  # some set of arguments, similar to the first example
    my_raster = client.raster.export(arguments)

    # ... any other code you like here - the OpenET API will do its work and make the raster ready - or not, depending on your place in their queue ...

    client.raster.check_statuses()  # check the API's all_files endpoint to see which rasters are ready
    if my_raster.status == openet_client.raster.STATUS_AVAILABLE  # check that the raster we want is now ready
        client.raster.download_available_rasters()  # try to download the ones that are ready and not yet downloaded (from this session)


Raster API Class and Methods
--------------------------------
.. automodule:: openet_client.raster
    :members:
