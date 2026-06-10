def haversine_distance(coord1, coord2):
    """
    Calculate the Haversine distance between two points on the Earth specified in decimal degrees.
    Returns distance in kilometers.
    """
    from math import radians, cos, sin, asin, sqrt

    lat1, lon1 = coord1
    lat2, lon2 = coord2

    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    
    # Radius of Earth in kilometers. Use 3956 for miles
    r = 6371
    return c * r #TODO to change wen we have real geolocalisation