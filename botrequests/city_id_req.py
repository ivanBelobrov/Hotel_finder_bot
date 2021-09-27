import requests
import json


def city_id_request(TOKEN, params):
    headers = {
        'x-rapidapi-key': TOKEN,
        'x-rapidapi-host': "hotels4.p.rapidapi.com"}

    url = "https://hotels4.p.rapidapi.com/locations/search"
    res = requests.request("GET", url, headers=headers, params=params)
    return json.loads(res.text)['suggestions'][0]['entities']



