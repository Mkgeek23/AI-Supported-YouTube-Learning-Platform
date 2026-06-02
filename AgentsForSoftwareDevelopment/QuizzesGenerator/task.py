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

from typing import List, Dict, Any

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

        Args:
            text: The transcribed text source for question generation
            difficulty: Difficulty level (easy, medium, hard)

        Returns:
            List of dictionaries containing questions and answers
        """
        if not text or num_questions < 1:
            return []
        prompt = None # TODO: call gen_prompt function with text as argument

        logger.info("Generating quiz questions")
        logger.debug(f"Using prompt: {prompt[:100]}...")  # Log the first 100 chars of prompt

        try:
            # Generate question
            logger.debug("Sending request to LLM API")
            model = "deepseek-ai/DeepSeek-V3"
            response = "" # TODO: use `call_nebius_llm` function here
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


def main():
    # Generate quizzes for all modules in a video
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
