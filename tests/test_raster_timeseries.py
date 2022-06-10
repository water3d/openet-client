import pytest
import os

import openet_client

# https://openet.dri.edu/raster/timeseries/point?start_date=2016-01-01&end_date=2016-12-31&lat=42.806546&lon=-114.601811&model=ensemble&ref_et_source=gridmet&units=metric&variable=et&output_output_date_format=standard&output_file_format=json
TRUE_2016_ET_TS_ENSEMBLE = [
		{
			"time": "2016-01-01",
			"et": 16
		},
		{
			"time": "2016-02-01",
			"et": 32
		},
		{
			"time": "2016-03-01",
			"et": 57
		},
		{
			"time": "2016-04-01",
			"et": 23
		},
		{
			"time": "2016-05-01",
			"et": 64
		},
		{
			"time": "2016-06-01",
			"et": 166
		},
		{
			"time": "2016-07-01",
			"et": 217
		},
		{
			"time": "2016-08-01",
			"et": 162
		},
		{
			"time": "2016-09-01",
			"et": 45
		},
		{
			"time": "2016-10-01",
			"et": 32
		},
		{
			"time": "2016-11-01",
			"et": 16
		},
		{
			"time": "2016-12-01",
			"et": 12
		}
	]


def test_single_point_sample_monthly_september():
	client = openet_client.OpenETClient()
	client.token = os.environ["OPENET_TOKEN"]

	september_result = client.raster.timeseries.single_month_point_sample(longitude=-114.601811, latitude=42.806546,
													   date="2016-09-01", params={"model": "ensemble", "et_ref_source":"gridmet"})

	assert september_result == TRUE_2016_ET_TS_ENSEMBLE[8]["et"]
