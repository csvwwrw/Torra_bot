# -*- coding: utf-8 -*-
"""
Created on Tue Dec 17 21:37:08 2024

@author: csvww
"""

import asyncio
import time
import datetime
import json
import os
from pathlib import Path
import telebot
from telebot.async_telebot import AsyncTeleBot
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply

TG_TOKEN = open('mountables/token.txt', 'r').read()
bot = telebot.TeleBot(TG_TOKEN, parse_mode = 'HTML')

### PET CLASS ###
class TorraPet:
    def __init__(self, owner_id, species):
        self.owner_id = owner_id
        self.species = species
        self.name = ''
        self.hunger = 0
        self.last_update = time.time()
    
    def to_dict(self):
        return {
            'owner_id': self.owner_id,
            'species': self.species,
            'name': self.name,
            'hunger': self.hunger,
            'last_update': self.last_update
        }
    
    @classmethod
    def from_dict(cls, data):
        pet = cls(data['owner_id'], data['name'])
        pet.hunger = data['hunger']
        pet.last_update = data['last_update']
        return pet
    
###   PET MANAGER CLASS   ###
class TorraPetManager:
    def __init__(self):
        self.pets = {}
        self.load_pets()
        
    def create_pet(self, owner_id, name):
        self.remove_pet(owner_id)
        
        pet = TorraPet(owner_id, name)
        self.pets[owner_id] = pet
        self.save_pets()
        return pet
    
    def get_pet(self, owner_id):
        return self.pets.get(owner_id)
    
    def remove_pet(self, owner_id):
        if owner_id in self.pets:
            del self.pets[owner_id]
            self.save_pets()
    
    def save_pets(self):
        with open('mountables/pets.json', 'w') as f:
            pets_dict = {str(k): v.to_dict() for k, v in self.pets.items()}
            json.dump(pets_dict, f, ensure_ascii=False, indent=2)
            
    def load_pets(self):
        try:
            with open('mountables/pets.json', 'r') as f:
                pets_dict = json.load(f)
                self.pets = {int(k): TorraPet.from_dict(v) for k, v in pets_dict.items()}
        except FileNotFoundError:
            self.pets = {}
            
pet_manager = TorraPetManager()

#TODO hunger
# async def update_hunger():
#     while True:
#         for pet in pet_manager.pets.values():
#             time_passed = time.time() - pet.last_update
#             hunger_increase = time_passed * 0.1
#             pet.hunger = min(100, pet.hunger + hunger_increase)
#             pet.last_update = time.time()
#         pet_manager.save_pets()
#         print('hunger')
#         await asyncio.sleep(10)
        
def start_polling():
    bot.polling(none_stop=True)
    
def get_species():
    with open('mountables/species.json', 'r') as f:
        species_dict = json.load(f)
        return species_dict
    
def create_species_choice_keyboard():
    species_buttons = []
    species = get_species()
    for s in species:
        species_button = [species[s]['icon'] + species[s]['ru_name'].capitalize()]
        species_button.append('species_choice_' + s)
        species_buttons.append(species_button)
    markup = InlineKeyboardMarkup()
    for button in species_buttons:
        markup.add(InlineKeyboardButton(button[0], callback_data = button[1]))
    return markup

def finalize_pet(call):
    owner_id = call.from_user.id
    species = call.data.split('_', 2)[2]
    username = call.from_user.username
    pet_manager.create_pet(owner_id, species)
    bot.edit_message_text(chat_id = call.message.chat.id,
                          message_id = call.message.message_id,
                          text = f'@{username} хочет себе зверюшку {species}!')
    bot.send_message(chat_id = call.message.chat.id,
                     text = f'Осталось совсем немного! @{username}, дай своему TorraPet вида {species} имя командой /name &lt;имя&gt; (без треугольных скобок).')
#TODO maybe delete
def check_if_named(pet):
    if pet.name:
        return True
    else:
        return False
    

###   TG COMMANDS   ###

@bot.message_handler(commands=['start'])
def welcome(message):
    owner_id = message.from_user.id
    pet = pet_manager.get_pet(owner_id)
    if pet:
        #TODO
        bot.reply_to(message,
                     'Давай проведаем твоего TorraPet!')
        bot.send_message(message.chat.id, 
                         f'TorraPet @{message.from_user.id}\n<b>{pet.name}</b>\n<i>{pet.species}</i>\n\nСтатус:\nвозраст - {time.time() - pet.last_update}\nголод - {pet.hunger}')
    else:
        bot.reply_to(message, "Добро пожаловать в TorraPet! Используй команду /create &lt;имя&gt; чтобы создать своего питомца.")

@bot.message_handler(commands = ['create'])
def create_pet(message):
    pet_manager = TorraPetManager()
    owner_id = message.from_user.id
    pet = pet_manager.get_pet(owner_id)
    if pet:
        bot.reply_to(message, f"У тебя уже есть TorraPet! Ты что, совсем забыл про {pet.name}?")
    else:
        bot.reply_to(message, "Для начала давай решим, какого вида будет твоей TorraPet.",
                 reply_markup = create_species_choice_keyboard())

@bot.message_handler(commands = ['name'])
def name_pet(message):
    owner_id = message.from_user.id
    pet = pet_manager.get_pet(owner_id)
    if pet and pet.name == '':
        try:
            name = message.text.split(maxsplit=1)[1]
            owner_id = message.from_user.id
            pet = pet_manager.get_pet(owner_id)
            pet.name = name
            pet_manager.save_pets()
            bot.reply_to(message, f"Теперь у @{message.from_user.username} есть очаровательный {get_species()[pet.species]['ru_name']} по имени {name}!")
        except IndexError:
            bot.reply_to(message, "Пожалуйста, дай своему TorraPet имя комнандой /name &lt;имя&gt;.")
    
    elif pet and pet.name != '':
        bot.reply_to(message, f"У твоего питомца уже есть имя: {pet.name}.")
        
    else:
        bot.reply_to(message, "У тебя ещё нет TorraPet. Ты можешь завести его командой /create.")
        
#TODO feeding
# @bot.message_handler(commands = ['feed'])
# def feed_pet(message):
#     owner_id = message.from_user.id
#     pet = pet_manager.get_pet(owner_id)
#     if pet:
#         pet.hunger = max(0, pet.hunger - 30)
#         pet_manager.save_pets()
#         bot.reply_to(message, f"Fed {pet.name}! Current hunger: {pet.hunger:.1f}%")
#     else:
#         bot.reply_to(message, "You don't have a pet! Use /create <name> to create one.")
        
@bot.callback_query_handler(func = lambda call: True)
def callback_query(call):
    if call.data.startswith('species_choice_'):
        finalize_pet(call)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    # loop.create_task(update_hunger())
    
    threading.Thread(target=start_polling).start()