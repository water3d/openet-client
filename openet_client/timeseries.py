"""
	For code related to the raster API primarily, but where we're not downloading raster data, and instead are retrieving JSON objects
"""

import logging
import copy
import datetime
try:
	import arrow
	ARROW_SUPPORT = True
except ImportError:
	ARROW_SUPPORT = False

log = logging.getLogger(__name__)


class RasterTimeSeries(object):
	def __init__(self, raster_manager):
		self.raster_manager = raster_manager
		self.client = raster_manager.client

	def point_sample(self, longitude, latitude, start_date, end_date, interval="monthly", make_lookup=False, **params):
		"""
		Retrieve the timeseries data from OpenET for a specific coordinate and date range. Uses the
		Raster API endpoint at :link:`raster/timeseries/point <https://open-et.github.io/docs/build/html/ras_timeseries.html#raster-timeseries-point>`_
		to retrieve data.

		This function accepts specified keyword arguments for the most common items to specify, but all other parameters to the endpoint
		can be provided as additional keyword arguments to this function. You do not need to include the keys for :code:`lon`
		 or :code:`lat` -  if provided - they will be set (or overwritten) by the values
		provided in the keys longitude and latitude (note that this function uses the full words for longitude and
		latitude though)

		This function returns a list of dictionaries, as provided by the OpenET API. Each dictionary represents a single
		observation/value and will have a key :code:`time`, whose value indicates the timepoint of the observation. The
		dictionaries will also have a second key for the variable returned (defaults to :code:`et`) - see the OpenET
		API documentation for options.

		:param longitude:
		:param latitude:
		:param start_date:
		:param end_date:
		:param interval:
		:param make_lookup:
		:param params:
		:return:
		"""
		send_params = copy.copy(params)
		send_params["start_date"] = self._parse_date(start_date)
		send_params["end_date"] = self._parse_date(end_date)
		send_params["lon"] = longitude
		send_params["lat"] = latitude
		send_params["interval"] = interval

		if "variable" not in send_params:
			send_params["variable"] = "et"
		else:
			send_params["variable"] = send_params["variable"].lower()

		results = self._raw_point_sample(params=send_params)

		if make_lookup:
			results = [{r["time"]: r[send_params["variable"]]} for r in results]

	def single_day_point_sample(self, longitude, latitude, date, **params):
		"""

		:param longitude:
		:param latitude:
		:param date:
		:param params:
		:return:
		"""
		if "interval" in params:
			log.warning("Ignoring 'interval' parameter specified - function sets interval to a single day on its own")

		return self._single_point_sample(longitude=longitude, latitude=latitude, date=date, interval="daily")

	def single_month_point_sample(self, longitude, latitude, date, **params):
		"""

		The :code:`point_sample` function can return an arbitrary timeseries for a single point. This function instead
		returns only the ET value specified (with optional additional parameters sent to the same endpoint as additional
		keyword arguments to this function). Returns a single value for the month specified (either as a string date
		in the form "YYYY-MM-DD" or as a datetime.datetime object or an arrow object().

		The behavior for this is currently funky - don't specify the days in your :code:`date` value as anything ending
		in a 9 to avoid the bad behavior. This will be fixed in a future release.

		:param longitude:
		:param latitude:
		:param date:
		:param params:
		:return:
		"""
		if "interval" in params:
			log.warning("Ignoring 'interval' parameter specified - function sets interval to a single month on its own")

		return self._single_point_sample(longitude=longitude, latitude=latitude, date=date, interval="monthly")

	def _single_point_sample(self, longitude, latitude, date, interval, **params):

		date_value = self._parse_date(date)

		send_params = copy.copy(params)
		if "variable" not in params:
			params["variable"] = "et"  # this is the default, but we'll be explicit to avoid surprises since we'll use this below
		else:
			params["variable"] = params["variable"].lower()  # just ensure it's lowercase so we make sure have consistent values

		send_params["interval"] = interval
		send_params["lon"] = longitude
		send_params["lat"] = latitude
		send_params["start_date"] = date_value

		# get the end value - this is a string by this point, so we'll do something silly and strip off the last character, make it a number, add one, then re-add it. This is obviously not valid in all kinds of situations. We'd be better off making a datetime (or arrow) object out of it, then adding to that and re-stringifying it. Which seems a bit silly. But this needs to change and will break if, e.g. someone provides a date of day 19 of a month - weird ways
		end_value = copy.copy(date_value)
		new_ending = str(int(end_value[-1]) + 1)
		end_value = end_value[:-1] + new_ending
		send_params["end_date"] = end_value

		result = self._raw_point_sample(**send_params)
		return result[0][params["variable"]]  # since we'll just be asking for one value in the timeseries, get the first item in the list, and return the value for the variable we requested

	def _parse_date(self, date):
		"""
			Handles date parsing to give support for arrow and datetime objects. If it's not one of those, it's assumed to be a string in YYYY-MM-DD format
		"""
		if ARROW_SUPPORT and isinstance(date, arrow.arrow.Arrow):
			date = date.datetime
		if isinstance(date, datetime.datetime):
			date_value = date.strftime("%Y-%m-%d")
		else:
			date_value = date

		return date_value

	def _raw_point_sample(self, **params):
		return self.client.send_request('raster/timeseries/point', method="get", disable_encoding=False, **params).json()