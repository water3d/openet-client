import logging

import requests

logging.basicConfig()

from .raster import RasterManager
from .exceptions import AuthenticationError


class OpenETClient(object):
    token = None
    _base_url = "https://openet.dri.edu/"
    _validate_ssl = False

    def __init__(self, token=None):
        self.token = token
        self.raster = RasterManager(client=self)

    def _check_token(self):
        if self.token is None:
            raise AuthenticationError("Token missing/undefined - you must set the value of your token before proceeding")

    def send_request(self, endpoint, method="get", **kwargs):
        self._check_token()

        requester = getattr(requests, method)
        send_kwargs = {}
        if method == "get":
            send_kwargs["params"] = kwargs
            send_kwargs["data"] = None
        elif method == "post":
            send_kwargs["data"] = kwargs
            send_kwargs["params"] = None

        url = self._base_url + endpoint
        logging.info(f"Connecting to {url}")
        logging.info(f"Sending params {kwargs}")
        logging.info(f"Sending token in header{self.token}")

        extra_kwargs = {}
        if self._validate_ssl != True:
            extra_kwargs['verify'] = False

        result = requester(url, headers={"Authorization": self.token}, params=send_kwargs["params"], data=send_kwargs["data"], **extra_kwargs)
        return result
