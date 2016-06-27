import random
import time
from datetime import datetime
from enum import Enum

import googlemaps
from googlemaps import convert
from tornado import gen, httpclient, escape


class ApiErrorCode(Enum):
    OK = 200
    NOT_FOUND = 404
    ZERO_RESULTS = 400
    MAX_WAYPOINTS_EXCEEDED = 400
    INVALID_REQUEST = 400
    OVER_QUERY_LIMIT = 429
    REQUEST_DENIED = 403
    UNKNOWN_ERROR = 500


class AsyncClient(googlemaps.Client):
    """
    Asynchronous implementation of googlemaps python client
    """
    def __init__(self, *args, **kwargs):
        super(AsyncClient, self).__init__(*args, **kwargs)
        self.http_client = httpclient.AsyncHTTPClient()
        self.requests_kwargs = kwargs.get('requests_kwargs') or {}
        self.requests_kwargs.update({
            "user_agent": googlemaps.client._USER_AGENT,
            "request_timeout": self.timeout,
            "validate_cert": True,  # NOTE(cbro): verify SSL certs.
        })

    async def _get(self, url, params, first_request_time=None, retry_counter=0,
                   base_url=googlemaps.client._DEFAULT_BASE_URL,
                   accepts_clientid=True, extract_body=None,
                   requests_kwargs=None):
        """Performs _asynchronous_ HTTP GET request with credentials,
        returning the body as JSON.
        :param url: URL path for the request. Should begin with a slash.
        :type url: string
        :param params: HTTP GET parameters.
        :type params: dict or list of key/value tuples
        :param first_request_time: The time of the first request (None if no
            retries have occurred).
        :type first_request_time: datetime.datetime
        :param retry_counter: The number of this retry, or zero for first attempt.
        :type retry_counter: int
        :param base_url: The base URL for the request. Defaults to the Maps API
            server. Should not have a trailing slash.
        :type base_url: string
        :param accepts_clientid: Whether this call supports the client/signature
            params. Some APIs require API keys (e.g. Roads).
        :type accepts_clientid: bool
        :param extract_body: A function that extracts the body from the request.
            If the request was not successful, the function should raise a
            googlemaps.HTTPError or googlemaps.ApiError as appropriate.
        :type extract_body: function
        :param requests_kwargs: Same extra keywords arg for requests as per
            __init__, but provided here to allow overriding internally on a
            per-request basis.
        :type requests_kwargs: dict
        :raises ApiError: when the API returns an error.
        :raises Timeout: if the request timed out.
        :raises TransportError: when something went wrong while trying to
            exceute a request.
        """
        if not first_request_time:
            first_request_time = datetime.now()

        authed_url = self._generate_auth_url(url, params, accepts_clientid)
        # Default to the client-level self.requests_kwargs, with method-level
        # requests_kwargs arg overriding.
        requests_kwargs = dict(self.requests_kwargs, **(requests_kwargs or {}))

        while True:
            elapsed = datetime.now() - first_request_time
            if elapsed > self.retry_timeout:
                raise googlemaps.exceptions.Timeout()

            if retry_counter > 0:
                # 0.5 * (1.5 ^ i) is an increased sleep time of 1.5x per iteration,
                # starting at 0.5s when retry_counter=0. The first retry will occur
                # at 1, so subtract that first.
                delay_seconds = 0.5 * 1.5 ** (retry_counter - 1)

                # Jitter this value by 50% and pause.
                await gen.sleep(delay_seconds * (random.random() + 0.5))

            try:
                resp = await self.http_client.fetch(base_url + authed_url,
                                                    **requests_kwargs)
            except httpclient.HTTPError as e:
                if e.code == 599:
                    raise googlemaps.exceptions.Timeout()
                else:
                    raise googlemaps.exceptions.TransportError(e)

            if resp.code in googlemaps.client._RETRIABLE_STATUSES:
                # Retry request.
                retry_counter += 1
                continue

            # Check if the time of the nth previous query (where n is queries_per_second)
            # is under a second ago - if so, sleep for the difference.
            if self.sent_times and len(
                    self.sent_times) == self.queries_per_second:
                elapsed_since_earliest = time.time() - self.sent_times[0]
                if elapsed_since_earliest < 1:
                    await gen.sleep(1 - elapsed_since_earliest)

            try:
                if extract_body:
                    result = extract_body(resp)
                else:
                    result = self._get_body(resp)
                self.sent_times.append(time.time())
                return result
            except googlemaps.exceptions._RetriableRequest:
                # Retry request.
                retry_counter += 1

    def _get_body(self, resp):
        if resp.code != 200:
            raise googlemaps.exceptions.HTTPError(resp.code)

        body = escape.json_decode(resp.body)

        api_status = body["status"]
        if api_status == "OK" or api_status == "ZERO_RESULTS":
            return body

        if api_status == "OVER_QUERY_LIMIT":
            raise googlemaps.exceptions._RetriableRequest()

        if "error_message" in body:
            raise googlemaps.exceptions.ApiError(api_status,
                                                 body["error_message"])
        else:
            raise googlemaps.exceptions.ApiError(api_status)

    async def directions(self, origin, destination,
                         mode=None, waypoints=None, alternatives=False,
                         avoid=None,
                         language=None, units=None, region=None,
                         departure_time=None,
                         arrival_time=None, optimize_waypoints=False,
                         transit_mode=None,
                         transit_routing_preference=None, traffic_model=None):
        """Get directions between an origin point and a destination point.

        :param origin: The address or latitude/longitude value from which you wish
            to calculate directions.
        :type origin: string, dict, list, or tuple

        :param destination: The address or latitude/longitude value from which
            you wish to calculate directions.
        :type destination: string, dict, list, or tuple

        :param mode: Specifies the mode of transport to use when calculating
            directions. One of "driving", "walking", "bicycling" or "transit"
        :type mode: string

        :param waypoints: Specifies an array of waypoints. Waypoints alter a
            route by routing it through the specified location(s).
        :type waypoints: a single location, or a list of locations, where a
            location is a string, dict, list, or tuple

        :param alternatives: If True, more than one route may be returned in the
            response.
        :type alternatives: bool

        :param avoid: Indicates that the calculated route(s) should avoid the
            indicated features.
        :type avoid: list or string

        :param language: The language in which to return results.
        :type language: string

        :param units: Specifies the unit system to use when displaying results.
            "metric" or "imperial"
        :type units: string

        :param region: The region code, specified as a ccTLD ("top-level domain"
            two-character value.
        :type region: string

        :param departure_time: Specifies the desired time of departure.
        :type departure_time: int or datetime.datetime

        :param arrival_time: Specifies the desired time of arrival for transit
            directions. Note: you can't specify both departure_time and
            arrival_time.
        :type arrival_time: int or datetime.datetime

        :param optimize_waypoints: Optimize the provided route by rearranging the
            waypoints in a more efficient order.
        :type optimize_waypoints: bool

        :param transit_mode: Specifies one or more preferred modes of transit.
            This parameter may only be specified for requests where the mode is
            transit. Valid values are "bus", "subway", "train", "tram", "rail".
            "rail" is equivalent to ["train", "tram", "subway"].
        :type transit_mode: string or list of strings

        :param transit_routing_preference: Specifies preferences for transit
            requests. Valid values are "less_walking" or "fewer_transfers"
        :type transit_routing_preference: string

        :param traffic_model: Specifies the predictive travel time model to use.
            Valid values are "best_guess" or "optimistic" or "pessimistic".
            The traffic_model parameter may only be specified for requests where
            the travel mode is driving, and where the request includes a
            departure_time.
        :type units: string

        :rtype: list of routes
        """

        params = {
            "origin": convert.latlng(origin),
            "destination": convert.latlng(destination)
        }

        if mode:
            # NOTE(broady): the mode parameter is not validated by the Maps API
            # server. Check here to prevent silent failures.
            if mode not in ["driving", "walking", "bicycling", "transit"]:
                raise ValueError("Invalid travel mode.")
            params["mode"] = mode

        if waypoints:
            waypoints = convert.location_list(waypoints)
            if optimize_waypoints:
                waypoints = "optimize:true|" + waypoints
            params["waypoints"] = waypoints

        if alternatives:
            params["alternatives"] = "true"

        if avoid:
            params["avoid"] = convert.join_list("|", avoid)

        if language:
            params["language"] = language

        if units:
            params["units"] = units

        if region:
            params["region"] = region

        if departure_time:
            params["departure_time"] = convert.time(departure_time)

        if arrival_time:
            params["arrival_time"] = convert.time(arrival_time)

        if departure_time and arrival_time:
            raise ValueError("Should not specify both departure_time and"
                             "arrival_time.")

        if transit_mode:
            params["transit_mode"] = convert.join_list("|", transit_mode)

        if transit_routing_preference:
            params["transit_routing_preference"] = transit_routing_preference

        if traffic_model:
            params["traffic_model"] = traffic_model

        result = await self._get("/maps/api/directions/json", params)
        return result["routes"]
