import uuid
import tempfile
import shutil
import time
import functools
import logging

import requests

from .exceptions import BadRequestError, FileRetrievalError

STATUS_NONE = 0
STATUS_SUBMITTED = 1
STATUS_WAITING = 2
STATUS_AVAILABLE = 3
STATUS_DOWNLOADED = 4
STATUS_FAILED_OPENET = 5
STATUS_FAILED_CLIENT = 6


class Raster(object):
    def __init__(self, request_result):
        self.status = STATUS_NONE
        self.params = {}
        self.remote_url = None
        self.local_file = None
        self.uuid = uuid.uuid4()

        self._request_result = request_result
        self._set_values()

    def _set_values(self):
        self.remote_url = self._request_result['bucket_url'][0]
        if "Queued" in self._request_result['status']:
            self.status = STATUS_SUBMITTED

    def download_file(self, retry_interval=20, max_wait=600):
        # adapted from https://stackoverflow.com/a/39217788/587938
        local_filename = self.remote_url.split('/')[-1]
        local_file_path = tempfile.mktemp(local_filename)
        # NOTE the stream=True parameter below
        wait_time = 0
        while self.status == STATUS_AVAILABLE and wait_time < max_wait:  # keep trying - it can take time for the permissions to work out
            with requests.get(self.remote_url, stream=True) as r:
                r.raw.read = functools.partial(r.raw.read, decode_content=True)  # we need this to stream gzipped data correctly and decode it
                if r.status_code == 200 and r.headers["content-type"] == "image/tiff":  # if it's not a tiff, then we might be getting a text error back
                    with open(local_file_path, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)

                    self.local_file = local_file_path
                    self.status = STATUS_DOWNLOADED
                    logging.info(f"Retrieved {self.local_file}")

                if r.status_code not in (200, 403):
                    # we skip 403 as well, because we're going to temporarily get 403s until permissions are set regardless.
                    raise FileRetrievalError(f"Couldn't retrieve {self.remote_url}. Received HTTP Status code {r.status_code}.")

                if not self.status == STATUS_DOWNLOADED:
                    logging.info(f"not yet available - trying again in {retry_interval}")
                    time.sleep(retry_interval)
                    wait_time += retry_interval

class RasterManager(object):
    client = None

    def __init__(self, client, wait_time=30):
        self.client = client
        self.registry = {}
        self._wait_interval = wait_time

    def export(self, params=None, synchronous=False, public=True):
        endpoint = "raster/export"
        params = {} if params is None else params

        if "filename_suffix" in params and not "public" in params["filename_suffix"] and public is True:
            params["filename_suffix"] += "_public"
        elif "filename_suffix" not in params and public is True:
            params["filename_suffix"] = "_public"

        result = self.client.send_request(endpoint, **params)

        if result.status_code not in (200, 201, 301):
            raise BadRequestError(f"OpenET API returned status code {result.status_code} with reason {result.reason} and message {result.text}")

        raster = Raster(result.json())
        self.registry[raster.uuid] = raster

        if synchronous:
            self.wait_for_rasters(raster.uuid)

    @property
    def queued_rasters(self):
        """
            Which rasters are we still waiting for?
        :return:
        """

        return [raster for raster in self.registry.values() if raster.status < STATUS_DOWNLOADED ]

    @property
    def available_rasters(self):
        return [raster for raster in self.registry.values() if raster.status == STATUS_AVAILABLE]

    @property
    def downloaded_raster_paths(self):
        return [raster.local_file for raster in self.registry.values() if raster.status == STATUS_DOWNLOADED]

    def download_available_rasters(self):
        rasters = self.available_rasters

        for raster in rasters:
            raster.download_file()

    def wait_for_rasters(self, uuid=None, max_time=86400):
        """

        :param uuid:
        :param max_time: Maximum time in seconds to wait for all rasters to complete - defaults to 86400 (a day)
        :return:
        """

        endpoint = "raster/export/all_files"

        if uuid is None:
            rasters = self.queued_rasters
        else:
            rasters = [self.registry[uuid],]

        wait_time = 0
        while len(rasters) > 0 and wait_time < max_time:
            time.sleep(self._wait_interval)
            wait_time += self._wait_interval  # we'll have some error in this approach because we won't account for the time we spend processing things. We could just check how long it's been since we started waiting too

            results = self.client.send_request(endpoint)

            for raster in rasters:
                if raster.remote_url in results.json()["rasters"]:
                    raster.status = STATUS_AVAILABLE

            self.download_available_rasters()
            rasters = [raster for raster in rasters if raster.status < STATUS_AVAILABLE]

