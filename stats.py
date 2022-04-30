import math

from geopy.distance import geodesic


DELTA_HEADING = 'delta_heading'
DEFAULT_DELTA_STATS = [DELTA_HEADING]

INSTANT_DISTANCE_TO_CENTER = 'instant_distance_to_center'
INSTANT_BBOX_LATLON_PAN = 'instant_bbox_latlon_pan'
INSTANT_FLIGHT_PROGRESS = 'instant_flight_progress'
FLIGHT_PROGRESS_MAX_DEPARTURE_PERCENT = 10
FLIGHT_PROGRESS_MIN_ARRIVAL_PERCENT = 90
FLIGHT_PROGRESS_DEPARTING = 'departing'
FLIGHT_PROGRESS_MIDFLIGHT = 'midflight'
FLIGHT_PROGRESS_ARRIVING = 'arriving'
DEFAULT_INSTANT_STATS = [
    INSTANT_DISTANCE_TO_CENTER,
    INSTANT_BBOX_LATLON_PAN,
    INSTANT_FLIGHT_PROGRESS
]
FR_API_DEFAULT_TEXT = 'N/A'
DEFAULT_FLIGHT_PROGRESS = FLIGHT_PROGRESS_MIDFLIGHT
DEFAULT_FLIGHT_PROGRESS_PERCENT = 50


class StatsController(object):

    def __init__(self, bbox, airport_cache,
                 delta_stats=DEFAULT_DELTA_STATS,
                 instant_stats=DEFAULT_INSTANT_STATS):
        self.bbox = bbox
        self.airport_cache = airport_cache
        self.delta_stats = delta_stats
        self.delta_stats_calculator = DeltaStatsCalculator(delta_stats)
        self.instant_stats_calculator = InstantStatsCalculator(
            bbox, airport_cache, instant_stats)

    def add_delta_stats(self, prev_flights, next_flights):
        prev_ids = prev_flights.get_flight_ids()
        next_ids = next_flights.get_flight_ids()

        repeated_ids = [i for i in next_ids if i in prev_ids]
        for i in repeated_ids:
            self.delta_stats_calculator.calculate_delta_stats(
                prev_flights.flights[i],
                next_flights.flights[i]
            )

        new_ids = [i for i in next_ids if i not in prev_ids]
        for i in new_ids:
            self.delta_stats_calculator.init_delta_stats(
                next_flights.flights[i]
            )

    def add_instant_stats(self, flights):
        for flight in flights.get_ordered():
            self.instant_stats_calculator.calculate_instant_stats(flight)



class DeltaStatsCalculator(object):

    def __init__(self, airport_cache, stats=DEFAULT_DELTA_STATS):
        self.airport_cache = airport_cache
        self.stats = stats

    def calculate_delta_stats(self, prev_flight, next_flight):
        if DELTA_HEADING in self.stats:
            next_flight.delta_heading = next_flight.heading - \
                prev_flight.heading

    def init_delta_stats(self, flight):
        if DELTA_HEADING in self.stats:
            flight.delta_heading = 0


class InstantStatsCalculator(object):

    def __init__(self, bbox, airport_cache, stats=DEFAULT_INSTANT_STATS):
        self.bbox = bbox
        self.airport_cache = airport_cache
        self.stats = stats

    def calculate_instant_stats(self, flight):
        if INSTANT_DISTANCE_TO_CENTER in self.stats:
            self.calculate_distance_to_center(flight)
        if INSTANT_BBOX_LATLON_PAN in self.stats:
            self.calculate_bbox_latlon_pan(flight)
        if INSTANT_FLIGHT_PROGRESS in self.stats:
            self.calculate_flight_progress(flight)

    def calculate_distance_to_center(self, flight):
        flight.distance_to_center_mi = geodesic(
            (flight.latitude, flight.longitude),
            (self.bbox.center.latitude, self.bbox.center.longitude)
        ).mi
        max_d = math.sqrt(2) * self.bbox.margin_mi
        flight.proximity = 1 - self.ratio(
            flight.distance_to_center_mi,
            max_d,
            0,
            1
        )

    def calculate_bbox_latlon_pan(self, flight):
        flight.bbox_pan_lat = self.ratio(
            (flight.latitude - self.bbox.center.latitude),
            self.bbox.margin_latlong,
            -1,
            1
        )
        flight.bbox_pan_lon = self.ratio(
            (flight.longitude - self.bbox.center.longitude),
            self.bbox.margin_latlong,
            -1,
            1
        )

    def calculate_flight_progress(self, flight):
        origin = self.airport_cache.get_by_iata(flight.origin_airport_iata)
        dest = self.airport_cache.get_by_iata(flight.destination_airport_iata)
        if not origin or not dest:
            flight.progress = DEFAULT_FLIGHT_PROGRESS
            flight.progress_percent = DEFAULT_FLIGHT_PROGRESS_PERCENT
            return
        origin_to_dest_mi = geodesic((origin['lat'], origin['lon']),
                                  (dest['lat'], dest['lon'])).mi
        flight_to_dest_mi = geodesic((flight.latitude, flight.longitude),
                                  (dest['lat'], dest['lon'])).mi
        flight.origin_to_dest_mi = origin_to_dest_mi
        flight.flight_to_dest_mi = flight_to_dest_mi
        distance_ratio = self.ratio(
            flight_to_dest_mi,
            origin_to_dest_mi,
            0,
            1
        )
        flight.progress_percent = 100 * (1 - distance_ratio)
        if flight.progress_percent < FLIGHT_PROGRESS_MAX_DEPARTURE_PERCENT:
            flight.progress = FLIGHT_PROGRESS_DEPARTING
        elif flight.progress_percent < FLIGHT_PROGRESS_MIN_ARRIVAL_PERCENT:
            flight.progress = FLIGHT_PROGRESS_MIDFLIGHT
        else:
            flight.progress = FLIGHT_PROGRESS_ARRIVING

    def ratio(self, numerator, denominator, min_value, max_value):
        ratio = numerator / denominator
        if ratio < min_value:
            ratio = min_value
        elif ratio > max_value:
            ratio = max_value
        return ratio
