import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import openai
import os
import time
import dotenv
import base64 # image encoding
from pydantic import BaseModel

dotenv.load_dotenv()

# APP
app = FastAPI(title="Backend Hackathon Devs Impacto")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OPENAI
# Model
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
client = openai.OpenAI()

# Response model
class DescribePageResponse(BaseModel):
    description: str
    thread_id: str

# ENDPOINTS
@app.get("/")
def health_check():
    """Verifica se o servidor está no ar."""
    return {"status": "ok", "message": "Servidor no ar!"}

@app.post("/describe/")
async def handle_describe_page(
    user_query: str = Form(...),
    image_file: UploadFile = File(...),    
    thread_id: str | None = Form(None)
):
    try:
        if not thread_id:
            thread = client.beta.threads.create()
            thread_id = thread.id
            print("Nova thread criada:", thread_id)
        else:
            print("Usando thread existente:", thread_id)

        print(image_file.filename, image_file.content_type)

        file_content = await image_file.read()
        file = client.files.create(file=io.BytesIO(file_content), purpose="assistants")

        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=[
                {"type": "text", "text": user_query},
                {"type": "image_file", "image_file": {"file_id": file.id}},
            ]
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
        print(f"[Descrever Página] Resposta: '{resposta_texto}'")

        return DescribePageResponse(
            description=resposta_texto,
            thread_id=thread_id
        )
    
    except openai.APIError as e:
        print(f"Erro na API da OpenAI: {e}")
        raise HTTPException(status_code=502, detail=f"Erro na API da OpenAI: {e.message}")
    except Exception as e:
        print(f"Erro interno no servidor: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)