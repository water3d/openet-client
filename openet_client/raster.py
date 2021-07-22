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
    """
        Internal object for managing raster exports - tracks current status, the remote URL and the local file path once
        it exists.
    """
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
        """
            Attempts to download a raster, assuming it's ready for download.
            Will make multiple attempts over a few minutes because sometimes it takes a while for the permissions
            to propagate, so the first few responses may give a 403 error. We then have a timeout (max_wait) where
            if we exceed that value, we exit anyway without downloading.

            Downloads the file to a tempfile path - the user may move the file after that if they
            wish.
        :param retry_interval: time in seconds between repeated attempts
        :param max_wait: How long, in seconds should we wait for the correct permissions before stopping attempts to download.
        :return:
        """
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
    """
        The manager that becomes the .raster attribute on the OpenETClient object.
        Handles submitting raster export requests and polling for completed exports.

        As constructed, could slow down if it handles many thousands of raster exports, or
        if the all_files OpenET endpoint displays lots of files as options.

        Generally speaking, you won't create this object yourself, but you can set
        client.raster.wait_interval to the length of time, in seconds, that the manager
        should wait between polling the all_files endpoint for new exports when waiting for new
        rasters.
    """

    client = None
    wait_interval = 30

    def __init__(self, client):
        self.client = client
        self.registry = {}

    def export(self, params=None, synchronous=False, public=True):
        """
            Handles the raster/export endpoint for OpenET.
        :param params: A dictionary of arguments with keys matching the raster/export endpoints parameters
                        and values matching the requirements for the values of those keys
        :param synchronous: Whether or not to wait for the raster to export and be downloaded before
                            exiting this function and proceeding
        :param public:  Whether or not to make the raster public - at this point, keeping this as True is
                        required for all the features of this package to work, but if you just want to use the
                        package to submit a bunch of raster jobs, but not to *download* those rasters, then
                        you may set this to False.
        :return: Raster object - when synchronous, the local_file attribute will
                        have the path to the downloaded raster on disk - otherwise it
                        will have the status of the raster
        """
        endpoint = "raster/export"
        params = {} if params is None else params

        if "filename_suffix" in params and not "public" in params["filename_suffix"] and public is True:
            params["filename_suffix"] += "_public"
        elif "filename_suffix" not in params and public is True:
            params["filename_suffix"] = "_public"

        # consider adding a geometry check here, such as
        #
        # if hasattr(params["geometry"], "transform") and hasattr(params["geometry"], "coords"):
        #   params["geometry"] = str(p.boundary.transform(4326, clone=True).coords).replace("(", "").replace(")", "").replace(" ", "")[:-1]
        #
        # it checks if we have the ability to reproject the geometry data passed in and if we can get a coordinate string from it,
        # such as from OGR and GEOS objects in GeoDjango. If it has those abilities, then it attempts to reproject, get the coordinates, and then
        # stringifies them and removes parens, spaces, and the trailing comma.

        result = self.client.send_request(endpoint, **params)

        if result.status_code not in (200, 201, 301):
            raise BadRequestError(f"OpenET API returned status code {result.status_code} with reason {result.reason} and message {result.text}")

        raster = Raster(result.json())
        self.registry[raster.uuid] = raster

        if synchronous:
            self.wait_for_rasters(raster.uuid)

        return raster

    @property
    def queued_rasters(self):
        """
            Which rasters are we still waiting for?
        :return:
        """

        return [raster for raster in self.registry.values() if raster.status < STATUS_DOWNLOADED ]

    @property
    def available_rasters(self):
        """
            Which rasters have we marked as ready to download, but haven't yet been retrieved?
        :return:
        """
        return [raster for raster in self.registry.values() if raster.status == STATUS_AVAILABLE]

    @property
    def downloaded_raster_paths(self):
        return [raster.local_file for raster in self.registry.values() if raster.status == STATUS_DOWNLOADED]

    def download_available_rasters(self):
        """
            Attempts to download all available rasters individually
        :return:
        """
        rasters = self.available_rasters

        for raster in rasters:
            raster.download_file()

    def wait_for_rasters(self, uuid=None, max_time=86400):
        """
            When we want to just wait until the rasters are ready, we call this method, which polls
            the all_files endpoint at set intervals and checks which rasters are done.

            Then updates the statuses on individual rasters and calls the download functions
            for the individual rasters and time some are ready to download, but won't exit until
            all rasters are available and have had at least one download attempt.
        :param uuid:
        :param max_time: Maximum time in seconds to wait for all rasters to complete - defaults to 86400 (a day)
        :return:
        """

        if uuid is None:
            rasters = self.queued_rasters
        else:
            rasters = [self.registry[uuid],]

        wait_time = 0
        while len(rasters) > 0 and wait_time < max_time:
            time.sleep(self.wait_interval)
            wait_time += self.wait_interval  # we'll have some error in this approach because we won't account for the time we spend processing things. We could just check how long it's been since we started waiting too

            self.check_statuses(rasters)

            self.download_available_rasters()
            rasters = [raster for raster in rasters if raster.status < STATUS_AVAILABLE]

    def check_statuses(self, rasters=None):
        """
            Updates the status information on each raster only - does not attempt to download them.
        :param rasters: the list of rasters to update the status of - if not provided, defaults to all rasters that
                        are queued and not downloaded
        :return: None
        """
        endpoint = "raster/export/all_files"

        if rasters is None:
            rasters = self.queued_rasters

        results = self.client.send_request(endpoint)
        for raster in rasters:
            if raster.remote_url in results.json()["rasters"]:
                raster.status = STATUS_AVAILABLE

