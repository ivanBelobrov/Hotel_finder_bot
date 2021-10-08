import requests
import json
from decouple import config
from telebot.types import InputMediaPhoto
from Classes.User import User
from typing import Tuple, List, Dict, Any

API_TOKEN = config('RAPIDAPI_KEY')


def get_photo(hotel: Dict[str, Any], user_id: int, hotels_names: str, message: str)\
        -> Tuple[List[InputMediaPhoto], str]:
    """
    Функция, которая делает запрос к API и получает фотографии отелей,
    а так же их названия для формирования записи в БД.

    :param hotel: словарь с параметрами отеля
    :type: Dict[str, Any]
    :param user_id: id пользователя
    :type: int
    :param hotels_names: перечисление названий отеля, подобранных для пользователя
    :type: str
    :param message: текст сообщения для пользователя с описанием отеля
    :type: str
    :return: кортеж в котором содержится список из объектов класса InputMediaPhoto и перечисление найденных отелей.
    :rtype: Tuple[List[InputMediaPhoto], str]
    """
    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
    querystring = {"id": hotel['id']}
    headers = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': API_TOKEN
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    data_photo = json.loads(response.text)
    photos_amt = int(User.get_user_params(user_id)['photo_amt'])
    photo_links = list()
    for i_photo in range(photos_amt):
        photo_links.append(data_photo['hotelImages'][i_photo]['baseUrl'].format(
            size=data_photo['hotelImages'][i_photo]['sizes'][0]['suffix']))
    photos = [InputMediaPhoto(media=link, caption=message) for link in photo_links[:1]]
    photos.extend([InputMediaPhoto(media=link) for link in photo_links[1:]])
    return photos, hotels_names
