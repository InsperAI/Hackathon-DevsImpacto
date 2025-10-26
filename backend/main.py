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
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
PROMPT = os.getenv("PROMPT")
client = openai.OpenAI()

# Response model
class DescribePageResponse(BaseModel):
    description: str

# FUNCTIONS AND HELPERS

async def transcribe(audio_file: UploadFile = File(...)):
    try:
        audio_data = await audio_file.read()
        audio_stream = io.BytesIO(audio_data)
        audio_stream.name = "audio.mpeg"

        transcription = client.audio.transcriptions.create(
            file=audio_stream,
            model="whisper-1",
            response_format="text",
            language="pt"
        )

        return transcription

    except openai.APIError as e:
        raise HTTPException(status_code=502, detail=f"Erro na API da OpenAI: {e.message}")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler o arquivo de áudio: {str(e)}")
    
async def text_to_speech(text_input: str):
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="fable",
            input=text_input,
            response_format="mp3"
        )

        return response.content

    except openai.APIError as e:
        raise HTTPException(status_code=502, detail=f"Erro na API da OpenAI: {e.message}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na síntese de voz: {str(e)}")

# ENDPOINTS
@app.get("/")
def health_check():
    """Verifica se o servidor está no ar."""
    return {"status": "ok", "message": "Servidor no ar!"}

@app.post("/describe/")
async def handle_describe_page(
    audio_file: UploadFile = File(...),
    image_file: UploadFile = File(...),    
):
    try:
        file = image_file.file.read()
        base64_image = base64.b64encode(file).decode('utf-8')

        user_query = await transcribe(audio_file)
        #user_query = "O que há nesta página?"

        response = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system",
                 "content": PROMPT},
                {"role": "user",
                 "content": [
                     {"type": "input_text",
                      "text": str(user_query),
                     },
                     {"type": "input_image",
                      "image_url": f"data:{image_file.content_type};base64,{base64_image}",
                     }
                 ]
                }
            ]
        )

        audio_bytes = await text_to_speech(response.output_text)

        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mp3")
    
    except openai.APIError as e:
        print(f"Erro na API da OpenAI: {e}")
        raise HTTPException(status_code=502, detail=f"Erro na API da OpenAI: {e.message}")
    except Exception as e:
        print(f"Erro interno no servidor: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)