Using the Client with the OpenET Geodatabase API
=====================================================

The geodatabase API is supported, including functions that allow pulling ET data for spatial objects.

.. code-block:: python

    import os
    import geopandas
    import openet_client

    features = "PATH TO YOUR SPATIAL DATA" # must be a format geopandas supports, which is most spatial data
    df = geopandas.read_file(features)

    client = openet_client.OpenETClient()
    client.token = os.environ["OPENET_TOKEN"]
    result = client.geodatabase.get_et_for_features(params={
            "aggregation": "mean",
            "feature_collection_name": "CA",
            "model": "ensemble_mean",
            "variable": "et",
            "start_date": 2018,
            "end_date": 2018
        },
        features=df,
        feature_type=openet_client.geodatabase.FEATURE_TYPE_GEOPANDAS,
        output_field="et_2018_mean_ensemble_mean",
        endpoint="timeseries/features/stats/annual"
    )

More documentation for this portion of the API will be forthcoming, but note that, like the raster API, you provide a set of
parameters that will be sent directly to OpenET based on the endpoint. The function `get_et_for_features` takes many additional
parameters that indicate what kind of data you're providing as an input, in this case a geopandas data frame.
You also can provide different geodatabase feature endpoints.

This function then calculates the centroid of each feature, finds the fields in OpenET that are associated with those centroids,
then downloads the ET data for those fields based on the `params` you provide. It attaches the ET
to a data frame as a new field with the name specified in `output_field`. Note that for large features, it does not currently
retrieve ET for multiple fields and aggregate them to the larger area. For that functionality, use the raster functionality.

This function also caches the field IDs for the features to avoid future lookups that use API quota. Rerunning the
same features with different params will run significantly faster and use significantly fewer API requests behind the scenes.


Geodatabase API Access Class and Methods
----------------------------------------------
.. autoclass:: openet_client.Geodatabase
    :members:
