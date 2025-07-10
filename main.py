
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

Если совсем ничего не найдено:
«К сожалению, я не нашёл информации по запросу [вопрос] в базе компании.»

Однако, если база содержит хотя бы одну частично или тематически релевантную запись (например, синоним, переформулировку, близкий по смыслу запрос), используй её для ответа на вопрос.

Отвечай только на основе приведённой информации из базы знаний. Не придумывай дополнительного текста.

ВАЖНО:
- Все имена, цифры, термины и факты нужно использовать **точно так, как они есть** в базе, без изменений.
- Не выдумывай и не переформулируй их.
- Имена, Фамилии и Отчества используй как есть без изменений. Имя Сагима - это женское имя.
- Объединяй несколько найденных ответов аккуратно, создавая связный текст.

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
    
