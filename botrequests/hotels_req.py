import requests
import json


def hotels_request(TOKEN, params):
    headers = {
        'x-rapidapi-key': TOKEN,
        'x-rapidapi-host': "hotels4.p.rapidapi.com"}

    url = "https://hotels4.p.rapidapi.com/properties/list"
    response = requests.request('GET', url, headers=headers, params=params)
    return json.loads(response.text)









