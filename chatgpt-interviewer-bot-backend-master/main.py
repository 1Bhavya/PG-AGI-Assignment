from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import openai
import os
import json
import requests

load_dotenv()

openai.api_key = os.getenv("OPEN_AI_KEY")
elevenlabs_key = os.getenv("ELEVENLABS_KEY")

app = FastAPI()

# CORS settings to allow requests from specific frontend origins
origins = [
    "http://localhost:5174",  # Add your frontend server's URL here
    "http://localhost:5173",  # Add your frontend server's URL here
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Make sure this is correct
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Post endpoint to handle audio input
@app.post("/talk")
async def post_audio(file: UploadFile):
    user_message = transcribe_audio(file)
    chat_response = get_chat_response(user_message)
    audio_output = text_to_speech(chat_response)

    # Streaming audio back to the frontend
    def iterfile():
        yield audio_output

    return StreamingResponse(iterfile(), media_type="application/octet-stream")

# Endpoint to clear chat history
@app.get("/clear")
async def clear_history():
    file = 'database.json'
    open(file, 'w')
    return {"message": "Chat history has been cleared"}

# Helper function to transcribe audio using OpenAI Whisper API
def transcribe_audio(file):
    # Save the audio file to disk first
    with open(file.filename, 'wb') as buffer:
        buffer.write(file.file.read())
    
    # Open the file for reading
    with open(file.filename, "rb") as audio_file:
        # Use the Whisper API for transcription
        transcript = openai.Audio.transcribe(
            model="whisper-1", 
            file=audio_file
        )
    
    print(transcript)  # Optional: Debugging
    return transcript

# Helper function to get a response from GPT model
def get_chat_response(user_message):
    messages = load_messages()
    messages.append({"role": "user", "content": user_message['text']})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        parsed_response = response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "Error: Unable to get a response from the AI."

    save_messages(user_message['text'], parsed_response)
    return parsed_response

# Function to load chat history from the database
def load_messages():
    messages = []
    file = 'database.json'

    empty = os.stat(file).st_size == 0

    if not empty:
        with open(file) as db_file:
            data = json.load(db_file)
            for item in data:
                messages.append(item)
    else:
        # Default system message
        messages.append(
            {"role": "system", "content": "You are interviewing the user for a front-end React developer position. Ask short questions that are relevant to a junior level developer. Your name is Greg. The user is Travis. Keep responses under 30 words and be funny sometimes."}
        )
    return messages

# Function to save chat history to the database
def save_messages(user_message, gpt_response):
    file = 'database.json'
    try:
        messages = load_messages()
        messages.append({"role": "user", "content": user_message})
        messages.append({"role": "assistant", "content": gpt_response})
        with open(file, 'w') as f:
            json.dump(messages, f)
    except Exception as e:
        print(f"Error saving messages: {e}")

# Helper function for text-to-speech using Eleven Labs API
def text_to_speech(text):
    voice_id = 'pNInz6obpgDQGcFmaJgB'  # Your Eleven Labs voice ID
    
    body = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0,
            "similarity_boost": 0,
            "style": 0.5,
            "use_speaker_boost": True
        }
    }

    headers = {
        "Content-Type": "application/json",
        "accept": "audio/mpeg",
        "xi-api-key": elevenlabs_key
    }

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    try:
        response = requests.post(url, json=body, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            print('Error in Eleven Labs API response')
            return None
    except Exception as e:
        print(f"Error calling Eleven Labs API: {e}")
        return None

# Test message for GPT response
test_message = {"text": "What is React?"}
response = get_chat_response(test_message)
print(f"Response: {response}")

