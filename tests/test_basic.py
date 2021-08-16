import pytest

import os

import openet_client

raster_params = {
    'start_date': '2016-01-01',
    'end_date': '2016-03-20',
    'geometry': '-120.72612533471566,37.553211935016215,-120.72612533471566,37.474782294423676,-120.59703597924691,37.474782294423676,-120.59703597924691,37.553211935016215',
    'filename_suffix': 'client_test',
    'variable': 'et',
    'model': 'ensemble',
    'units': 'metric'
}


def test_basic():
    client = openet_client.OpenETClient()
    client.token = os.environ["OPENET_TOKEN"]
    client.raster.export(params=raster_params, synchronous=True)
    print(client.raster.downloaded_raster_paths)


