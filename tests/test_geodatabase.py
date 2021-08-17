import os
import pytest

FOLDER = os.path.dirname(os.path.abspath(__file__))
TEST_DATA = os.path.join(FOLDER, "test_data")

import openet_client

import geopandas


def test_simple_feature_retrieval(features=os.path.join(TEST_DATA, "vw_landiq.geojson")):
	df = geopandas.read_file(features)
	#df["centroid"]

	client = openet_client.OpenETClient()
	client.token = os.environ["OPENET_TOKEN"]
	result = client.geodatabase.get_et_for_features(params={
		"aggregation": "mean",
		"feature_collection_name": "CA",
		"model": "ensemble_mean",
		"variable": "et_2018_ensemble_mean_mean",
		"start_date": 2018,
		"end_date": 2018
	}, features=df, feature_type=openet_client.geodatabase.FEATURE_TYPE_GEOPANDAS, id_field="UniqueID", output_field="et")

	result.to_file(os.path.join(TEST_DATA, "results.gpkg"), layer='et_vw_results', driver="GPKG")
	print(result)