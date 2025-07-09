from curses.ascii import HT
import os
import requests
from fastapi import FastAPI, Request, HTTPException
from gigachat import GigaChat
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()
GIGA_API_KEY = os.getenv("GIGA_API_KEY")

SYSTEM_PROMPT = """
Ты - ассистент, который отвечает на вопросы о продуктах компании.
Отвечай на вопросы кратко и понятно.
Ничего не придумывай, используй только информацию из контекста.
Если не знаешь ответа, скажи что ответ не найден и попроси перефразировать вопрос.
Не используй эмоции, смайлики, ссылки.
"""

app = FastAPI()


@app.post("/chat")
async def read_root(request: Request):
    """ Перенаправляет запрос на API. """
    try:
        data = await request.json()
        question = data.get("question")     
        
        try:
            answer = await search_db(question)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))
            
        context = "\n".join([f"{k}: {v}" for k, v in answer.items()])
        prompt = f"{SYSTEM_PROMPT}\n\nВопрос: {question} \n\nКонтекст: {context}"
        
        with GigaChat(credentials=GIGA_API_KEY, model="GigaChat", verify_ssl_certs=False) as chat:
            response = chat.chat(prompt)
            answer = response.choices[0].message.content
            return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def search_db(question: str) -> List[Dict[str, str]]:
    """ Производит поиск по векторной БД. """
    try:
        response = requests.post(f"http://qa-service:6500/search", json={'query': question, 'top': 3})
        return response.json()
    except Exception as e:
        raise ValueError("Ошибка поиска")
    
