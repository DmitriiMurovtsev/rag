
import logging
import os
import requests
from fastapi import FastAPI, Request, HTTPException
from gigachat import GigaChat
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()
GIGA_API_KEY = os.getenv("GIGA_API_KEY")

SYSTEM_PROMPT = """
Ты — ассистент, который отвечает на вопросы только на основе базы вопросов и ответов компании.
Не используй внешние знания и не додумывай.
Если в базе совсем нет информации или база пуста, ответь фразой:
«К сожалению, я не нашёл информации по запросу [вопрос] в базе компании.»

Если в базе есть хотя бы частично или тематически релевантная информация, используй её для ответа.
Разрешено использовать данные, содержащие синонимы, переформулировки или близкие по смыслу формулировки.

Не используй смайлики, выделения (жирный, курсив и т.д.) — только чистый текст ответа.
"""

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# логируем в stdout
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

app = FastAPI()


@app.post("/chat")
async def read_root(request: Request):
    """ Перенаправляет запрос на API. """
    try:
        data = await request.json()
        question = data.get("question")     
        
        try:
            answer = await search_db(question)
            if len(answer) == 0:
                return {"answer": f"К сожалению, я не нашёл информации по запросу '{question}' в базе компании."}
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))
            
        context = "\n".join(
            [f"{item['question']}: {item['answer']}" for item in answer]
        )
        prompt = f"{SYSTEM_PROMPT}\nВопрос: {question} \nНайдено в базе знаний: \n{context}"
        logger.info(prompt)
        
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
        logger.info(f'response_text: {response.text}')
        if response.status_code != 200:
            raise ValueError(f"Ошибка поиска: {response.status_code} {response.text}")
        
        return response.json()
    except Exception as e:
        raise ValueError("Ошибка поиска")
    
