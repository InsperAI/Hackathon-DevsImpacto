import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware # Importante para o PWA
import io
import openai
import os
import time
import dotenv
from pydantic import BaseModel

dotenv.load_dotenv()

# APP
app = FastAPI(title="Backend Hackathon Devs Impacto")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens (ok para hackathon)
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, etc)
    allow_headers=["*"],
)

# OPENAI
# Model
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
client = openai.OpenAI()

# Request models
class ChatTextRequest(BaseModel):
    text: str
    thread_id: str | None = None


# Response models
class ChatTextResponse(BaseModel):
    response_text: str
    thread_id: str


@app.get("/")
def health_check():
    """Verifica se o servidor está no ar."""
    return {"status": "ok", "message": "Servidor no ar!"}

@app.post("/chat/")
async def handle_chat(request: ChatTextRequest):
    text = request.text
    thread_id = request.thread_id or ""

    print(f"[Text-to-Text] Recebido texto para thread: {thread_id}")
    print(f"[Text-to-Text] Texto recebido: {text}")

    try:
        if not thread_id:
            thread = client.beta.threads.create()
            thread_id = thread.id
            print("[Text-to-Text] Nova thread criada:", thread_id)
        else:
            print("[Text-to-Text] Usando thread existente:", thread_id)

        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=text
        )

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )

        start_time = time.time()
        while run.status not in ["completed", "failed"]:
            if time.time() - start_time > 30: # Timeout de 30s
                raise HTTPException(status_code=504, detail="Timeout: O Assistente da OpenAI demorou muito para responder.")
            
            time.sleep(0.5)
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        if run.status == "failed":
           print(f"Erro no Run da OpenAI: {run.last_error}")
           raise HTTPException(status_code=500, detail=f"Run falhou: {run.last_error.message}")
        
        messages = client.beta.threads.messages.list(
            thread_id=thread_id,
            order="desc", 
            limit=1       
        )

        resposta_texto = "Erro: Não foi possível obter a resposta."
        if messages.data and messages.data[0].content[0].type == "text":
            resposta_texto = messages.data[0].content[0].text.value
        
        print(f"[Agente/Memória] Resposta: '{resposta_texto}'")

        return ChatTextResponse(
            response_text=resposta_texto,
            thread_id=thread_id # Retorna o ID para o Postman/PWA
        )
    
    except openai.APIError as e:
        print(f"Erro na API da OpenAI: {e}")
        raise HTTPException(status_code=502, detail=f"Erro na API da OpenAI: {e.message}")
    except Exception as e:
        print(f"Erro interno no servidor: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {str(e)}")
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)