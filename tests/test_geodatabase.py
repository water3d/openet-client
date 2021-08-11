import os
import pytest

from . import TEST_DATA

import openet_client

import geopandas


def test_simple_feature_retrieval(features=os.path.join(TEST_DATA, "simple_features.geojson")):
	df = geopandas.read_file(features)
	df["centroid"]

	client = openet_client.OpenETClient()
	client.token = os.environ["OPENET_TOKEN"]
	client.geodatabase.get_feature_ids()