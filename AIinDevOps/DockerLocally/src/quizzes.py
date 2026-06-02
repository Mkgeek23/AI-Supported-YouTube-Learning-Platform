"""
Quiz Generation Module

This module provides functionality for generating educational quiz questions using AI.

The questions are cached in an SQLite database to improve performance and reduce
API calls. Each question includes the question text, multiple choice options,
the correct answer, and an explanation.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import re

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

from modules import get_cached_modules

# Load environment variables from .env file
load_dotenv()

client = OpenAI(
    base_url="https://api.studio.nebius.com/v1/",
    api_key=os.environ.get("NEBIUS_API_KEY")
)


def call_nebius_llm(model="deepseek-ai/DeepSeek-R1", prompt=""):
    try:
        response = client.chat.completions.create(
            model=model,
            max_tokens=8192,
            temperature=0.2,
            top_p=0.9,
            extra_body={
                "top_k": 50
            },
            messages=[
                {"role": "user",
                 "content": prompt
                }
            ]
        )
        result = response.to_json()
        return result

    except Exception as e:
        print(f"Error making API call: {e}")
        return None

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

    # Create a file handler for all logs with a fixed filename using an absolute path
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
QUIZ_CACHE_DB = './data/quizes.db'

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


def gen_prompt(text, difficulty="medium", num_questions=2):
    return f"""Create {num_questions} {difficulty} multiple-choice questions in JSON format 
        from the text below.

        Format question as JSON array with:
        - "question" (string)
        - "options" (dict with A-D keys)
        - "correct_answer" (A/B/C/D)
        - "explanation" (string)

        Example Response:
        ```json
        [
          {{
            "question": "What is Python's main feature?",
            "options": {{"A": "Static typing", "B": "Dynamic typing", "C": "Compiled", "D": "Low-level"}},
            "correct_answer": "B",
            "explanation": "Python uses dynamic typing by default"
          }}
        ]```

        Text: {text}
        """


class CourseDesignerAgent:
    def generate_quiz_questions(self, text: str, difficulty: str, num_questions: int = 2) -> List[Dict]:
        """
        Generate a quiz question based on the given transcribed text and difficulty level

        Args:
            text: The transcribed text source for question generation
            difficulty: Difficulty level (easy, medium, hard)

        Returns:
            List of dictionaries containing questions and answers
        """
        if not text or num_questions < 1:
            return []
        prompt = gen_prompt(text, difficulty=difficulty, num_questions=num_questions)

        logger.info("Generating quiz questions")
        logger.debug(f"Using prompt: {prompt[:100]}...")  # Log the first 100 chars of prompt

        try:
            # Generate question
            logger.debug("Sending request to LLM API")
            model = "deepseek-ai/DeepSeek-V3"
            response = call_nebius_llm(model, prompt)
            if response:
                response_dict = json.loads(response)
                # Extract content from the response
                content = response_dict['choices'][0]['message']['content']

            logger.debug("Received response from LLM API")
            logger.debug(f"Generated content: {content}")

            # Extract JSON from a Markdown code block
            json_block = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)

            # Extract the actual JSON string from the match object
            if json_block:
                questions = json.loads(json_block.group(1))
            else:
                logger.debug("No JSON block found in the response")
                questions = [self._create_fallback_question(text)]

            logger.info(f"Successfully generated {len(questions)} questions")
            return questions

        except Exception as e:
            logger.debug(f"Error generating question: {e}")
            return []

    def _create_fallback_question(self, text: str) -> Dict:
        return {
            "question": "What is the main focus of " + text[:15] + "?",
            "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
            "correct_answer": "A",
            "explanation": "Fallback question due to generation error."
        }


def get_quiz(video_id: str, module_title: str,
             difficulty: str) -> list[dict] | None | Any:
    """
    Main function to generate quiz questions with caching

    Args:
        video_id: The YouTube video ID
        module_title: The module title (e.g., "How To Use Jetbrains Academy Plugin For Homework Help")
        difficulty: Difficulty level (easy, medium, hard)

    Returns:
        List of dictionaries containing questions and answers
    """

    # Initialize cache
    quiz_cache = QuizCache()
    quiz_cache.init_table()

    # Check cache first
    cached_questions = quiz_cache.get_cached_quiz(video_id, module_title)
    if cached_questions:
        logger.debug("Retrieved quiz from cache")
        return cached_questions

    # Generate new questions if not in cache
    quizzes = generate_all_module_quizzes(video_id, difficulty)

    for quiz in quizzes:
        if quiz['module_title'] == module_title:
            return quiz['questions']


def generate_all_module_quizzes(video_id: str,
                                difficulty: str = "medium") -> list:
    """
    Generate quizzes for all modules associated with a video_id

    Args:
        video_id (str): The ID of the video to generate quizzes for
        difficulty (str): Difficulty level for the quiz questions (default: "medium")

    Returns:
        list: List of dictionaries containing module information and their respective quizzes
    """
    # Initialize quiz cache if needed
    quiz_cache = QuizCache()
    quiz_cache.init_table()

    # Get all modules
    modules = get_cached_modules(video_id)
    if not modules:
        raise ValueError("No modules found in cache")

    # Initialize CourseDesignerAgent
    agent = CourseDesignerAgent()

    # Generate quizzes for each module
    module_quizzes = []
    for i, module in enumerate(modules):
        module_text = get_module_text(module)
        if not module_text:
            continue

        try:
            questions = agent.generate_quiz_questions(
                module_text,
                difficulty
            )

            module_quiz = {
                'module_title': module.get('title', ''),
                'questions': questions
            }
            module_quizzes.append(module_quiz)

            # Save the generated quiz to cache
            quiz_cache.save_quiz_to_cache(video_id, module_quiz['module_title'], difficulty, questions)
            logger.debug(f"Generated quiz for module {module.get('title', '')} with {len(questions)} questions")

        except Exception as e:
            logger.debug(f"Error generating quiz for module {module.get('title', '')}: {str(e)}")
            continue

    return module_quizzes
