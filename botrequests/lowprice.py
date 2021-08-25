from bot_init import bot
import requests
from string import ascii_lowercase
import re
import json
from telebot import types
from datetime import datetime, timedelta
from User import User

headers = {
    'x-rapidapi-key': "0f123c60b9msh1e7991fcc1d156ep152a0fjsn7dadfd804f37",
    'x-rapidapi-host': "hotels4.p.rapidapi.com"
}


@bot.message_handler(commands=['lowprice'])
def low_price_command(message):
    bot.send_message(message.from_user.id, 'В каком городе вас интересуют отели?')
    bot.register_next_step_handler(message, get_city_id)


def get_city_id(message):
    city = message.text.lower()
    querystring = dict()
    if all([True if sym in ascii_lowercase else False for sym in city]):
        querystring['query'] = city
        querystring['locale'] = 'en_US'
    elif all([True if sym in 'йцукенгшщзхъэждлорпавыфячсмитьбюё' else False for sym in city]):
        querystring['query'] = city
        querystring['locale'] = 'ru_RU'
    else:
        bot.send_message(message.from_user.id, 'Кажется вы не верно указали название города.'
                                               ' Попробуйте еще раз.')
        bot.register_next_step_handler(get_city_id)

    url = "https://hotels4.p.rapidapi.com/locations/search"

    res = requests.request("GET", url, headers=headers, params=querystring)

    cities_data = json.loads(res.text)['suggestions'][0]['entities']
    cities_list = list()
    for city_dict in cities_data:

        if 'CITY' in city_dict.values() and city_dict['name'].lower() == city:
            cities_list.append({
                'destinationID': city_dict['destinationId'],
                'city_name': city_dict['name'] + ''.join(re.findall(r'>(,\s.*)', city_dict['caption']))
            })

    if len(cities_list) > 1:
        markup = types.InlineKeyboardMarkup(row_width=2)

        for i in cities_list:
            button = types.InlineKeyboardButton(i['city_name'], callback_data=i['destinationID'])
            markup.add(button)

        bot.send_message(message.from_user.id, 'Какой город вы имели ввиду?', reply_markup=markup)

    else:
        bot.send_message(message.from_user.id, 'Сколько отелей вам показать?')
        bot.register_next_step_handler(message, get_hotels, cities_list[0]['destinationID'])


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    bot.send_message(call.message.chat.id, 'Сколько отелей вам показать?')

    bot.register_next_step_handler(call.message, get_hotels, call.data)


def get_hotels(message, destination_id):
    User.users[message.from_user.id]['city_id'] = destination_id
    hotels_amt = message.text
    User.users[message.from_user.id]['hotels_amt'] = hotels_amt
    url = "https://hotels4.p.rapidapi.com/properties/list"

    querystring = {"destinationId": User.users[message.from_user.id]['city_id'],
                   "pageNumber": "1", "pageSize": User.users[message.from_user.id]['hotels_amt'],
                   "checkIn": str(datetime.now().date()),
                   "checkOut": str(datetime.now().date() + timedelta(days=1)), "adults1": "1",
                   "sortOrder": "PRICE", "locale": "ru_RU",
                   "currency": "RUB"}

    response = requests.request('GET', url, headers=headers, params=querystring)

    data = json.loads(response.text)
    for hotel in data['data']['body']['searchResults']['results']:
        hotel_name = hotel['name']
        hotel_address = hotel['address']['streetAddress']
        hotel_dist = hotel['landmarks'][0]['distance']
        hotel_price = hotel['ratePlan']['price']['current']
        bot.send_message(message.from_user.id, '{}\n{}\n{}\n{}'.format(
                                                                        hotel_name,
                                                                        hotel_address,
                                                                        hotel_dist,
                                                                        hotel_price
        ))




