
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
Ты — ассистент, который отвечает на вопросы только на основе предоставленных фрагментов из базы знаний компании.
Не используй внешние знания. Если в контексте нет ответа на вопрос, просто скажи, что не нашёл информации в базе компании. Именно так. Не в контексте.
Не используй эмоции, смайлики, ссылки.
И если ответ есть, отвечай максимально точно по ответу.
"""

logger = logging.getLogger(__name__)

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
            
        context = "\n".join(
            [f"{item['question']}: {item['answer']}" for item in answer]
        )
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
        logger.info(f'response_text: {response.text}')
        if response.status_code != 200:
            raise ValueError(f"Ошибка поиска: {response.status_code} {response.text}")
        
        return response.json()
    except Exception as e:
        raise ValueError("Ошибка поиска")
    
