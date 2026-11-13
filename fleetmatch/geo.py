"""Geographic helpers."""
import math


def hav(a, b):
    """Haversine distance in km between two {'lat','lng'} points."""
    r = math.pi / 180
    x = (math.sin((b['lat'] - a['lat']) * r / 2) ** 2
         + math.cos(a['lat'] * r) * math.cos(b['lat'] * r)
         * math.sin((b['lng'] - a['lng']) * r / 2) ** 2)
    return 12742 * math.asin(math.sqrt(x))
