# -*- coding: utf-8 -*-
"""
Discord Bot

Using https://github.com/Rapptz/discord.py installed from source
API: http://discordpy.readthedocs.io/en/latest/api.html

@author: drkatnz
"""

import discord
import sys
import random

import quiz
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
quiz = quiz.Quiz(client)

@client.event
async def on_ready():
    print('Logged in as: ' + client.user.name)
    print('User ID: ' + str(client.user.id))
    print('------')

@client.event
async def on_message(message):
    if message.content.startswith('!logoff'):
        await message.channel.send('Leaving server. BYE!')
        await client.close()
        exit()
        
    elif (message.content.startswith('!halt') or 
          message.content.startswith('!salir')):
        await quiz.stop()
    elif (message.content.startswith('!reset')):
        await quiz.reset()        
    elif (message.content.startswith('!quiz') or 
          message.content.startswith('!ask')):
        await quiz.start(message.channel)      
    elif (message.content.startswith('!scores')):
        await quiz.print_scores()    
    elif (message.content.startswith('!next')):
        await quiz.next_question(message.channel)
    elif message.content.startswith('!img'):
        with open(f'imagenes/infografia.png', 'rb') as f:
            # ¡Vamos a almacenar el archivo de la biblioteca Discord convertido en esta variable!
            picture = discord.File(f)
        # A continuación, podemos enviar este archivo como parámetro.
        await message.channel.send(file=picture)
    elif quiz is not None and quiz.started():
        #check if we have a question pending
        await quiz.answer_question(message)
        #check quiz question correct


#run the program!
if __name__ == "__main__":
    
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    BOT_TOKEN = "TOKEN"
    
    # logs into channel    
    try:
        client.run(BOT_TOKEN)
    except Exception as e:        
        print(f"Error: {e}")
        client.close()
