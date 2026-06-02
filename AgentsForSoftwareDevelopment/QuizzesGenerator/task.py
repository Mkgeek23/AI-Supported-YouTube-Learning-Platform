"""
Quiz Generation Module

This module provides functionality for generating educational quiz questions using AI.

The questions are cached in an SQLite database to improve performance and reduce
API calls. Each question includes the question text, multiple choice options,
the correct answer, and an explanation.
"""
from __future__ import annotations

import json
import re
import sys
import os

from typing import List, Dict, Any

# Dynamiczne dodanie głównego katalogu do ścieżek wyszukiwania,
# aby zapobiec ModuleNotFoundError na każdym środowisku
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from AgentsForSoftwareDevelopment.CreateModules.task import get_cached_modules
from AgentsForSoftwareDevelopment.QuizzesGenerator.utils import logger, get_module_text, QuizCache
from PromptingTechniques.SpecGeneration.task import call_nebius_llm


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
        """
        if not text or text.strip() == "":
            logger.debug("Input text is empty or whitespace. Returning an empty list.")
            return []

        logger.info("Generating quiz questions")
        prompt = gen_prompt(text, difficulty, num_questions)
        logger.debug(f"Using prompt: {prompt[:100]}...")

        try:
            logger.debug("Sending request to LLM API")
            model = "deepseek-ai/DeepSeek-V3.2"

            # POPRAWKA 2: Jawne przekazanie parametrów jako keyword arguments
            response = call_nebius_llm(prompt=prompt, model=model)

            # POPRAWKA 1: Cała logika przetwarzania wewnątrz warunku 'if response'
            if not response:
                logger.error("No response received from LLM API")
                return [self._create_fallback_question(text)]

            response_dict = json.loads(response)
            content = response_dict['choices'][0]['message']['content'].strip()

            logger.debug("Received response from LLM API")
            logger.debug(f"Generated content: {content}")

            # POPRAWKA 3: Elastyczne parsowanie JSON
            questions = None

            # Najpierw spróbujmy bezpośrednio (gdy model nie zwrócił markdowna, tylko czysty JSON)
            try:
                questions = json.loads(content)
            except json.JSONDecodeError:
                # Jeśli się nie udało, wyciągamy za pomocą regexa (obsługuje wielkość liter i spacje)
                json_block = re.search(r'```(?:json)?\s*\n(.*?)\n```', content, re.DOTALL | re.IGNORECASE)
                if json_block:
                    try:
                        questions = json.loads(json_block.group(1).strip())
                    except json.JSONDecodeError as jde:
                        logger.debug(f"Failed to parse JSON inside markdown block: {jde}")

            if not questions:
                logger.debug("Could not parse JSON from model response. Using fallback.")
                questions = [self._create_fallback_question(text)]

            logger.info(f"Successfully generated {len(questions)} questions")
            return questions

        except Exception as e:
            logger.error(f"Error generating question: {e}")
            return [self._create_fallback_question(text)]

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
    """
    quiz_cache = QuizCache()
    quiz_cache.init_table()

    # Sprawdzenie cache (upewnij się, czy Twoja klasa QuizCache obsługuje też parametr difficulty)
    # Jeśli tak, przekaż go jako parametr.
    cached_questions = quiz_cache.get_cached_quiz(video_id, module_title)
    if cached_questions:
        logger.debug("Retrieved quiz from cache")
        return cached_questions

    # Generowanie nowych pytań
    quizzes = generate_all_module_quizzes(video_id, difficulty)

    for quiz in quizzes:
        if quiz['module_title'] == module_title:
            return quiz['questions']

    return None


def generate_all_module_quizzes(video_id: str,
                                difficulty: str = "medium") -> list:
    """
    Generate quizzes for all modules associated with a video_id
    """
    quiz_cache = QuizCache()
    quiz_cache.init_table()

    modules = get_cached_modules(video_id)
    if not modules:
        raise ValueError("No modules found in cache")

    agent = CourseDesignerAgent()
    module_quizzes = []

    for module in modules:
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

            quiz_cache.save_quiz_to_cache(video_id, module_quiz['module_title'], difficulty, questions)
            logger.debug(f"Generated quiz for module {module.get('title', '')} with {len(questions)} questions")

        except Exception as e:
            logger.error(f"Error generating quiz for module {module.get('title', '')}: {str(e)}")
            continue

    return module_quizzes


def main():
    try:
        quizzes = generate_all_module_quizzes(
            video_id="UEtBMyzLBFY",
            difficulty="medium"
        )
        logger.debug(f"Generated quizzes for {len(quizzes)} modules")
    except ValueError as e:
        logger.debug(f"Error: {str(e)}")


if __name__ == '__main__':
    main()