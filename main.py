# -*- coding: utf-8 -*-
"""
Created on Mon Dec 23 22:56:45 2024

@author: csvww
"""

import json
import os
from datetime import datetime
import telebot
import random
import asyncio
import threading

async_test = False

TG_TOKEN = open('mountables/token.txt', 'r').read()
bot = telebot.TeleBot(TG_TOKEN, parse_mode = 'HTML')

class JSONDatabase:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = self._load_data()

    def _load_data(self):
        '''Load data from the JSON file.'''
        try:
            with open(self.file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def _save_data(self):
        '''Save data to the JSON file.'''
        with open(self.file_path, 'w') as file:
            json.dump(self.data, file, ensure_ascii = False, indent = 4)

    def get_pet_data(self, owner_id):
        '''Retrieve pet data by owner ID.'''
        return self.data.get(str(owner_id))

    def save_pet_data(self, owner_id, pet_data):
        '''Save/update pet data for an owner ID.'''
        self.data[str(owner_id)] = pet_data
        self._save_data()

class TorraPet:
    def __init__(self, 
                 owner_id, 
                 name, 
                 species, 
                 image = None,
                 hunger = 50,
                 fun = 100,
                 creation_date = None, 
                 update_time = None):
        self.owner_id = str(owner_id)
        self.name = name
        self.species = species
        self.image = image or random.choice(os.listdir(f'mountables/species/{species}'))
        self.hunger = hunger
        self.fun = fun
        self.creation_date = creation_date or datetime.now().isoformat()
        self.update_time = update_time or datetime.now().timestamp()

    def to_dict(self):
        '''Convert the pet to a dictionary for saving.'''
        return {
            'name': self.name,
            'species': self.species,
            'image': self.image,
            'hunger': self.hunger,
            'fun': self.fun,
            'creation_date': self.creation_date,
            'update_time': self.update_time
        }

class TorraPetManager:
    '''Class for TorraPetManager'''
    def __init__(self, db: JSONDatabase):
        self.db = db

    def load_pet(self, owner_id):
        '''Load a pet by owner ID.'''
        pet_data = self.db.get_pet_data(owner_id)
        if not pet_data:
            return None
        else:
            return TorraPet(owner_id, **pet_data)

    def save_pet(self, pet: TorraPet):
        '''Save a pet to the database.'''
        self.db.save_pet_data(pet.owner_id, pet.to_dict())

def get_species():
    with open('mountables/species.json', 'r') as f:
        species_dict = json.load(f)
        return species_dict


db = JSONDatabase('mountables/pets.json')
tpm = TorraPetManager(db)
species = get_species()

async def update_hunger():
    while True:
        for pet in db.data.items():
            pet = list(pet)
            time_passed = datetime.now().timestamp() - pet[1]['update_time']
            hunger_increase = species[pet[1]['species']]['hunger_increase']
            pet[1]['hunger'] = min(100, int(pet[1]['hunger'] + (time_passed * hunger_increase)))
            pet[1]['update_time'] = datetime.now().timestamp()
            db.save_pet_data(pet[0], pet[1])
        await asyncio.sleep(20*60)
        #TODO warnings about hunger
        
# async def update_fun():
#     while True:
#         for pet in db.data.items():
#             pet = list(pet)
#             time_passed = datetime.now().timestamp() - pet[1]['update_time']
#             fun_decrease = species[pet[1]['species']]['fun_decrease']
#             pet[1]['fun'] = max(0, int(pet[1]['fun'] + (time_passed * fun_decrease)))
#             pet[1]['update_time'] = datetime.now().timestamp()
#             db.save_pet_data(pet[0], pet[1])
#         await asyncio.sleep(20*60)
        #TODO warnings about fun
        #TODO also maybe add multipliers in single json level, maybe then we can do one async fun

@bot.message_handler(commands = ['start', 'status'])
def tg_welcome_and_status(message):
    owner_id = message.from_user.id
    pet = tpm.load_pet(owner_id)
    if pet:
        bot.send_photo(message.from_user.id,
                       open(f'mountables/species/{pet.species}/{pet.image}', 'rb'),
                       reply_to_message_id = message.message_id)
        bot.reply_to(message, f'TorraPet @{message.from_user.username}\n\n{species[pet.species]["icon"]} <b>{pet.name}</b>\n\nГолод: {pet.hunger}\nВеселье: {pet.fun}') #TODO
    else:
        species_text = [x['icon'] + ' ' + x['ru_name'] + '\n' for x in species.values()]
        species_text = ''.join(species_text)
        bot.reply_to(message, 'Добро пожаловать в TorraPet v0.1! Вот каких питомцев ты можешь сейчас завести:\n\n' + species_text + '\n\nЧтобы узнать побольше о видах, используй команду /info. Как определишься, используй команду с названием вида питомца и его будущим именем, например "/дадун Алёша".')

@bot.message_handler(commands = [x['ru_name'] for x in species.values()])
def tg_create_pet(message):
    owner_id = message.from_user.id
    pet = tpm.load_pet(owner_id)
    if pet:
        bot.reply_to(message, f'У тебя уже есть {pet.species} по имени {pet.name}. Куда ещё? с:') #TODO
    else:
        try:
            pet_species = message.text.split(maxsplit = 1)[0].replace('/', '')
            name = message.text.split(maxsplit = 1)[1]
            new_pet = TorraPet(owner_id = owner_id, name = name, species = pet_species)
            tpm.save_pet(new_pet)
            pet = tpm.load_pet(owner_id)
            bot.send_photo(message.from_user.id,
                           open(f'mountables/species/{pet.species}/{pet.image}', 'rb'),
                           reply_to_message_id = message.message_id)
            bot.reply_to(message, f'Готово, теперь у тебя есть твой собственный TorraPet!\nЭто {pet.species} по имени {pet.name}.')
        except IndexError:
            bot.reply_to(message, 'Что-то не так. Используй команду с названием вида питомца и его будущим именем. Например "/дадун Алёша".')

@bot.message_handler(commands = ['feed'])
def tg_feed_pet(message):
    owner_id = message.from_user.id
    pet = tpm.load_pet(owner_id)
    if not pet:
        bot.reply_to(message, 'У тебя пока нет TorraPet. Чтобы узнать, как его завести, используй команду /start.')
    else:
        pet.hunger = max(0, pet.hunger - 40)
        species = get_species()
        bot.reply_to(message, f'{pet.name} {random.choice(species[pet.species]["feeding_text"])}!\nНовый уровень голода: {int(pet.hunger)}%.')

@bot.message_handler(commands = ['info'])
def tg_species_info(message):
    for s in species.items():
        title = s[1]['icon'] + ' ' + s[1]['ru_name'].capitalize() + ' ' + s[1]['icon']
        s_image = random.choice(os.listdir(f'mountables/species/{s[0]}/')) #TODO fix this mess of a reference to dir
        bot.send_photo(message.from_user.id,
                       open(f'mountables/species/{s[0]}/{s_image}', 'rb'))
        bot.send_message(message.from_user.id, 
                         text = f'<i>{title}</i>\n\n{s[1]["desc"]}')

# def guess_highest(message, pet):
#     tokens = random.randint(10, 99)
#     bot.send_message(message.from_user.id, f'{pet.name} что-то прячет в лапках. Это листочки, которые твой TorraPet натаскал с прогулки. Их двузначное число. Поробуй угадать, сколько их, и {pet.name} порадуется! (Используй команду /play. Например, /play 69.) ')

def start_polling():
    bot.polling(none_stop = True, timeout = 1000)
    
if __name__ == "__main__":
    if async_test:
        loop = asyncio.get_event_loop()
        loop.create_task(update_hunger())
        # loop.create_task(update_fun())
        
        threading.Thread(target = start_polling()).start()
    else:
        start_polling() #TODO remove this obv

#TODO playing. professions? relationship
#TODO deal with runame
#TODO tictactoe hangman quiz
#TODO species class please