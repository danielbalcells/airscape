from geopy.geocoders import Nominatim


USER_AGENT = "Airscape"
MILES_PER_DEGREE = 69
X1 = 'x1'
X2 = 'x2'
Y1 = 'y1'
Y2 = 'y2'
ORDER_BBOXFINDER = [X1, Y1, X2, Y2]
ORDER_FR_API = [Y2, Y1, X1, X2]
ORDER_DEFAULT = ORDER_FR_API


class BoundingBox(object):

    def __init__(self, center_query, margin_mi):
        self.geolocator = Nominatim(user_agent="Airscape")
        self.center_query = center_query
        self.center = self.geolocator.geocode(center_query)
        self.margin_mi = margin_mi
        self.margin_latlong = margin_mi/MILES_PER_DEGREE
        self.x1 = self.center.longitude - self.margin_latlong
        self.y1 = self.center.latitude - self.margin_latlong
        self.x2 = self.center.longitude + self.margin_latlong
        self.y2 = self.center.latitude + self.margin_latlong
        self.coordinates = {
            X1: self.x1,
            X2: self.x2,
            Y1: self.y1,
            Y2: self.y2
        }

    def __str__(self):
        return self.get_coordinate_string()

    def __repr__(self):
        return f'<BoundingBox {self}, {self.center_query}>'

    def get_coordinate_string(self, order=ORDER_DEFAULT):
        coordinate_string = ''
        for o in order:
            coordinate_string += f'{self.coordinates[o]},'
        return coordinate_string[:-1]
