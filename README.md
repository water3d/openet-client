# OpenET Python Client

A Python library for accessing OpenET data

Currently just provides access to the raster export and download endpoints.

## Examples
One common need is issuing a raster export command and then waiting to proceed until the
image is available and downloaded to the current machine. To do that:

WARNING - the current approach will make all exported rasters public in order
to be able to automatically download them - do not proceed to use this code if that isn't
acceptable.

```python
import openet

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

client = openet.OpenETClient("your_open_et_token_value_here")

# note that the path matches OpenET's raster export endpoint
client.raster.export(arguments, synchronous=True)  # synchronous says to wait for it to download before proceeding
print(client.raster.downloaded_raster_paths)  # get the paths to the downloaded rasters (will be a list, even for a single raster)
```

### Batching it
You may also want to queue up multiple rasters, then wait to download them all. To do that,
run the `raster.export` commands with `synchronous=False` (the default), then
issue a call to `wait_for_rasters`
```python
import openet
client = openet.OpenETClient("your_open_et_token_value_here")
arguments1 = {}  # some set of arguments, similar to the first example
arguments2 = {}  # same
client.raster.export(arguments1)  
client.raster.export(arguments2)
client.raster.wait_for_rasters()  # this will keep running until all rasters are downloaded - it will wait up to a day by default, but that's configurable by providing a `max_time` argument in seconds
print(client.raster.downloaded_raster_paths)  # a list with all downloaded rasters
```

## Notes
Lots of important things are missing from this project right now, including full documentation and better handling
of exceptions, logging, edge cases, a setupfile, etc. It is mostly a demonstration case right now and also for internal use. Contributions welcome.

## Licensing
This project is released under the MIT license.

This project is not affiliated with OpenET or DRI and is not an official release of the OpenET project.