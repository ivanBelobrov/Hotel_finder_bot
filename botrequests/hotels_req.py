import requests
import json
from datetime import datetime, timedelta


def rapid_api_request(TOKEN, querystring):
    headers = {
        'x-rapidapi-key': TOKEN,
        'x-rapidapi-host': "hotels4.p.rapidapi.com"}
    url = "https://hotels4.p.rapidapi.com/properties/list"
    response = requests.request('GET', url, headers=headers, params=querystring)
    return json.loads(response.text)['data']['body']['searchResults']['results']


def hotels_request(TOKEN, params):
    querystring = {"destinationId": params['city_id'],
                   "pageNumber": 1, "pageSize": params['hotels_amt'],
                   "checkIn": str(datetime.now().date()),
                   "checkOut": str(datetime.now().date() + timedelta(days=1)), "adults1": "1",
                   "sortOrder": params['sort_order'], "locale": "ru_RU",
                   "currency": "RUB"}

    if params['command'] == 'bestdeal':
        querystring.update({
            'priceMin': params['priceMin'],
            'priceMax': params['priceMax'],
            'landmarkIds': params['landmarkIds'],
            'pageSize': '25'
        })

    if params['command'] == 'bestdeal':
        hotels_list = list()
        while len(hotels_list) != int(params['hotels_amt']):
            for hotel in rapid_api_request(TOKEN, querystring):
                if float(params['distanceMin']) <= float('.'.join(hotel['landmarks'][0]['distance'].split(' ')[0].split(','))) <= float(params['distanceMax']):
                    hotels_list.append(hotel)
                if len(hotels_list) == int(params['hotels_amt']):
                    return hotels_list
            querystring['pageNumber'] += 1
        return hotels_list

    return rapid_api_request(TOKEN, querystring)









