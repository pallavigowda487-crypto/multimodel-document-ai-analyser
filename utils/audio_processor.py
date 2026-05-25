import speech_recognition as sr
import logging
from pydub import AudioSegment
import os

logger = logging.getLogger(__name__)

def convert_audio_to_wav(file_path: str) -> str:
    """Converts audio file to WAV format required by SpeechRecognition."""
    try:
        audio = AudioSegment.from_file(file_path)
        wav_path = file_path + "_converted.wav"
        audio.export(wav_path, format="wav")
        return wav_path
    except Exception as e:
        logger.error(f"Error converting audio to wav: {e}")
        return file_path

def extract_text_from_audio(file_path: str) -> str:
    """
    Extracts text from audio using SpeechRecognition (Google Web Speech API).
    """
    text = ""
    wav_path = file_path
    
    # Check if we need to convert to wav
    if not file_path.lower().endswith(".wav"):
        wav_path = convert_audio_to_wav(file_path)
        
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_path) as source:
            # Adjust for ambient noise and read the entire audio file
            recognizer.adjust_for_ambient_noise(source)
            audio_data = recognizer.record(source)
            
            # Use Google's public speech recognition for free tier compatibility
            # Note: For production with larger files, an API like Whisper should be used.
            text = recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        logger.warning("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        logger.error(f"Could not request results from Google Speech Recognition service; {e}")
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
    finally:
        # Cleanup temporary wav file if we created one
        if wav_path != file_path and os.path.exists(wav_path):
            os.remove(wav_path)
            
    return text.strip()

def process_audio(file_path: str, file_type: str) -> str:
    """Routing function for audio processing."""
    return extract_text_from_audio(file_path)
