import requests
import json
from typing import Dict, Any, List


def city_id_request(TOKEN: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Функция, которая делает запрос к API для определения id города.

    :param TOKEN: токен для доступа к API
    :type: str
    :param params: параметры передаваемые в функцию для формирования запроса.
    :type: Dict[str, Any]
    :return: список словарей с данными о населенных пунктах
    :rtype: List[Dict[str, Any]]
    """
    headers = {
        'x-rapidapi-key': TOKEN,
        'x-rapidapi-host': "hotels4.p.rapidapi.com"}

    url = "https://hotels4.p.rapidapi.com/locations/search"
    res = requests.request("GET", url, headers=headers, params=params)
    return json.loads(res.text)['suggestions'][0]['entities']
