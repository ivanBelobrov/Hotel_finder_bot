import requests
import json
from decouple import config
from telebot.types import InputMediaPhoto
from User import User

API_TOKEN = config('RAPIDAPI_KEY')


def get_photo(hotel, user_id):
    hotel_name = hotel['name']
    hotel_address = hotel['address']['streetAddress']
    hotel_dist = hotel['landmarks'][0]['distance']
    hotel_price = hotel['ratePlan']['price']['current']
    message = '{}\n\n{}\n{}\n{}'.format(
        hotel_name,
        hotel_address,
        hotel_dist,
        hotel_price)
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
    return photos
