import streamlit as st
from dotenv import load_dotenv
import google.generativeai as gen_ai
import speech_recognition as sr
from gtts import gTTS
import os
from io import BytesIO
from audio_recorder_streamlit import audio_recorder

# Loading environment variables 
load_dotenv()

# Configure page settings
st.set_page_config(page_title="Intelligent Voice Chatbot", layout="wide", page_icon="👾")

# Using custom CSS for designing the webpage
st.markdown(
    """
    <style>
    body {
        background-color: #FAF3E0; /* Warmer background color */
    }
    .title {
        color: lightskyblue; /* Lighter text color */
        font-size: 45px;
        text-align: center;
        font-family: verdana;
    }
    .user-message {
        background-color: #cce5ff; /* Light blue background for user messages */
        color: #003366; /* Dark blue text color */
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .assistant-message {
        background-color: #e6ffe6; /* Light green background for assistant messages */
        color: #004d00; /* Dark green text color */
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    </style>
    <h1><p class="title">🎯<b><i> Gemini AI Voice Chatbot</i></b> 🎯</p></h1>
    """,
    unsafe_allow_html=True
)

# Create a speech-to-text conversion
def speech_to_text(audio_path):
    r = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = r.record(source)
        try:
            return r.recognize_google(audio_data)
        except sr.UnknownValueError:
            return "Sorry, I did not understand that."
        except sr.RequestError:
            return "Sorry, the service is unavailable at the moment."

# Setting up Google API key from env
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

# Initializing a session state for conversation history
if "conversation" not in st.session_state:
    st.session_state.conversation = []
    st.session_state.first_interaction = True

# Converting chat history format
def convert_history(history):
    converted = []
    for role, text in history:
        if role == "user":
            converted.append({"parts": [{"text": text}], "role": "user"})
        elif role == "model":
            converted.append({"parts": [{"text": text}], "role": "model"})
    return converted

# Adding the welcome message to conversation history if not already added
if st.session_state.first_interaction:
    welcome_message = "Hello! Welcome to Gemini Chatbot! How may I help you today?"
    st.session_state.conversation.append(("model", welcome_message))
    
    # Generate and play the welcome message
    tts_welcome = gTTS(text=welcome_message, lang='en')
    welcome_audio = BytesIO()
    tts_welcome.write_to_fp(welcome_audio)
    welcome_audio.seek(0)
    
    # Play the welcome audio
    st.audio(welcome_audio, format="audio/mp3")

    st.session_state.first_interaction = False

# Displaying the conversation history
for role, text in st.session_state.conversation:
    if role == "user":
        st.markdown(f'<div class="user-message">{text}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-message">{text}</div>', unsafe_allow_html=True)

# Creating a sidebar for microphone button
with st.sidebar:
    audio_data = audio_recorder()

# Processing the audio data
if audio_data:
    st.write("Processing audio...")

    with BytesIO(audio_data) as audio_file:
        # Save audio data to a temporary file
        temp_audio_path = "temp_audio.wav"
        with open(temp_audio_path, "wb") as f:
            f.write(audio_file.read())

        user_prompt = speech_to_text(temp_audio_path)

        # Add user's question to chat and display it
        st.session_state.conversation.append(("user", user_prompt))
        st.markdown(f'<div class="user-message">{user_prompt}</div>', unsafe_allow_html=True)

        # Send user's question to Gemini-Pro and get answer
        conversation_history = convert_history(st.session_state.conversation)
        try:
            chat_session = model.start_chat(history=conversation_history)
            gemini_answer = chat_session.send_message(user_prompt)

            # Display and voice the answer
            st.session_state.conversation.append(("model", gemini_answer.text))
            st.markdown(f'<div class="assistant-message">{gemini_answer.text}</div>', unsafe_allow_html=True)

            # Generate and play TTS response
            tts_response = gTTS(text=gemini_answer.text, lang='en')
            response_audio = BytesIO()
            tts_response.write_to_fp(response_audio)
            response_audio.seek(0)
            st.audio(response_audio, format="audio/mp3")
        except Exception as e:
            st.error(f"An error occurred: {e}")
            