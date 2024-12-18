# -*- coding: utf-8 -*-
"""
Created on Tue Dec 17 21:37:08 2024

@author: csvww
"""

import asyncio
import time
import json
import os
from pathlib import Path
import telebot
from telebot.async_telebot import AsyncTeleBot
import threading

TG_TOKEN = open('mountables/token.txt', 'r').read()
bot = telebot.TeleBot(TG_TOKEN)

class TorraPet:
    def __init__(self, owner_id, name):
        self.owner_id = owner_id
        self.name = name
        self.hunger = 0
        self.last_update = time.time()
    
    def to_dict(self):
        return {
            'owner_id': self.owner_id,
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
            json.dump(pets_dict, f)
            
    def load_pets(self):
        try:
            with open('mountables/pets.json', 'r') as f:
                pets_dict = json.load(f)
                self.pets = {int(k): TorraPet.from_dict(v) for k, v in pets_dict.items()}
        except FileNotFoundError:
            self.pets = {}
            
pet_manager = TorraPetManager()

async def update_hunger():
    while True:
        for pet in pet_manager.pets.values():
            time_passed = time.time() - pet.last_update
            hunger_increase = time_passed * 0.1
            pet.hunger = min(100, pet.hunger + hunger_increase)
            pet.last_update = time.time()
        pet_manager.save_pets()
        print('hunger')
        await asyncio.sleep(10)
        
def start_polling():
    bot.polling(none_stop=True)
        
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to Pet Bot! Use /create to create your pet.")

@bot.message_handler(commands = ['create'])
def creare_pet(message):
    try:
        name = message.text.split(maxsplit = 1)[1]
        owner_id = message.from_user.id
        pet = pet_manager.create_pet(owner_id, name)
        bot.reply_to(message, f"Created your new pet named {name}!")
    except IndexError:
        bot.reply_to(message, "Please provide a name for your pet: /create <name>")

@bot.message_handler(commands = ['status'])
def pet_status(message):
    owner_id = message.from_user.id
    pet = pet_manager.get_pet(owner_id)
    if pet:
        bot.reply_to(message, f"Your pet {pet.name}: Hunger {pet.hunger:.1f}%")
    else:
        bot.reply_to(message, "You don't have a pet! Use /create <name> to create one.")

@bot.message_handler(commands = ['feed'])
def feed_pet(message):
    owner_id = message.from_user.id
    pet = pet_manager.get_pet(owner_id)
    if pet:
        pet.hunger = max(0, pet.hunger - 30)
        pet_manager.save_pets()
        bot.reply_to(message, f"Fed {pet.name}! Current hunger: {pet.hunger:.1f}%")
    else:
        bot.reply_to(message, "You don't have a pet! Use /create <name> to create one.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(update_hunger())
    
    threading.Thread(target=start_polling).start()