import json
import logging
import os
import sqlite3

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

# Define an absolute path for logs directory at project root level
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
# Create a logs directory if it doesn't exist
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure logging
def setup_logging():
    # Create a logger
    logger = logging.getLogger('quiz_generator')

    # Return an existing logger if it's already configured
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Create a file handler for all logs with fixed filename using an absolute path
    log_file = os.path.join(LOGS_DIR, 'quiz_generator.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    # Create a console handler with a higher log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatters and add them to the handlers
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Initialize logger
logger = setup_logging()


def get_module_text(module: dict) -> str:
    """
    Extract and combine all text content from a module's JSON structure.

    Args:
        module (dict): Module dictionary containing 'title' and 'content' fields

    Returns:
        str: Combined text content of the module
    """
    if not isinstance(module, dict):
        return ""

    # Initialize with the title if present
    text_parts = [module.get('title', '')] if module.get('title') else []

    # Process content array if it exists
    content = module.get('content', [])
    if content and isinstance(content, list):
        # Extract text from each content segment
        for segment in content:
            if isinstance(segment, dict) and 'text' in segment:
                text_parts.append(segment['text'])

    # Join all parts with space
    return ' '.join(text_parts).strip()


# Cache database path
QUIZ_CACHE_DB = '../../common/data/quizes.db'

class QuizCache:
    def __init__(self, cache_path: str = QUIZ_CACHE_DB):
        self.cache_path = Path(cache_path)
        self.init_table()


    def init_table(self):
        """Initialize the SQLite database for caching quiz questions"""
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS module_questions (
                video_id TEXT,
                module_title TEXT,
                difficulty TEXT,
                questions TEXT,
                created_at TIMESTAMP,
                PRIMARY KEY (video_id, module_title)
            )
        ''')
        conn.commit()
        conn.close()

    def get_cached_quiz(self, video_id: str, module_title: str) -> Optional[List[Dict]]:
        """Retrieve cached quiz questions for a given topic and difficulty"""
        conn = sqlite3.connect(QUIZ_CACHE_DB)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT questions FROM module_questions WHERE video_id = ? AND module_title = ?',
            (video_id, module_title)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            return json.loads(result[0])
        return None

    def save_quiz_to_cache(self, video_id: str, module_title: str,
                           difficulty: str, questions: List[Dict]):
        """Save generated quiz questions to cache"""
        conn = sqlite3.connect(QUIZ_CACHE_DB)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO module_questions 
            (video_id, module_title, difficulty, questions, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            video_id,
            module_title,
            difficulty,
            json.dumps(questions),
            datetime.now()
        ))
        conn.commit()
        conn.close()
