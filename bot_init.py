from decouple import config
import telebot

TOKEN = config('HOTELSBOT_TOKEN')
bot = telebot.TeleBot(TOKEN)