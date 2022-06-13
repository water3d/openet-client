"""
	For code related to the raster API primarily, but where we're not downloading raster data, and instead are retrieving JSON objects
"""

import logging
import copy
import datetime
import arrow

log = logging.getLogger(__name__)


class RasterTimeSeries(object):
	def __init__(self, raster_manager):
		self.raster_manager = raster_manager
		self.client = raster_manager.client

	def point_sample(self, longitude, latitude, start_date, end_date, interval="monthly", make_lookup=False, **params):
		"""
		A general function to retrieve the timeseries data from OpenET for a specific coordinate and date range. Uses the
		Raster API endpoint at `raster/timeseries/point <https://open-et.github.io/docs/build/html/ras_timeseries.html#raster-timeseries-point>`_
		to retrieve data. This function retrieves the full timeseries between the start and the end date, but convenience
		functions for retrieving a single value are also available as single_month_point_sample or single_day_point_sample

		This function accepts specified keyword arguments for the most common items to specify, but all other parameters to the endpoint
		can be provided as additional keyword arguments to this function. You do not need to include the keys for :code:`lon`
		or :code:`lat` -  if provided - they will be set (or overwritten) by the values
		provided in the keys longitude and latitude (note that this function uses the full words for longitude and
		latitude though)

		This function returns a list of dictionaries, as provided by the OpenET API. Each dictionary represents a single
		observation/value and will have a key :code:`time`, whose value indicates the timepoint of the observation. The
		dictionaries will also have a second key for the variable returned (defaults to :code:`et`) - see the OpenET
		API documentation for options.

		:param longitude: Longitude portion of the coordinate to retrieve data from, in decimal degrees. See `OpenET API documentation <https://open-et.github.io/docs/build/html/ras_timeseries.html#raster-timeseries-point>`_ for any additional specifications for this item (param :code:`lon` to the OpenET API)
		:param latitude: Latitude portion of the coordinate to retrieve data from, in decimal degrees
		:param start_date: The date to start the sample. Can be a Python standard library datetime.datetime object, an arrow.Arrow object or a string in "YYYY-MM-DD" format.
		:param end_date: The date to end the sample. Can be a Python standard library datetime.datetime object, an arrow.Arrow object or a string in "YYYY-MM-DD" format.
		:param interval: The time step to use in the timeseries. The OpenET API documentation doesn't specify valid values here, but :code:`monthly: and :code:`daily` are both known allowed values
						When using the :code:`monthly` timestep, the returned timeseries will use dates for the first of every month within the timeseries. See :code:`return` below
						for more details
		:param make_lookup: By default, the API returns a list of dictionaries that each have a key for :code:`time` and the variable requested (e.g. :code:`et`).
						To find specific values in that list you would need to search all objects. If, instead, you want to rely on a known structure
						of the :code:`time` values (e.g., that with monthly data, values will look like :code:`2018-01-01` then :code:`2018-02-01`), you canm
						set :code:`make_lookup` to true. This flag changes the return type of the function into a dictionary, where the keys are the dates
						and the values are the data in the variable field of the original dictionaries (e.g. the `et` value).

						For example, if their API returned the following data for a request, by default, this function would return a similar Python
						representation of the data:

						.. code-block:: python

							[
								{
									"time": "2018-01-01",
									"et": 30
								},
								{
									"time": "2018-02-01",
									"et": 52
								},
							]

						If :code:`make_lookup` is set to :code:`True` then this function will instead return the following dictionary

						.. code-block:: python

							{
								"2018-01-01": 30,
								"2018-02-01": 52,
							}
		:param params: Additional keyword arguments that the OpenET API allows can be provided to this function and
						they will be passed along to the API. Do not provide a keyword :code:`params` to this function.
						Instead, provide keyword arguments that match the OpenET API's parameter names
		:return: See :code:`make_lookup` above for return behavior, which is dependent on the value of :code:`make_lookup`.
					Either a list of dictionaries (loaded from JSON) by default, or a dictionary when :code:`make_lookup == True`
		"""
		send_params = copy.copy(params)
		send_params["start_date"] = self._date_to_string(start_date)
		send_params["end_date"] = self._date_to_string(end_date)
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
		The :code:`point_sample` function can return an arbitrary timeseries for a single point. This function instead
		returns only the ET value specified, or other variable if an argument is provided for the API. Optional additional
		parameters may sent to the same endpoint as	keyword arguments to this function - the same as other functions in this
		same timeseries module. Returns a single value for the day specified.

		If you need to retrieve multiple values, you may stay within your OpenET API quotas better with well-constructed
		use of the :code:`point_sample`, but for scattered or small numbers of samples, this function may be easier to use.

		:param longitude: Longitude portion of the coordinate to retrieve data from, in decimal degrees. See `OpenET API documentation <https://open-et.github.io/docs/build/html/ras_timeseries.html#raster-timeseries-point>`_ for any additional specifications for this item (param :code:`lon` to the OpenET API)
		:param latitude: Latitude portion of the coordinate to retrieve data from, in decimal degrees
		:param date: The day to obtain the sample for. The date may be a Python standard library datetime.datetime object, an arrow.Arrow object or a string in "YYYY-MM-DD" format.
		:param params: Additional keyword arguments that the OpenET API allows can be provided to this function and
						they will be passed along to the API. Do not provide a keyword :code:`params` to this function.
						Instead, provide keyword arguments that match the OpenET API's parameter names. Note that in this
						function, you should not provide keyword arguments for :code:`interval`, :code:`lat`,
						:code:`lon`, :code:`start_date`, or :code:`end_date`, as these values will be created automatically
						by this function.
		:return: A single value (may be a string, check the type before using) for the variable of interest, in the units returned by the API
					for the day specified. By default, the API will return values for ET, from the ensemble model,
					in metric units. To change these
					parameters, pass the appropriate additional keyword arguments for the API into this function.
		"""
		if "interval" in params:
			log.warning("Ignoring 'interval' parameter specified - function sets interval to a single day on its own")

		return self._single_point_sample(longitude=longitude, latitude=latitude, date=date, interval="daily")

	def single_month_point_sample(self, longitude, latitude, date, **params):
		"""
		The :code:`point_sample` function can return an arbitrary timeseries for a single point. This function instead
		returns only the ET value specified, or other variable if an argument is provided for the API. Optional additional
		parameters may sent to the same endpoint as	keyword arguments to this function - the same as other functions in this
		same timeseries module. Returns a single value for the month specified.

		If you need to retrieve multiple values, you may stay within your OpenET API quotas better with well-constructed
		use of the :code:`point_sample`, but for scattered or small numbers of samples, this function may be easier to use.

		:param longitude: Longitude portion of the coordinate to retrieve data from, in decimal degrees. See `OpenET API documentation <https://open-et.github.io/docs/build/html/ras_timeseries.html#raster-timeseries-point>`_ for any additional specifications for this item (param :code:`lon` to the OpenET API)
		:param latitude: Latitude portion of the coordinate to retrieve data from, in decimal degrees
		:param date: The month to obtain the sample for. The date may be a Python standard library datetime.datetime object, an arrow.Arrow object or a string in "YYYY-MM-DD" format.
		:param params: Additional keyword arguments that the OpenET API allows can be provided to this function and
						they will be passed along to the API. Do not provide a keyword :code:`params` to this function.
						Instead, provide keyword arguments that match the OpenET API's parameter names. Note that in this
						function, you should not provide keyword arguments for :code:`interval`, :code:`lat`,
						:code:`lon`, :code:`start_date`, or :code:`end_date`, as these values will be created automatically
						by this function.
		:return: A single value (may be a string, check the type before using) for the variable of interest, in the units returned by the API
					for the month specified. By default, the API will return values for ET, from the ensemble model,
					in metric units. To change these
					parameters, pass the appropriate additional keyword arguments for the API into this function.
		"""
		if "interval" in params:
			log.warning("Ignoring 'interval' parameter specified - function sets interval to a single month on its own")

		return self._single_point_sample(longitude=longitude, latitude=latitude, date=date, interval="monthly")

	def _single_point_sample(self, longitude, latitude, date, interval, **params):

		dates = self._interval_date(start=date, interval=interval, add=1)

		send_params = copy.copy(params)
		if "variable" not in params:
			params["variable"] = "et"  # this is the default, but we'll be explicit to avoid surprises since we'll use this below
		else:
			params["variable"] = params["variable"].lower()  # just ensure it's lowercase so we make sure have consistent values

		send_params["interval"] = interval
		send_params["lon"] = longitude
		send_params["lat"] = latitude
		send_params["start_date"] = dates['start']
		send_params["end_date"] = dates['end']

		result = self._raw_point_sample(**send_params)
		return result[0][params["variable"]]  # since we'll just be asking for one value in the timeseries, get the first item in the list, and return the value for the variable we requested

	def _date_to_string(self, date):
		"""
			Handles date parsing to give support for arrow and datetime objects. If it's not one of those, it's assumed to be a string in YYYY-MM-DD format
		"""
		if isinstance(date, arrow.arrow.Arrow):
			date = date.datetime
		if isinstance(date, datetime.datetime):
			date_value = date.strftime("%Y-%m-%d")
		else:
			date_value = date

		return date_value

	def _interval_date(self, start, interval, add=1):
		start_date = start
		if isinstance(start, datetime.datetime):
			start_date = arrow.Arrow.fromdatetime(start)
		elif type(start) is str:
			# assume start is in YYYY-MM-DD format
			parts = start.split("-")
			start_date = arrow.Arrow(year=int(parts[0]), month=int(parts[1]), day=int(parts[2]))

		end_date = start_date
		if interval == "daily":
			end_date = start_date.shift(days=add)
		elif interval == "monthly":
			end_date = start_date.shift(months=add)
		elif interval == "yearly":
			end_date = start_date.shift(years=add)

		return {'start': start_date.strftime("%Y-%m-%d"), 'end': end_date.strftime("%Y-%m-%d")}

	def _raw_point_sample(self, **params):
		return self.client.send_request('raster/timeseries/point', method="get", disable_encoding=False, **params).json()