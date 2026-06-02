from typing import Dict, List, Optional, Any, TypedDict
import whisper
import yt_dlp
import os
import sqlite3
import json
from datetime import datetime

from openai.resources.audio import Transcriptions


class TranscriptSegment(TypedDict):
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: List[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float


class VideoInfo(TypedDict):
    title: str
    embed_url: str
    duration: int
    transcript: List[TranscriptSegment]


Transcriptions_CACHE_DB = './data/transcriptions.db'

def init_database() -> None:
    """
    Initializes the SQLite database and creates the necessary table if it doesn't exist.
    """
    conn: sqlite3.Connection = sqlite3.connect(Transcriptions_CACHE_DB)
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transcriptions (
            video_id TEXT PRIMARY KEY,
            title TEXT,
            embed_url TEXT,
            duration INTEGER,
            transcript TEXT,
            created_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def get_transcription_from_db(video_id: str) -> Optional[VideoInfo]:
    """
    Retrieves transcription from a database for a given video_id.

    Args:
        video_id: The YouTube video ID.

    Returns:
        Dictionary containing video information and transcript if found, None otherwise.
    """
    conn: sqlite3.Connection = sqlite3.connect(Transcriptions_CACHE_DB)
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute('SELECT * FROM transcriptions WHERE video_id = ?', (video_id,))
    result: Optional[tuple] = cursor.fetchone()
    conn.close()

    if result:
        return {
            'title': result[1],
            'embed_url': result[2],
            'duration': result[3],
            'transcript': json.loads(result[4])
        }
    return None


def save_transcription_to_db(video_id: str, video_info: VideoInfo) -> None:
    """
    Saves transcription data to a database.

    Args:
        video_id: The YouTube video ID
        video_info: Dictionary containing video information and transcript
    """
    conn: sqlite3.Connection = sqlite3.connect(Transcriptions_CACHE_DB)
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO transcriptions 
        (video_id, title, embed_url, duration, transcript, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        video_id,
        video_info['title'],
        video_info['embed_url'],
        video_info['duration'],
        json.dumps(video_info['transcript']),
        datetime.now()
    ))
    conn.commit()
    conn.close()


def transcribe_youtube_video(url: str) -> Optional[VideoInfo]:
    """
    Transcribes a YouTube video using Whisper, with database caching.

    Args:
        url: The URL of the YouTube video.

    Returns:
        A dictionary containing video information and transcript segments, or None if an error occurs.
    """
    try:
        # Initialize database
        init_database()

        # Extract video ID and check database first
        ydl_opts: Dict[str, Any] = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info: Dict[str, Any] = ydl.extract_info(url, download=False)

        video_id: str = info.get('id', '')

        # Check if transcription exists in a database
        cached_result: Optional[VideoInfo] = get_transcription_from_db(video_id)
        if cached_result:
            print("Retrieved transcription from database cache")
            return cached_result

        # If not in the database, proceed with transcription
        model: Any = whisper.load_model("base")

        embed_url: str = f"https://www.youtube.com/embed/{video_id}"
        video_info: VideoInfo = {
            'title': info.get('title', ''),
            'embed_url': embed_url,
            'duration': info.get('duration', 0),
            'transcript': []  # Will be populated after transcription
        }

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'outtmpl': 'temp_audio'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        result: Dict[str, Any] = model.transcribe('temp_audio.wav')

        video_info['transcript'] = result['segments']

        # Clean up a temporary audio file
        if os.path.exists('temp_audio.wav'):
            os.remove('temp_audio.wav')

        # Save result to a database
        save_transcription_to_db(video_id, video_info)
        print("Saved new transcription to database")

        return video_info

    except Exception as e:
        print(f"Failed to process YouTube URL: {str(e)}")
        return None
