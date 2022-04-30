from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer



DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 5005

DEFAULT_FIELDS = [
    'slot',
    'new',
    'id',
    'number',
    'altitude',
    'ground_speed',
    'heading',
    'delta_heading',
    'distance_to_center_mi',
    'proximity',
    'progress',
    'progress_percent',
    'bbox_pan_lat',
    'bbox_pan_lon'
]


class OSCController(object):

    def __init__(self, ip=DEFAULT_IP, port=DEFAULT_PORT,
                 fields=DEFAULT_FIELDS):
        self.ip = ip
        self.port = port
        self.fields = fields
        self.client = udp_client.SimpleUDPClient(ip, port)

    def send_flight(self, flight):
        address_root = f'/{flight.slot}'
        for field in self.fields:
            value = flight.__getattribute__(field)
            address = address_root + f'/{field}'
            self.client.send_message(address, value)


class BlockingOSCServer(object):

    def __init__(self, ip=DEFAULT_IP, port=DEFAULT_PORT):
        self.ip = ip
        self.port = port
        self.dispatcher = Dispatcher()
        self.dispatcher.set_default_handler(self.default_handler)
        self.server = BlockingOSCUDPServer(
            (self.ip, self.port), self.dispatcher)

    def default_handler(address, *args):
        print(f"{address}: {args}")

    def serve_forever(self):
        self.server.serve_forever()
