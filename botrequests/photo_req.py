import requests
import json
from pprint import pprint
from decouple import config
import telebot

API_TOKEN, TOKEN = config('RAPIDAPI_KEY'), config('HOTELSBOT_TOKEN')
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def photo(message):
    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"

    querystring = {"id": "1178275040"}

    headers = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': "0f123c60b9msh1e7991fcc1d156ep152a0fjsn7dadfd804f37"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    data = json.loads(response.text)

    photos_amt = 5
    media_group = list()
    for i_photo in range(photos_amt):
        # media_group.append({'type': 'photo', 'media': data['hotelImages'][i_photo]['baseUrl'].format(
        #     size=data['hotelImages'][i_photo]['sizes'][0]['suffix']), 'parse_mode': 'HTML'}) # Пробовал создавать список словарей
        media_group.append(data['hotelImages'][i_photo]['baseUrl'].format(   # И просто список URLов
                size=data['hotelImages'][i_photo]['sizes'][0]['suffix']))
    media_group_json = json.dumps(media_group)
    pprint(media_group)
    bot.send_media_group(message.from_user.id, media=media_group_json)


bot.polling(none_stop=True)
