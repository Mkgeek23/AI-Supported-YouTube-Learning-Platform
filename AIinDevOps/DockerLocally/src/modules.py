import os
import re
import sqlite3
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

from typing import Optional, List, Dict

# Database path
MODULES_CACHE_DB = './data/modules.db'


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


def init_course_cache() -> None:
    """
    Initializes the SQLite database for caching course structures
    """
    conn = sqlite3.connect(MODULES_CACHE_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS course_modules (
            video_id TEXT PRIMARY KEY,
            modules TEXT,
            created_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def get_cached_modules(video_id: str) -> Optional[List[Dict]]:
    """
    Retrieves cached course modules for a given transcript ID.

    Args:
        video_id: Unique identifier for the transcript

    Returns:
        List of module dictionaries if found, None otherwise
    """
    conn = sqlite3.connect(MODULES_CACHE_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT modules FROM course_modules WHERE video_id = ?',
                   (video_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return json.loads(result[0])
    return None


def save_modules_to_cache(video_id: str, modules: List[Dict]) -> None:
    """
    Saves structured course modules to cache

    Args:
        video_id: Unique identifier for the transcript
        modules: List of module dictionaries to cache
    """
    conn = sqlite3.connect(MODULES_CACHE_DB)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO course_modules 
        (video_id, modules, created_at)
        VALUES (?, ?, ?)
    ''', (
        video_id,
        json.dumps(modules),
        datetime.now()
    ))
    conn.commit()
    conn.close()


def extract_video_id(url):
    # Match the video ID pattern in YouTube embed URLs
    pattern = r'(?:embed\/|watch\?v=|\/)?([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None


def structure_transcript(video: Dict) -> List[Dict]:
    """
    Structures transcript into logical parts with caching
    """
    # Generate a simple transcript ID (could be more sophisticated)
    video_id = extract_video_id(video['embed_url'])
    print(f"Generating course structure for video ID: {video_id}")

    # Initialize cache database
    init_course_cache()

    # Check cache first
    cached_modules = get_cached_modules(video_id)
    if cached_modules:
        print("Retrieved course structure from cache")
        return cached_modules

    # If not in cache, generate a new structure
    modules = []
    current_module = {
        'title': '',
        'content': [],
        'start_time': 0,
        'end_time': 0
    }

    CHUNK_SIZE = 600  # 10 minutes in seconds

    for entry in video['transcript']:
        if not current_module['content']:
            current_module['start_time'] = entry['start']
            current_module['content'].append(entry)
        elif entry['start'] - current_module['start_time'] < CHUNK_SIZE:
            current_module['content'].append(entry)
        else:
            # Finalize current module
            current_module['end_time'] = current_module['content'][-1]['end']
            current_module['title'] = generate_module_title(current_module['content'])
            modules.append(current_module.copy())

            # Start new module
            current_module = {
                'title': '',
                'content': [entry],
                'start_time': entry['start'],
                'end_time': 0
            }

    # Add the last module if it has content
    if current_module['content']:
        current_module['end_time'] = current_module['content'][-1]['end']
        current_module['title'] = generate_module_title(current_module['content'])
        modules.append(current_module)

    # Save to cache
    save_modules_to_cache(video_id, modules)
    print("Saved new course structure to cache")

    return modules


class TitleGenerator:
    def __init__(self):
        self.model = "meta-llama/Llama-3.3-70B-Instruct"

    def generate_title(self, text):
        prompt = f"""Generate a concise and descriptive title for the following content. 
                The title should be between 3 to 10 words and capture the main topic.

                Content:
                {text}

                Title:
                """

        try:
            title = None
            response = call_nebius_llm(model=self.model, prompt=prompt)
            if response:
                response_dict = json.loads(response)
                # Extract content from the response
                title = response_dict['choices'][0]['message']['content'].strip()

            return title

        except Exception as e:
            print(f"Error generating title: {e}")
            return None


def generate_module_title(content: List[Dict]) -> str:
    """
    Generates a title using the LLM based on content
    """
    # Combine all text in the module
    full_text = ' '.join([entry['text'] for entry in content])

    try:
        # Initialize the generator if not already done
        generator = TitleGenerator()

        title = generator.generate_title(full_text)

        if title:
            # Convert to a title case and remove the final punctuation
            title = title.title().rstrip('.!?')
            return title

    except Exception as e:
        print(f"Error generating title: {e}")

    # Fallback to simple approach if model fails
    words = full_text.split()
    if len(words) > 10:
        return ' '.join(words[:10]) + '...'
    return full_text
