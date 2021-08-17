import tempfile
import time
import logging
from collections import OrderedDict

try:
	import fiona  # try importing fiona directly, because otherwise geopandas defers errors to later on when it actually needs to use it
	import geopandas
	GEOPANDAS_AVAILABLE = True
except ImportError:
	GEOPANDAS_AVAILABLE = False
	logging.warning("Can't load fiona or geopandas - will not be able to undertake spatial operations")

import pandas

MAX_FEATURE_IDS_LIST_LENGTH = 100
RATE_LIMIT = 5000  # ms

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

	def get_et_for_features(self, params, features, feature_type, id_field, output_field, geometry_field="geometry", endpoint="timeseries/features/stats/annual", wait_time=RATE_LIMIT):
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

		if GEOPANDAS_AVAILABLE is False:
			# we'll check it this way because that way we can let people who don't want to get a working fiona/geopandas environment
			# use the application without it confusingly failing on them at runtime.
			raise EnvironmentError("Fiona or Geopandas is unavailable - check that Fiona and Geopandas are both installed and that importing Fiona works - cannot proceed without a working installation with fiona and geopandas")

		if endpoint.startswith("timeseries/"):  # strip it off the front if they included it
			endpoint.replace("timeseries/", "")

		if feature_type not in (FEATURE_TYPE_GEOPANDAS, FEATURE_TYPE_GEOJSON):
			raise ValueError(f"Feature type must be in ({FEATURE_TYPE_GEOPANDAS}, {FEATURE_TYPE_GEOJSON}) to get geometries and retrieve ET. CHeck that the feature_type parameter is specified correctly")

		if feature_type == FEATURE_TYPE_GEOJSON:
			features = geopandas.GeoDataFrame.from_features(features)

		features_wgs = features.to_crs(4326)
		features_wgs.loc[:, "centroid_geom"] = features_wgs["geometry"].centroid
		def set_centroid(row):
			"""
				There's a better way to do this, but my Pandas-fu is failing me right now.
				Make a function to set the centroid as text elementwise
			:param row:
			:return:
			"""
			# get the values as a string, but truncate it to 7 places for precision so that we can more reliably cache it
			row["centroid"] = f'{round(row["centroid_geom"].x, 7)} {round(row["centroid_geom"].y, 7)}'
			return row
		features_wgs = features_wgs.apply(set_centroid, axis=1)
		features_wgs = features_wgs.drop(columns=["centroid_geom"])  # drop it so it doesn't create output problems later

		# we're going to have to get the feature IDs one by one if we want a reliable mapping of polygons to openET features
		# which isn't ideal and we'll want to rate limit it to make sure we don't abuse the API too heavily
		# we'll probably also want to do some form of caching or saving the feature IDs to the geopandas dfs so that
		# we don't have to go back and get it again if we already got it.

		openet_feature_ids = self.get_feature_ids(features_wgs, field="centroid")
		#temp_feature_outputs = tempfile.mktemp(suffix=".csv", prefix="openet_client")
		#openet_feature_ids.to_csv(temp_feature_outputs)

		features_wgs = features_wgs.merge(openet_feature_ids, on="centroid")
		feature_ids = openet_feature_ids["openet_feature_id"].tolist()

		df_length = len(feature_ids)
		start = 0
		end = min(MAX_FEATURE_IDS_LIST_LENGTH, df_length)
		results = []
		while start < df_length:
			partial_list = [feat for feat in feature_ids[start:end] if feat is not None]  # remove the null values and filter to the batch size
			params["field_ids"] = str(partial_list).replace(" ", "").replace("\'", '"')  # what's weird is we basically have to send this as a python list, so we need to stringify it first so requests doesn't process it
			response = self.client.send_request(endpoint, method="post", disable_encoding=True, **params)
			results.extend(response.json())

			time.sleep(wait_time / 1000)

			start += MAX_FEATURE_IDS_LIST_LENGTH
			end += MAX_FEATURE_IDS_LIST_LENGTH
			end = min(MAX_FEATURE_IDS_LIST_LENGTH, df_length)  # we'll only check end because we won't enter the next iteration if start < df_length

		openet_output_field_name = "data_value" if "aggregation" not in params else params["aggregation"]

		results_reformed = [{output_field: item[openet_output_field_name], "openet_feature_id": item["feature_unique_id"]}
						for item in results]
		results_df = pandas.DataFrame(results_reformed)

		final = features_wgs.merge(results_df, on="openet_feature_id")
		return final

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
			inputs = features[field]
		else:
			inputs = features

		outputs = OrderedDict()
		for item in inputs:
			# check the cache first - we might not need an API request for their field ID
			cached_value = self.client.cache.check_gdb_cache(key=item)
			if cached_value is False:  # False indicates no records, None indicates it's there and Null
				params = {"coordinates": item, "spatial_join_type": "intersect", "override": "False"}
				results = self.feature_ids_list(params)
				results_dict = results.json()
				if "feature_unique_ids" in results_dict:
					ids = results_dict["feature_unique_ids"]
				else:
					logging.error(f"Unable to retrieve field ID. Server returned {results_dict}")
					raise ValueError(f"Unable to retrieve field ID. Server returned {results_dict}")

				if len(ids) > 0:
					outputs[item] = ids[0]
				else:
					outputs[item] = None

				# save the returned value in our cache so we don't make another roundtrip if we run these
				# same values through in the future
				self.client.cache.cache_gdb_item(key=item, value=outputs[item])
				time.sleep(wait_time / 1000)
			else:
				outputs[item] = cached_value
				# no need to sleep when we check out own cache!

		if field:
			out_df = pandas.DataFrame({field: outputs.keys(), "openet_feature_id": outputs.values()})
			out_df.set_index(keys=field)
			return out_df
		else:
			return outputs

	def feature_ids_list(self, params=None):
		"""
			The base OpenET Method - sends the supplied params to metadata/openet/region_of_interest/feature_ids_list
			and returns the requests.Response object
		:param params:
		:return:
		"""
		endpoint = "metadata/openet/region_of_interest/feature_ids_list"
		if params is None:
			params = {}
		results = self.client.send_request(endpoint, method="post", **params)
		return results
