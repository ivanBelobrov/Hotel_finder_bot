import telebot
from decouple import config

TOKEN = config('HOTELSBOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
