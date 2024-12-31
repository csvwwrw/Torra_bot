# -*- coding: utf-8 -*-
'''
Created on Sun Sep  1 15:45:38 2024

@author: csvww
'''
import json
import os
from datetime import datetime
import threading
import schedule

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply

TOKEN = '5112982075:AAFaVnKK4dowtmeiAVrMn6GIeMr8xY8wiNw'

bot = telebot.TeleBot(token = TOKEN, parse_mode = 'HTML')

pets = [
        ['🐔', 'dadun'],
        ['😸 ', 'mokhnonozhka']
        ]

def json_to_pet(user_id):
    with open(f'user_data/{user_id}.json', 'r', encoding='utf-8') as pet_json:
        pet_data = json.load(pet_json)
    return pet_data

def pet_to_json(user_id, pet_data):
    with open(f'user_data/{user_id}.json', 'w', encoding='utf-8') as pet_json:
        json.dump(pet_data, pet_json, indent = 4)

def create_inline_keyboard(buttons):
    markup = InlineKeyboardMarkup()
    for button in buttons:
        markup.add(InlineKeyboardButton(button[0], callback_data = button[1]))
    return markup

def choose_pet(call):
    user_id = call.from_user.id
    user_username = call.from_user.username
    pet_type = call.data.split('_', 1)[1]
    pet_data = json_to_pet("default_user")
    pet_data['user'] = user_id
    pet_data['chat'] = call.message.chat.id
    pet_data['pet']['type'] = pet_type
    pet_data['pet']['creation_date'] = str(datetime.now())
    pet_to_json(user_id, pet_data)
    bot.edit_message_text(chat_id = call.message.chat.id,
                          message_id = call.message.message_id,
                          text = f'@{user_username} homed a {pet_type}!')
    markup = ForceReply(selective = True)
    bot.send_message(chat_id = call.message.chat.id,
                     text = f'@{user_username}, now give your {pet_type} a name.',
                     reply_markup = markup)

@bot.message_handler(commands = ['start'], chat_types = ['group', 'supergroup'])
def start_bot(message):
    user_id = message.from_user.id
    if os.path.exists(f'user_data/{user_id}.json'):
        bot.send_message(message.chat.id, 'You already have a TorraPet!')
    else:
        petchoice_buttons = []
        for pet in pets:
            petchoice_button = [pet[0] + pet[1].capitalize()]
            petchoice_button.append('petchoice_' + pet[1])
            petchoice_buttons.append(petchoice_button)
        bot.send_message(message.chat.id,
                         'Choose your TorraPet:', 
                         reply_markup = create_inline_keyboard(petchoice_buttons))
        
@bot.message_handler(commands = ['mypet'], chat_types = ['group', 'supergroup'])
def check_pet(message):
    user_id = message.from_user.id
    pet_data = json_to_pet(user_id)
    bot.reply_to(message, f'Your {pet_data["pet"]["type"]} is named {pet_data["pet"]["name"]}.')

@bot.message_handler(func = lambda message:
                     message.reply_to_message is not None
                     and "a name" in message.reply_to_message.text)
def name_pet(message):
    pet_name = message.text
    user_id = message.from_user.id
    pet_data = json_to_pet(user_id)
    pet_data['pet']['name'] = pet_name
    pet_to_json(user_id, pet_data)
    pet_type = pet_data['pet']['type']
    bot.reply_to(message, f'Awesome! Now @{message.from_user.username} has a beautiful {pet_type} named {pet_name}!')

@bot.callback_query_handler(func = lambda call: True)
def callback_query(call):
    if call.data.startswith('petchoice'):
        choose_pet(call)
        
def check_schedule():
    print('1 min passed')

schedule.every(1).minute.do(check_schedule)
    
if __name__ == '__main__':
    scheduler_thread = threading.Thread(target=schedule.run_pending())
    scheduler_thread.start()
    
    bot.infinity_polling()
