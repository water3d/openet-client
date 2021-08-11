import tempfile
import time
from collections import OrderedDict

import geopandas
import pandas

MAX_FEATURE_IDS_LIST_LENGTH = 100
RATE_LIMIT = 250  # ms

FEATURE_TYPE_GEOPANDAS = "geopandas"
FEATURE_TYPE_GEOJSON = "geojson"
FEATURE_TYPE_ARCPY = "arcpy"
FEATURE_TYPE_SHAPEPLY = "shapely"


def get_coords_shapely(geometry):
	coords = geometry.centroid.coords
	return (coords.x, coords.y)


def get_coords_arcpy(geometry):
	centroid = geometry.centroid.projectAs(4326)
	return (centroid.X, centroid.Y)


class Geodatabase(object):

	def __init__(self, client):
		self.client = client

	def get_et_for_features(self, params, features, feature_type, id_field, output_field, geometry_field="geometry", endpoint="features/stats/annual"):
		"""
			Takes one of multiple data formats (user specified, we're not inspecting it - options are
			geopandas, geojson) and gets its
			coordinate values, then gets the field IDs in OpenET for the coordinate pair, retrieves the ET data
			and returns it as a geopandas data frame with the results in the specified output_field
		:param params:
		:param features:
		:param endpoint: which features endpoint should it use?
		:return:
		"""

		if endpoint.startswith("timeseries/"):  # strip it off the front if they included it
			endpoint.replace("timeseries/", "")

		if feature_type not in (FEATURE_TYPE_GEOPANDAS, FEATURE_TYPE_GEOJSON):
			raise ValueError(f"Feature type must be in ({FEATURE_TYPE_GEOPANDAS}, {FEATURE_TYPE_GEOJSON}) to get geometries and retrieve ET. CHeck that the feature_type parameter is specified correctly")

		if feature_type == FEATURE_TYPE_GEOJSON:
			features = geopandas.GeoDataFrame.from_features(features)

		features_wgs = features.to_crs(4326)
		features_wgs["centroid",] = features_wgs.geometry.centroid

		# we're going to have to get the feature IDs one by one if we want a reliable mapping of polygons to openET features
		# which isn't ideal and we'll want to rate limit it to make sure we don't abuse the API too heavily
		# we'll probably also want to do some form of caching or saving the feature IDs to the geopandas dfs so that
		# we don't have to go back and get it again if we already got it.

		openet_feature_ids = self.get_feature_ids(features_wgs, field="centroid")
		temp_feature_outputs = tempfile.mktemp(suffix=".csv", prefix="openet_client")
		openet_feature_ids.to_csv(temp_feature_outputsmet)

		#df_length = len(features_wgs)
		#start = 0
		#end = min(MAX_FEATURE_IDS_LIST_LENGTH, df_length)
		#while start < df_length:
		#	partial_df = features_wgs[start:end, ]
		#	start += MAX_FEATURE_IDS_LIST_LENGTH
		#	end += MAX_FEATURE_IDS_LIST_LENGTH
		#	end = min(MAX_FEATURE_IDS_LIST_LENGTH, df_length)  # we'll only check end because we won't enter the next iteration if start < df_length

	def get_feature_ids(self, features, field=None, wait_time=RATE_LIMIT):
		"""
			An internal method used to get a list of coordinate pairs and return the feature ID. Values come back as a dictionary
			where the input item in the list (coordinate pair shown as DD Longitude space DD latitude)
			is a dictionary key and the value is the OpenET featureID
		:param features:
		:param field: when field is defined, features will be a pandas data frame with a field that has the coordinate values to use.
						In that case, results will be joined back to the data frame as the field openet_feature_id.
		:param wait_time: how long in ms should we wait between subsequent requests?
		:return:
		"""
		if field and not isinstance(features, pandas.DataFrame):
			raise ValueError("A field name was provided, but `features` are not a Pandas DataFrame. Must be a DataFrame to proceed, or a field name should not be provided")

		if field:
			inputs = features[field,]
		else:
			inputs = features

		outputs = OrderedDict()
		for item in inputs:
			params = {"coordinates": item, "spatial_join_type": "intersect", "override": "False"}
			results = self.feature_ids_list(params)
			ids = results.json()["feature_unique_ids"]
			if len(ids) > 0:
				outputs[item] = ids[0]
			else:
				outputs[item] = None

			time.sleep(wait_time/1000)

		if field:
			return pandas.DataFrame({field: outputs.keys(), "openet_feature_id": outputs.values()})
		else:
			return outputs

	def feature_ids_list(self, params=None):
		endpoint = "metadata/openet/region_of_interest/feature_ids_list"
		results = self.client.send_request(endpoint, params, method="post")
		return results
