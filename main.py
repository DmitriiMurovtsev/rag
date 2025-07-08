import os
from fastapi import FastAPI, Request
from gigachat import GigaChat
from dotenv import load_dotenv

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
            answer = chat.chat(prompt)
            return {"answer": answer}
    except Exception as e:
        return {"error": str(e)}

