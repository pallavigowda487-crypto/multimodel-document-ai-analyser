import os
import logging

try:
    from moviepy.editor import VideoFileClip
except ImportError:
    from moviepy import VideoFileClip

from utils.audio_processor import extract_text_from_audio

logger = logging.getLogger(__name__)

def extract_audio_from_video(file_path: str) -> str:
    """Extracts audio from video and saves it to a temporary WAV file."""
    audio_path = file_path + ".wav"
    try:
        video = VideoFileClip(file_path)
        # Extract audio and save it
        if video.audio is not None:
            video.audio.write_audiofile(audio_path, logger=None)
        else:
            logger.warning("No audio track found in the video.")
            return None
        video.close()
        return audio_path
    except Exception as e:
        logger.error(f"Error extracting audio from video: {e}")
        return None

def process_video(file_path: str, file_type: str) -> str:
    """
    Routing function for video processing.
    Extracts audio, then passes the audio to the audio_processor for transcription.
    """
    text = ""
    audio_path = extract_audio_from_video(file_path)
    
    if audio_path and os.path.exists(audio_path):
        # Delegate to audio processor
        text = extract_text_from_audio(audio_path)
        # Clean up temporary audio
        try:
            os.remove(audio_path)
        except OSError:
            pass
            
    return text
