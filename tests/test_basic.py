import pytest

import os

import openet_client

raster_params_old_large = {
    'start_date': '2016-01-01',
    'end_date': '2016-03-20',
    'geometry': '-120.72612533471566,37.553211935016215,-120.72612533471566,37.474782294423676,-120.59703597924691,37.474782294423676,-120.59703597924691,37.553211935016215',
    'filename_suffix': 'client_test',
    'variable': 'et',
    'model': 'ensemble',
    'units': 'metric'
}

raster_params = {
    'start_date': '2016-01-01',
    'end_date': '2016-03-20',
    'geometry': '-119.39062,36.19926,-119.35817,36.19926,-119.35817,36.16867,-119.39062,36.16867',
    'filename_suffix': 'client_test',
    'variable': 'et',
    'model': 'ensemble',
    'units': 'metric'
}

raster_params_sample = {
    'start_date': '2018-01-01',
    'end_date': '2018-12-31',
    'geometry': '-121.57543,36.99152,-121.50564,36.99152,-121.50564,36.92374,-121.57543,36.92374',
    'filename_suffix': 'vw_sample',
    'variable': 'et',
    'model': 'ensemble',
    'units': 'metric'
}

raster_params_sample_tiny = {
    'start_date': '2018-01-01',
    'end_date': '2018-12-31',
    'geometry': '-121.53565,36.94787,-121.52588,36.94787,-121.52588,36.93911,-121.53565,36.93911',
    'filename_suffix': 'vw_sample',
    'variable': 'et',
    'model': 'ensemble',
    'units': 'metric'
}

raster_params_sample_super_tiny = {
    'start_date': '2018-01-01',
    'end_date': '2018-12-31',
    'geometry': '-121.53565,36.94787,-121.53565,36.946027,-121.533428,36.946027,-121.533428,36.94787',
    'filename_suffix': 'vw_sample',
    'variable': 'et',
    'model': 'ensemble',
    'units': 'metric'
}

def test_basic():
    client = openet_client.OpenETClient()
    client.token = os.environ["OPENET_TOKEN"]
    client.raster.export(params=raster_params_sample_super_tiny, synchronous=True)
    print(client.raster.downloaded_raster_paths)


