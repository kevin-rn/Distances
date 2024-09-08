import json
import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import http.client, urllib.parse

# Global variables
API_KEY = # Insert PositionStack API key here
GeoLocator = Nominatim(user_agent="Distance-Locations")


# Loads data stored in csv file into dataframe
def load_data(file_loc:str = "resources/addresses.csv"):
    headers = ['Name', 'Address']
    addresses_df = pd.read_csv(file_loc, 
                                delimiter=' - ', 
                                names=headers, 
                                engine='python')
    return addresses_df


# Retrieve coordinates (Latitude, Longitude) for single address
def get_location(address:str):
    location = GeoLocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    else:
        # Use Positionstack whenever Nominatim can't retrieve coordinates
        # https://positionstack.com/documentation
        conn = http.client.HTTPConnection('api.positionstack.com')
        params = urllib.parse.urlencode({
            'access_key': API_KEY,
            'query': address,
            'limit': 1,
            })
        conn.request('GET', '/v1/forward?{}'.format(params))
        res = conn.getresponse()
        bytes_data = res.read()
        
        # Use json.loads to parse the bytes data
        json_data = json.loads(bytes_data.decode('utf-8'))
        latitude = json_data['data'][0]['latitude']
        longitude = json_data['data'][0]['longitude']
        return latitude, longitude


# Retrieves all coordinates for all dataframe entries
def get_all_locations(addresses_df):
    latitude_list = []
    longitude_list = []

    for index, row in addresses_df.iterrows():
        location = row['Address']
        lat, lon = get_location(location)
        latitude_list.append(lat)
        longitude_list.append(lon)

    addresses_df['latitude'] = latitude_list
    addresses_df['longitude'] = longitude_list


# Calculates distance between address coordinates denoted by (latitude, longitude)
def calculate_distance(addr_1:str, addr_2:str):
    dist = geodesic(addr_1, addr_2).km
    return dist


def main():
    # Load data
    addresses_df = load_data()

    # Calculate all coordinates
    # addresses_df[['latitude', 'longitude']]=addresses_df[['location']].apply(get_location, axis=1, result_type='expand') # goes to wrong if else case
    get_all_locations(addresses_df)

    # Calculate distance to first target entry
    target_coords = (addresses_df.loc[0, 'latitude'], addresses_df.loc[0, 'longitude'])
    addresses_df['Distance'] = addresses_df.apply(lambda row: calculate_distance(target_coords, (row['latitude'], row['longitude'])), axis=1)
    addresses_df = addresses_df.sort_values('Distance')

    # Format final results
    addresses_df = addresses_df.iloc[1:]
    addresses_df['Distance'] = addresses_df['Distance'].map(lambda x: f"{x:.2f} km")
    addresses_df['Sortnumber'] = range(1, len(addresses_df) + 1)
    final_df = addresses_df[['Sortnumber', 'Distance', 'Name', 'Address']]
    print(final_df)
    final_df.to_csv('resources/distances.csv', index=False)


if __name__ == "__main__":
    main()
