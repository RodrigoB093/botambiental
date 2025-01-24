# -*- coding: utf-8 -*-
"""
Clases de Quiz / Pregunta para quizbot.

@autor: drkatnz
"""

import asyncio
import random
import re
import os

#todo: probablemente necesito eliminar la puntuación de las respuestas



class Quiz:
    
    def __init__(self, client, win_limit=10, hint_time=30):
        #inicializa el quiz
        self.__running = False
        self.current_question = None
        self._win_limit = win_limit
        self._hint_time = hint_time
        self._questions = []
        self._asked = []
        self.scores = {}
        self._client = client
        self._quiz_channel = None
        self._cancel_callback = True
       
        
        #cargar algunas preguntas
        datafiles = os.listdir('quizdata')
        for df in datafiles:
            filepath = 'quizdata' + os.path.sep + df
            self._load_questions(filepath)
            print('Cargado: ' + filepath)
        print('Carga de datos del quiz completada.\n')
        
    
    
    def _load_questions(self, question_file):
        # carga las preguntas para el quiz
        with open(question_file, encoding='utf-8',errors='replace') as qfile:
            lines = qfile.readlines()
            
        question = None
        category = None
        answer = None      
        regex = None
        position = 0
        
        while position < len(lines):
            if lines[position].strip().startswith('#'):
                #saltar
                position += 1
                continue
            if lines[position].strip() == '': #línea en blanco
                #agregar pregunta
                if question is not None and answer is not None:
                    q = Question(question=question, answer=answer, 
                                 category=category, regex=regex)
                    self._questions.append(q)
                    
                #reiniciar todo
                question = None
                category = None
                answer = None
                regex = None
                position += 1
                continue
                
            if lines[position].strip().lower().startswith('category'):
                category = lines[position].strip()[lines[position].find(':') + 1:].strip()
            elif lines[position].strip().lower().startswith('question'):
                question = lines[position].strip()[lines[position].find(':') + 1:].strip()
            elif lines[position].strip().lower().startswith('answer'):
                answer = lines[position].strip()[lines[position].find(':') + 1:].strip()
            elif lines[position].strip().lower().startswith('regexp'):
                regex = lines[position].strip()[lines[position].find(':') + 1:].strip()
            #de lo contrario, ignorar
            position += 1
                
    
    def started(self):
        #averigua si hay un quiz en marcha
        return self.__running
    
    
    def question_in_progress(self):
        #averigua si hay una pregunta en curso
        return self.__current_question is not None
    
    
    async def _hint(self, hint_question, hint_number):
        #ofrece una pista al usuario
        if self.__running and self.current_question is not None:
            await asyncio.sleep(self._hint_time)
            if (self.current_question == hint_question 
                 and self._cancel_callback == False):
                if (hint_number >= 5):
                    await self.next_question(self._channel)
                
                hint = self.current_question.get_hint(hint_number)
                await self._client.get_channel(self._channel.id).send('Pista {}: {}'.format(hint_number, hint))
                if hint_number < 5:
                    await self._hint(hint_question, hint_number + 1) 
    
    
    async def start(self, channel):
        #comienza el quiz en el canal dado.
        if self.__running:
            #no empezar de nuevo
            await self._client.get_channel(channel.id).send(
             'Quiz ya comenzado en el canal {}, puedes detenerlo con !stop o !halt'.format(self._channel.name))
        else:
            await self.reset()
            self._channel = channel
            await self._client.get_channel(self._channel.id).send('@here El quiz comenzará en 10 segundos...')
            await asyncio.sleep(10)
            self.__running = True
            await self.ask_question()
            
            
    async def reset(self):
        if self.__running:
            #detener
            await self.stop()
        
        #reiniciar las puntuaciones
        self.current_question = None
        self._cancel_callback = True
        self.__running = False
        self._questions.append(self._asked)
        self._asked = []
        self.scores = {}
            
            
    async def stop(self):
        #detiene el quiz
        if self.__running:
            #imprimir resultados
            #detener quiz
            await self._client.get_channel(self._channel.id).send('Deteniendo el quiz.')
            if(self.current_question is not None):
                await self._client.get_channel(self._channel.id).send(
                     'La respuesta a la pregunta actual es: {}'.format(self.current_question.get_answer()))
            await self.print_scores()
            self.current_question = None
            self._cancel_callback = True
            self.__running = False
        else:
            await self._client.get_channel(self._channel.id).send('No hay un quiz en marcha, comienza uno con !ask o !quiz')
            
    
    async def ask_question(self):
        #hace una pregunta en el quiz
        if self.__running:
            #agarrar una pregunta al azar
            qpos = random.randint(0,len(self._questions) - 1)
            self.current_question = self._questions[qpos]
            self._questions.remove(self.current_question)
            self._asked.append(self.current_question)
            await self._client.get_channel(self._channel.id).send(
             'Pregunta {}: {}'.format(len(self._asked), self.current_question.ask_question()))
            self._cancel_callback = False
            await self._hint(self.current_question, 1)
            
            
    async def next_question(self, channel):
        #pasa a la siguiente pregunta
        if self.__running:
            if channel == self._channel:
                await self._client.get_channel(self._channel.id).send(
                         'Pasando a la siguiente pregunta. La respuesta que buscaba era: {}'.format(self.current_question.get_answer()))
                self.current_question = None
                self._cancel_callback = True
                await self.ask_question()
            
            
            
    async def answer_question(self, message):
        #verifica la respuesta a una pregunta
        if self.__running and self.current_question is not None:
            if message.channel != self._channel:
                pass
            
            if self.current_question.answer_correct(message.content):
                #registrar éxito
                self._cancel_callback = True
                
                if message.author.name in self.scores:
                    self.scores[message.author.name] += 1
                else:
                    self.scores[message.author.name] = 1
                               
                await self._client.get_channel(self._channel.id).send(
                 'Bien hecho, {}, la respuesta correcta era: {}'.format(message.author.name, self.current_question.get_answer()))
                self.current_question = None
                
                #verificar victoria
                if self.scores[message.author.name] == self._win_limit:
                    
                    await self.print_scores()
                    await self._client.get_channel(self._channel.id).send('{} ha ganado! Felicitaciones.'.format(message.author.name))
                    self._questions.append(self._asked)
                    self._asked = []
                    self.__running = False                    
                
                #¿imprimir totales?
                elif len(self._asked) % 5 == 0:
                    await self.print_scores()                    
                
                    
                await self.ask_question()
                
                
                
                
    async def print_scores(self):
        #imprime una tabla de puntuaciones.
        if self.__running:
            await self._client.get_channel(self._channel.id).send('Resultados actuales del quiz:')
        else:
            await self._client.get_channel(self._channel.id).send('Resultados más recientes del quiz:')
            
        highest = 0
        for name in self.scores:
            await self._client.get_channel(self._channel.id).send('{}:\t{}'.format(name,self.scores[name]))
            if self.scores[name] > highest:
                highest = self.scores[name]
                
        if len(self.scores) == 0:
            await self._client.get_channel(self._channel.id).send('No hay resultados para mostrar.')
                
        leaders = []
        for name in self.scores:
            if self.scores[name] == highest:
                leaders.append(name)
                
        if len(leaders) > 0:
            if len(leaders) == 1:
                await self._client.get_channel(self._channel.id).send('Líder actual: {}'.format(leaders[0]))
            else:
                await self._client.get_channel(self._channel.id).send('Líderes actuales: {}'.format(leaders))
        
            
    
    
    
class Question:
    # Una pregunta en un quiz
    def __init__(self, question, answer, category=None, author=None, regex=None):
        self.question = question
        self.answer = answer
        self.author = author
        self.regex = regex
        self.category = category
        self._hints = 0

        
        
    def ask_question(self):
        # obtiene una versión bien formateada de la pregunta.
        question_text = ''
        if self.category is not None:
            question_text+='({}) '.format(self.category)
        else:
            question_text+='(General) '
        if self.author is not None:
            question_text+='Formulada por {}. '.format(self.author)
        question_text += self.question
        return question_text
    
    
    def answer_correct(self, answer):
        #verifica si una respuesta es correcta o no.
        
        #debería verificar regex
        if self.regex is not None:
            match = re.fullmatch(self.regex.strip(),answer.strip())
            return match is not None
            
        #de lo contrario, solo coincidir cadenas
        return  answer.lower().strip() == self.answer.lower().strip()
    
    
    def get_hint(self, hint_number):
        # obtiene una pista formateada para la pregunta
        hint = []
        for i in range(len(self.answer)):
            if i % 5 < hint_number:
                hint = hint + list(self.answer[i])
            else:
                if self.answer[i] == ' ':
                    hint += ' '
                else:
                    hint += '-'
                    
        return ''.join(hint)
        
    
    def get_answer(self):
        # obtiene la respuesta esperada
        return self.answer
