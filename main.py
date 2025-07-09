import os
from fastapi import FastAPI, Request
from gigachat import GigaChat
from dotenv import load_dotenv
from typing import Dict

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
           
        answer = await search_db(question)
        context = "\n".join([f"{k}: {v}" for k, v in answer.items()])
        prompt = f"{SYSTEM_PROMPT}\n\nВопрос: {question} \n\nКонтекст: {context}"
        
        with GigaChat(credentials=GIGA_API_KEY, model="GigaChat", verify_ssl_certs=False) as chat:
            response = chat.chat(prompt)
            answer = response.choices[0].message.content
            return {"answer": answer}
    except Exception as e:
        return {"error": str(e)}


async def search_db(question: str) -> Dict[str, str]:
    """ Производит поиск по векторной БД. """
    pass
