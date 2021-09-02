from botrequests import city_id_req, hotels_req
from User import User
from decouple import config
import telebot
from loguru import logger
from telebot import types
import time
from datetime import datetime, timedelta
from string import ascii_lowercase
import re

API_TOKEN, TOKEN = config('RAPIDAPI_KEY'), config('HOTELSBOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
my_logger = logger.add('log.log', format='{time} {level} {message}')


@bot.message_handler(commands=['start'])
def start_command(message):
    User(message.from_user.id)
    bot.send_message(message.from_user.id, 'Привет! я бот "Hotel_finder".')


@bot.message_handler(commands=['help'])
def get_text_message(message) -> None:
    bot.send_message(message.from_user.id, '/start - Запуск бота\n/help - Помощь\n'
                                           '/hello_world - Приветствие\n/lowprice - Подбор отелей с самой низкой ценой')


@bot.message_handler(commands=['lowprice'])
def low_price_command(message):
    if message.from_user.id not in User.users:
        User(message.from_user.id)
    logger.info('Received lowprice command from user {}'.format(message.from_user.id))
    bot.send_message(message.from_user.id, 'В каком городе вас интересуют отели?')
    bot.register_next_step_handler(message, get_city_id)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    bot.send_message(call.message.chat.id, 'Сколько отелей вам показать?')
    bot.register_next_step_handler(call.message, get_hotels, call.data)


def get_city_id(message):
    city = message.text.lower()
    logger.info('A user {} is looking for a hotel in {}'.format(message.from_user.id, city))
    querystring = dict()
    if all([True if sym in ascii_lowercase else False for sym in city]):
        querystring['query'] = city
        querystring['locale'] = 'en_US'
    elif all([True if sym in 'йцукенгшщзхъэждлорпавыфячсмитьбюё' else False for sym in city]):
        querystring['query'] = city
        querystring['locale'] = 'ru_RU'
    try:
        cities_data = city_id_req.city_id_request(API_TOKEN, querystring)
    except Exception as e:
        logger.error('Api error {}'.format(e))
        time.sleep(10)
        try:
            cities_data = city_id_req.city_id_request(API_TOKEN, querystring)
        except Exception as e:
            logger.error('Api error {}'.format(e))
            bot.send_message(message.from_user.id, 'Возникла ошибка, давайте начнем с начала')
            bot.register_next_step_handler(message, low_price_command)
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
    elif len(cities_list) == 0:
        bot.send_message(message.from_user.id, 'Город не найден. Попробуйте еще раз.')
        logger.error('City {} not found'.format(city))
        bot.register_next_step_handler(message, get_city_id)
    else:
        bot.send_message(message.from_user.id, 'Сколько отелей вам показать?')
        bot.register_next_step_handler(message, get_hotels, cities_list[0]['destinationID'])


def get_hotels(message, destination_id):
    User.users[message.from_user.id]['city_id'] = destination_id
    hotels_amt = message.text
    logger.info('Found the id of the desired city - {} and the number of hotels to search - {} for the user {}'.format(
        destination_id, hotels_amt, message.from_user.id))
    User.users[message.from_user.id]['hotels_amt'] = hotels_amt
    bot.send_message(message.from_user.id, 'Желаете загрузить фото отелей? Ответьте да или нет.')
    bot.register_next_step_handler(message, get_photo_url_and_request)


def get_photo_url_and_request(message):
    if message.text.lower() == 'да':
        User.users[message.from_user.id]['send_photo'] = True
        logger.info('User {} wants photos of hotels'.format(message.from_user.id))
    else:
        User.users[message.from_user.id]['send_photo'] = False
        logger.info('User {} dose not want photos of hotels'.format(message.from_user.id))
    user_params = User.get_user_params(message.from_user.id)
    querystring = {"destinationId": user_params['city_id'],
                   "pageNumber": "1", "pageSize": user_params['hotels_amt'],
                   "checkIn": str(datetime.now().date()),
                   "checkOut": str(datetime.now().date() + timedelta(days=1)), "adults1": "1",
                   "sortOrder": "PRICE", "locale": "ru_RU",
                   "currency": "RUB"}
    try:
        data = hotels_req.hotels_request(API_TOKEN, querystring)
    except Exception as e:
        logger.error('Api error {}'.format(e))
        time.sleep(10)
        try:
            data = hotels_req.hotels_request(API_TOKEN, querystring)
        except Exception as e:
            logger.error('Api error {}'.format(e))
            bot.send_message(message.from_user.id, 'Что-то пошло не так, давайте начнем все с начала.')
            bot.register_next_step_handler(message, low_price_command)

    if user_params.get('send_photo'):
        for hotel in data['data']['body']['searchResults']['results']:
            hotel_name = hotel['name']
            hotel_photo = hotel['optimizedThumbUrls']['srpDesktop']
            hotel_address = hotel['address']['streetAddress']
            hotel_dist = hotel['landmarks'][0]['distance']
            hotel_price = hotel['ratePlan']['price']['current']
            bot.send_message(message.from_user.id, '{}\n<a href="{}">&#8203;</a>\n{}\n{}\n{}'.format(
                hotel_name,
                hotel_photo,
                hotel_address,
                hotel_dist,
                hotel_price
            ), parse_mode='HTML')
    else:
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


bot.polling(none_stop=True)

