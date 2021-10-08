import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Union
from collections.abc import Callable


def rapid_api_request(TOKEN: str, querystring: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Функция делает запрос к API и возвращает список результатов в виде словарей, в которых хранятся параметры подходящих
    отелей.

    :param TOKEN: токен для доступа к API
    :type: str
    :param querystring: параметры, передаваемые в функцию для формирования запроса
    :type: Dict[str, Any]
    :return: результат запроса в виде списка словарей, в которых хранятся параметры подходящих отелей
    :rtype: List[Dict[str, Any]]
    """
    headers = {
        'x-rapidapi-key': TOKEN,
        'x-rapidapi-host': "hotels4.p.rapidapi.com"}
    url = "https://hotels4.p.rapidapi.com/properties/list"
    response = requests.request('GET', url, headers=headers, params=querystring)
    return json.loads(response.text)['data']['body']['searchResults']['results']


def hotels_request(TOKEN: str, params: Dict[str, Any]) -> Union[Callable, List[Dict[str, Any]]]:
    """
    Функция, которая формирует параметры запроса перед передачей в функцию rapid_api_request()

    :param TOKEN: токен для доступа к API
    :type: str
    :param params: параметры передаваемые в функцию для формирования запроса
    :type: Dict[str, Any]
    :return: возвращает список отелей в виде словарей, в которых хранятся параметры, подхожящих отелей или возвращает
     результат работы функции rapid_api_request()
    :rtype: Union[Callable, List[Dict[str, Any]]]
    """
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
            hotels = rapid_api_request(TOKEN, querystring)
            if not hotels:
                return hotels_list
            for hotel in hotels:
                cur_distance = float('.'.join(hotel['landmarks'][0]['distance'].split(' ')[0].split(',')))
                if float(params['distanceMin']) <= cur_distance <= float(params['distanceMax']):
                    hotels_list.append(hotel)
                    if len(hotels_list) == int(params['hotels_amt']):
                        return hotels_list
                elif float(cur_distance) > float(params['distanceMax']):
                    return hotels_list
            querystring['pageNumber'] += 1
        return hotels_list

    return rapid_api_request(TOKEN, querystring)









