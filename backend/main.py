import json
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.models.llm_factory import LLMFactory
from src.chat.chat import Chat


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_config():
    config_path = "config.json"
    with open(config_path, "r") as f:
        return json.load(f)
    
class Message(BaseModel):
    content: str
    selectedLLM: str
    vectordb: str
    retrieverType: str

@app.post("/chat/")
async def chat_endpoint(message: Message):
    user_input = message.content

    config = load_config()
    settings = None  
    for item in config["available_settings"]:
        if (
            str(item["selected_approach"]).lower() == str(message.selectedLLM).lower()
            and str(item["vectore_store_type"]).lower() == str(message.vectordb).lower()
        ):
            settings = item
            break  

    print(settings)
    if not settings or settings is None:
        return {"error": "Invalid LLM or vector store type configuration."}

    model = LLMFactory(settings["llm_name"]).get_llm()

    assistant = Chat(
        model=model,
        vectorstore_type="Chroma",
        collection_name="turismo_metadata",
        embedding_model_name="nomic-embed-text",
        retriever_type=message.retrieverType
    )

    async def event_generator():
        try:
            async for letter in assistant.ask_stream(user_input):
                if letter:
                    yield f"data: {json.dumps({'response': letter})}\n\n"
        except Exception as e:
            error_data = json.dumps({'error': str(e)})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
         
        }
    )

@app.post("/process_audio/")
async def process_audio(audio: UploadFile = File(...)):
    import tempfile
    import os
    import whisper
    import subprocess
    
    try:
        transcription_model = whisper.load_model("base", device="cpu")
    except Exception as e:
        transcription_model = None
        print(f"Error loading Whisper model: {e}")

    print("Processing audio file...")
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(await audio.read())
            temp_audio_path = temp_audio.name

        print(f"Temporary audio file saved at: {temp_audio_path}")

        compatible_audio_path = os.path.join(tempfile.gettempdir(), "compatible_audio.wav")
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-i", temp_audio_path,
                    "-ar", "16000", 
                    "-ac", "1", 
                    compatible_audio_path
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"Audio converted to compatible format: {compatible_audio_path}")
        except subprocess.CalledProcessError as ffmpeg_error:
            print(f"Error during FFmpeg conversion: {ffmpeg_error}")
            return JSONResponse(
                content={"error": "Error during audio conversion. Ensure FFmpeg is installed and accessible."},
                status_code=500
            )

        transcription_result = transcription_model.transcribe(compatible_audio_path, fp16=False)
        transcribed_text = transcription_result.get("text", "").strip()

        print(f"Transcription successful: {transcribed_text}")

        os.remove(temp_audio_path)
        os.remove(compatible_audio_path)

        async def event_generator():
            try:
                yield f"data: {json.dumps({'response': transcribed_text, 'type': 'transcription'})}\n\n"
            except Exception as e:
                error_data = json.dumps({'error': str(e)})
                print(f"Error sending transcription: {error_data}")
                yield f"data: {error_data}\n\n"


            try:
                model = LLMFactory("Bedrock").get_llm()
                assistant = Chat(model)
                async for letter in assistant.ask_stream(transcribed_text):
                    if letter:
                        yield f"data: {json.dumps({'response': letter, 'type': 'assistant'})}\n\n"
            except Exception as e:
                error_data = json.dumps({'error': str(e)})
                print(f"Error in assistant response: {error_data}")
                yield f"data: {error_data}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
            }
        )

    except FileNotFoundError as e:
        print(f"File error: {e}")
        return JSONResponse(content={"error": f"File not found: {str(e)}"}, status_code=400)
    except Exception as e:
        print(f"Error processing audio: {e}")
        return JSONResponse(content={"error": f"Error processing audio: {str(e)}"}, status_code=500)
