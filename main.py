import os
from fastapi import FastAPI, Request
from gigachat import GigaChat
from dotenv import load_dotenv
from typing import Dict

load_dotenv()
GIGA_API_KEY = os.getenv("GIGA_API_KEY")

app = FastAPI()


@app.post("/chat")
async def read_root(request: Request):
    """ Перенаправляет запрос на API """
    try:
        data = await request.json()
        prompt = data.get("prompt")
        
        with GigaChat(credentials=GIGA_API_KEY, model="GigaChat", verify_ssl_certs=False) as chat:
            response = chat.chat(prompt)
            answer = response.choices[0].message.content
            return {"answer": answer}
    except Exception as e:
        return {"error": str(e)}


@app.post("/add_question")
async def add_question(request: Request):
    """ Добавляет вопрос в базу данных """
    try:
        data = await request.json()
        question = data.get("question")
        answer = data.get("answer")
        return {"message": "Question added successfully"}
    except Exception as e:
        return {"error": str(e)}
    
    
async def get_answer(question: str) -> Dict[str, str]:
    """ Отправляет запрос к векторной БД и получает ответ. """
    pass
