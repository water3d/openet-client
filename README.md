# OpenET Python Client

A Python library for accessing OpenET data with support functions to enable quicker workflows.

Contents:
* [Examples](#examples)
    * [Raster API](#raster-api)
        * [Batching It](#batching-it)
        * [Doing work while you wait](#doing-work-while-you-wait--manual-control)
    * [Geodatabase API](#geodatabase-api)
* [Installation](#installation)
* [Notes](#notes)
* [Licensing](#licensing)

## Examples
Full documentation forthcoming in the future.

### Raster API
One common need is issuing a raster export command and then waiting to proceed until the
image is available and downloaded to the current machine. To do that:

WARNING - the current approach will make all exported rasters public in order
to be able to automatically download them - do not proceed to use this code if that isn't
acceptable.

```python
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
print(
    client.raster.downloaded_raster_paths)  # get the paths to the downloaded rasters (will be a list, even for a single raster)
```

#### Batching it
You may also want to queue up multiple rasters, then wait to download them all. To do that,
run the `raster.export` commands with `synchronous=False` (the default), then
issue a call to `wait_for_rasters`

```python
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
```

#### Doing work while you wait + manual control
You might also not want to *wait* around for the rasters to export, but still have control over the process. Here's how
to manually control the flow

```python
import openet_client

client = openet_client.OpenETClient("your_open_et_token_value_here")
arguments = {}  # some set of arguments, similar to the first example
my_raster = client.raster.export(arguments)

# ... any other code you like here - the OpenET API will do its work and make the raster ready - or not, depending on your place in their queue ...

client.raster.check_statuses()  # check the API's all_files endpoint to see which rasters are ready
if my_raster.status == openet_client.raster.STATUS_AVAILABLE  # check that the raster we want is now ready
    client.raster.download_available_rasters()  # try to download the ones that are ready and not yet downloaded (from this session)
```

### Geodatabase API
The geodatabase API is supported, including functions that allow pulling ET data for spatial objects.
```python
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
    id_field="UniqueID",
    output_field="et_2018_mean_ensemble_mean",
    endpoint="timeseries/features/stats/annual"
)
```

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

Lower level access is also available, such as simple wrappers of API functions. Documentation to come.

## Installation
```shell
python -m pip install openet-client
```

If you want support for spatial operations that help with wrapping the geodatabase API, also run
```shell
python -m pip install openet-client[spatial]
```
This will attempt to install `geopandas` and `fiona`, which are required for spatial processing. These packages may have trouble (especially on Windows) due to external dependencies. We recommend using a conda environment and the conda packages to simplify that install. In that case, simply use conda to install geopandas to install the necessary dependencies instead of running the above command.

You may also download the repository
and run `python setup.py install` to use the package, replacing
`python` with the full path to your python interpreter, if necessary.

## Notes
Lots of important things are missing from this project right now, including full documentation (though functions are documented
in the code), better handling of exceptions, logging, edge cases, etc. It is mostly a demonstration case right now and also for internal use. Contributions welcome.

Future work could also consider using some async patterns to kick off raster exports, but then the user is still left polling
for the file on their own. A better approach is probably still to follow the example above

## Licensing
This project is released under the MIT license.

This project is not affiliated with OpenET or DRI and is not an official release of the OpenET project.