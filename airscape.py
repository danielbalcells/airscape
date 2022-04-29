import time
import random

from FlightRadar24.api import FlightRadar24API

import util
import location as loc


DEFAULT_REFRESH_TIME = 5
FLIGHT_CHOICE_RANDOM = 'random'
DEFAULT_ONLY_AIRBORNE = True
AIRBORNE_ALTITUDE_THRESHOLD = 10
DEFAULT_FLIGHT_CHOICE = FLIGHT_CHOICE_RANDOM


class AirscapeController(object):

    def __init__(self, bbox_center_query, margin_mi=30,
                 refresh_time=DEFAULT_REFRESH_TIME, flight_limit=8):
        self.bbox = loc.BoundingBox(bbox_center_query, margin_mi)
        self.fr_api = FlightRadar24API()
        self.refresh_time = refresh_time
        self.running = False
        self.tracked_flights = TrackedFlights(flight_limit)

    def get_flights(self):
        bbox_str = self.bbox.get_coordinate_string(order=loc.ORDER_FR_API)
        flights = self.fr_api.get_flights(bounds=bbox_str)
        return flights

    def run(self):
        self.running = True
        while self.running:
            start_time = time.time()
            all_flights = self.get_flights()
            self.tracked_flights.update_or_add(all_flights)
            print(util.timestamp())
            print(self.tracked_flights)
            time_elapsed = time.time()-start_time
            sleep_time = max(0, self.refresh_time-time_elapsed)
            time.sleep(sleep_time)


class TrackedFlights(object):

    def __init__(self, flight_limit):
        self.flight_limit = flight_limit
        self.slots = list(range(flight_limit))
        self.flights = {}
        self.slot_assignments = {}

    def __str__(self):
        output_string = ''
        for index, flight in enumerate(self.sort_by_slot()):
            output_string += f'{index}: {flight}\n'
        return output_string

    def update_or_add(self, next_flights):
        next_flights = self.filter(next_flights)
        self.update(next_flights)
        while (
                len(self.flights) < self.flight_limit
                and len(self.flights) < len(next_flights)
        ):
            self.add_from_list(next_flights)

    def update(self, next_flights):
        next_flights_tracked = [f for f in next_flights if f.id in
                                self.flights.keys()]
        new_flight_slots = {}
        for f in next_flights_tracked:
            self.flights[f.id] = f
            new_flight_slots[f.id] = self.slot_assignments[f.id]
        self.slot_assignments = new_flight_slots

    def add_from_list(self, next_flights, flight_choice=DEFAULT_FLIGHT_CHOICE):
        next_flights_not_tracked = [f for f in next_flights if f.id not in
                                    self.flights.keys()]
        if flight_choice == FLIGHT_CHOICE_RANDOM:
            flight = self.get_random_flight(next_flights_not_tracked)
        if not flight:
            return
        slot = self.get_available_slot()
        self.slot_assignments[flight.id] = slot
        self.flights[flight.id] = flight

    def filter(self, flights, only_airborne=DEFAULT_ONLY_AIRBORNE):
        if only_airborne:
            flights = [f for f in flights
                       if f.altitude > AIRBORNE_ALTITUDE_THRESHOLD]
        return flights

    def get_random_flight(self, flights):
        if not flights:
            return
        return random.choice(flights)

    def get_available_slot(self):
        for p in self.slots:
            if p not in self.slot_assignments.values():
                return p

    def sort_by_slot(self):
        sorted_assignments = sorted(self.slot_assignments.items(), 
                                     key=lambda x: x[1])
        sorted_ids = [a[0] for a in sorted_assignments]
        return [self.flights[i] for i in sorted_ids]
