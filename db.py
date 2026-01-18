import asyncio
import logging
import sys

from os import getenv
from aiogram import Bot, Dispatcher, html, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram import types
import os
import supabase
from random import randint, shuffle

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext


class WordState(StatesGroup):
    waiting_translation = State()
    word_id = State()
    waiting_word = State()
    waiting_explenation = State()
    count_words = State()
    count_questions = State()

db_router = Router(name='db')
url = 'https://strmitiqeerzvavfdzag.supabase.co'
# 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN0cm1pdGlxZWVyenZhdmZkemFnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM3NDg2OTEsImV4cCI6MjA3OTMyNDY5MX0.HU6OgY-a21mmqxNk0_k67kwuBVU3zrSUtMqR6sOtEa4'
key = os.getenv("DB_TOKEN")
sp_db = supabase.create_client(url,key)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("intfloat/multilingual-e5-large")



print("model loaded")


from sklearn.metrics.pairwise import cosine_similarity

def add_word_data(word):
    
    try:
        word_emb = model.encode(word).tolist()
        response = sp_db.table('words').insert({'word':word, "embedding":word_emb}).execute()
        return response.data[0]["id"]
        
    except Exception as exception:
        return exception

def get_word_data(word=None, id = None):
    try:
        if id:
            response = sp_db.table("words").select('*').eq("id",id).execute()
        else:
            response = sp_db.table("words").select('*').eq("word",word).execute()
        return response
    except Exception as exception:
        return exception

def add_trans_data(trans, word_id, expl = None):
    try:
        trans_emb = model.encode(trans).tolist()
        response = sp_db.table('translation').insert({'trans':trans, 'word_id':word_id, "embedding":trans_emb,"explenation":expl}).execute()
        return response
        
    except Exception as exception:
        return exception

def get_trans_data(word):
    try:

        response = sp_db.table("translation").select('*').eq("trans",word).execute()
        return response
    except Exception as exception:
        return exception
    

def get_all_translations():
    return sp_db.table("translation").select("trans, embedding, explenation").execute().data

def find_similar(trans_word, min_sim=0.7, max_sim=0.98):
    result = []

    base = get_trans_data(trans_word).data
    if not base:
        return []

    base_emb = base[0]["embedding"]

    for t in get_all_translations():
        if t["trans"] == trans_word:
            continue

        sim = cosine_similarity(
            [base_emb],
            [t["embedding"]]
        )[0][0]

        if min_sim < sim < max_sim:
            result.append({
                "trans": t["trans"],
                "explenation": t["explenation"],
                
            })

    
    return result[:3]

def create_test(questions_count = 10):
    result = []
    for i in range(questions_count):    
        test = []
        all_trans = get_all_translations()
        question_obj = get_trans_data(all_trans[randint(0,len(all_trans)-1)]["trans"]).data
        question_trans = question_obj[0]["trans"]
        question = get_word_data(id = question_obj[0]['word_id']).data[0]["word"]
        answers_required = find_similar(question_trans)
        
        shuffle(answers_required)
        answers = []
        

        for i in range(3):
            # question_obj[0]["explenation"]
            answers.append({
                "text": answers_required[i]["trans"],
                "correct": False,
                "explenation": answers_required[i]["explenation"]
            })
        
        corect_expl = question_obj[0]['explenation']
        answers.append({
            "text": question_trans,
            "correct" : True,
            "explenation":  corect_expl
            })
        
        shuffle(answers)
        test.append(question)
        test.append(answers)
        result.append(test)
    return result
        
        
        
        
        


#перевірити find_similar, 4 відповіді в тесті, чергування питань англійських і українських слів

