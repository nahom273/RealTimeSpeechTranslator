import os
import pygame
from gtts import gTTS
import streamlit as st
import speech_recognition as sr
from googletrans import LANGUAGES, Translator
import time

# Global variable to control the translation loop
isTranslateOn = False
captured_audio = None

# Initialize the translator and sound mixer
translator = Translator()
pygame.mixer.init()

# Create a mapping between language names and language codes
language_mapping = {name.capitalize(): code for code, name in LANGUAGES.items()}

# Main content of the app
st.markdown(
    """
    <h1 style='text-align: center; color:#655194; padding-bottom: 30px;'>
        Real-time Speech Translation
    </h1>
    """,
    unsafe_allow_html=True
)

# Get dynamic values from the webpage
# Page layout
col1, col2 = st.columns([0.3, 0.7])

with col1:
    with st.expander("**Settings**", expanded=True):
        pause_threshold = st.slider("Pause Threshold", min_value=0.5, max_value=3.0, value=1.0, step=0.1)
        phrase_time_limit = st.number_input("Phrase Time Limit (seconds)", min_value=1, max_value=60, value=10, step=1)

# Dropdown menus for language selection
capitalized_languages = {code: name.capitalize() for code, name in LANGUAGES.items()}
with col2:
    with st.expander("**Select Language**", expanded=True):
        from_language_name = st.selectbox("Select Source Language:", list(capitalized_languages.values()))
        to_language_name = st.selectbox("Select Target Language:", list(capitalized_languages.values()))

        # Buttons to start and stop the translation process
        st.markdown("""
            <style>
            .button-container {
                display: flex;
                justify-content: space-between;
            }
            .stButton button {
                background-color: #655194; /* Button color */
                color: white;
                padding: 10px 21px;
                text-decoration: none;
                font-size: 16px;
                margin: 4px;
                cursor: pointer;
                border-radius: 4px;
            }
            </style>
            """, unsafe_allow_html=True)

        # Container for buttons
        st.markdown('<div class="button-container">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            start_button = st.button("Start")
        with col2:
            translate_button = st.button("Translate")
        with col3:
            stop_button = st.button("Stop")
        st.markdown('</div>', unsafe_allow_html=True)


def get_language_code(language_name):
    """Get the language code from the language name."""
    return language_mapping.get(language_name, language_name)


def translate_text(text, from_language, to_language):
    """Translate text from one language to another."""
    translation = translator.translate(text, src=from_language, dest=to_language)
    return translation.text


def text_to_speech(text, language_code):
    """Convert text to speech and play it."""
    tts = gTTS(text=text, lang=language_code, slow=False)
    tts.save("temp_audio.mp3")
    audio = pygame.mixer.Sound("temp_audio.mp3")
    audio.play()
    while pygame.mixer.get_busy():
        continue
    os.remove("temp_audio.mp3")  # Remove the temporary audio file


def listen_and_capture():
    """Listen to audio and capture it."""
    global captured_audio
    rec = sr.Recognizer()
    status_placeholder = st.empty()  # Placeholder for status updates

    with sr.Microphone() as source:
        with st.spinner("Listening..."):
            rec.pause_threshold = pause_threshold
            captured_audio = rec.listen(source, phrase_time_limit=phrase_time_limit)
    try:
        status_placeholder.text("Processing...")
        progress_bar = st.progress(0)

        spoken_text = rec.recognize_google(captured_audio, language=from_language)
        progress_bar.progress(50)  # Update progress bar to 50%

        status_placeholder.text("Captured successfully!")
        progress_bar.progress(100)  # Update progress bar to 100%

        status_placeholder.empty()
        progress_bar.empty()  # Clear the status placeholder after completion

        return spoken_text

    except sr.UnknownValueError:
        status_placeholder.markdown(
            "<span style='color:red'>Sorry, I could not understand the audio. Please speak clearly and loudly.</span>",
            unsafe_allow_html=True)
        progress_bar.empty()
        time.sleep(2)  # Wait for some time before resuming listening
        status_placeholder.empty()  # Clear the error message before listening again
        return None
    except sr.RequestError as e:
        status_placeholder.markdown(f"<span style='color:red'>Error with the speech recognition service: {e}</span>",
                                    unsafe_allow_html=True)
        progress_bar.empty()
        time.sleep(2)  # Wait for some time before resuming listening
        status_placeholder.empty()  # Clear the error message before listening again
        return None
    except Exception as e:
        status_placeholder.markdown(f"<span style='color:red'>Error during processing or translation: {e}</span>",
                                    unsafe_allow_html=True)
        progress_bar.empty()
        time.sleep(2)  # Wait for some time before resuming listening
        status_placeholder.empty()  # Clear the error message before listening again
        return None


# Convert language names to codes
from_language = get_language_code(from_language_name)
to_language = get_language_code(to_language_name)

# Placeholder for displaying the translated text
translated_text_placeholder = st.empty()

# Start translation process when "Start" button is clicked
if start_button:
    if not isTranslateOn:
        isTranslateOn = True
        while isTranslateOn:
            listen_and_capture()
            time.sleep(2)  # Wait for some time before resuming listening

# Translate when "Translate" button is clicked
if translate_button:
    isTranslateOn = False
    if captured_audio:
        rec = sr.Recognizer()
        try:

            spoken_text = rec.recognize_google(captured_audio, language=from_language)
            translated_text = translate_text(spoken_text, from_language, to_language)
            text_to_speech(translated_text, to_language)
            translated_text_placeholder.markdown(f"<h3>Translated Text:</h3><p>{translated_text}</p>",
                                                 unsafe_allow_html=True)
        except Exception as e:
            translated_text_placeholder.markdown(
                f"<span style='color:red'>Error during processing or translation: {e}</span>", unsafe_allow_html=True)
    time.sleep(2)  # Wait for some time before resuming listening
    isTranslateOn = True
    while isTranslateOn:
        listen_and_capture()
        time.sleep(2)

# Stop translation process when "Stop" button is clicked
if stop_button:
    isTranslateOn = False
