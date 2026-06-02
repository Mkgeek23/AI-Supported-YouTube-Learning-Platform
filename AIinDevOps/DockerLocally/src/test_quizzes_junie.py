import unittest
import sqlite3
import os
import json
from unittest.mock import patch, MagicMock

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import quizzes
from quizzes import (
    QuizCache,
    get_module_text,
    call_nebius_llm,
    CourseDesignerAgent,
    get_quiz,
    generate_all_module_quizzes,
    gen_prompt,
    setup_logging
)

class TestQuizCacheDatabaseOperations(unittest.TestCase):
    """Tests for the database operations in the Quizzes module."""

    def setUp(self):
        """Set up a test environment before each test."""
        # Use an in-memory database for testing
        self.test_db_path = 'quizes.db'
        self.original_path = quizzes.QUIZ_CACHE_DB
        quizzes.QUIZ_CACHE_DB = self.test_db_path

    def tearDown(self):
        """Clean up after each test."""
        # Delete the test database file
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

        # Restore the original database path
        quizzes.QUIZ_CACHE_DB = self.original_path

    def test_quiz_cache_initialization(self):
        """Test QuizCache class initialization."""
        # Initialize the cache
        cache = QuizCache(self.test_db_path)

        # Connect to the database and check if the table exists
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        # Query to check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='module_questions'")
        table_exists = cursor.fetchone() is not None

        # Check if the table has the correct columns
        cursor.execute("PRAGMA table_info(module_questions)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]

        conn.close()

        # Assert that the table exists
        self.assertTrue(table_exists, "The module_questions table was not created")

        # Assert that all expected columns exist
        expected_columns = ['video_id', 'module_title', 'difficulty', 'questions', 'created_at']
        for column in expected_columns:
            self.assertIn(column, column_names, f"Column {column} is missing from the module_questions table")

    def test_get_cached_quiz(self):
        """Test that get_cached_quiz retrieves correct data."""
        # Initialize the cache
        cache = QuizCache(self.test_db_path)

        # Connect to the database and insert test data
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        # Test data
        video_id = "test_video_id"
        module_title = "Test Module"
        difficulty = "medium"
        questions = [
            {
                "question": "Test question?",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "A",
                "explanation": "Test explanation"
            }
        ]

        # Insert test data
        cursor.execute(
            "INSERT INTO module_questions (video_id, module_title, difficulty, questions, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
            (video_id, module_title, difficulty, json.dumps(questions))
        )
        conn.commit()
        conn.close()

        # Retrieve the data using the function
        result = cache.get_cached_quiz(video_id, module_title)

        # Assert that the result matches the test data
        self.assertIsNotNone(result, "No result returned from get_cached_quiz")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['question'], questions[0]['question'])
        self.assertEqual(result[0]['options'], questions[0]['options'])
        self.assertEqual(result[0]['correct_answer'], questions[0]['correct_answer'])
        self.assertEqual(result[0]['explanation'], questions[0]['explanation'])

    def test_save_quiz_to_cache(self):
        """Test that save_quiz_to_cache saves data correctly."""
        # Initialize the cache
        cache = QuizCache(self.test_db_path)

        # Test data
        video_id = "test_video_id"
        module_title = "Test Module"
        difficulty = "medium"
        questions = [
            {
                "question": "Test question?",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "A",
                "explanation": "Test explanation"
            }
        ]

        # Save the data using the function
        cache.save_quiz_to_cache(video_id, module_title, difficulty, questions)

        # Connect to the database and retrieve the saved data
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT questions FROM module_questions WHERE video_id = ? AND module_title = ?", (video_id, module_title))
        result = cursor.fetchone()
        conn.close()

        # Assert that the saved data matches the test data
        self.assertIsNotNone(result, "No data was saved to the database")
        saved_questions = json.loads(result[0])
        self.assertEqual(len(saved_questions), 1)
        self.assertEqual(saved_questions[0]['question'], questions[0]['question'])
        self.assertEqual(saved_questions[0]['options'], questions[0]['options'])
        self.assertEqual(saved_questions[0]['correct_answer'], questions[0]['correct_answer'])
        self.assertEqual(saved_questions[0]['explanation'], questions[0]['explanation'])


class TestQuizHelperFunctions(unittest.TestCase):
    """Tests for the helper functions in the Quizzes module."""

    def test_get_module_text(self):
        """Test get_module_text extracts text correctly."""
        # Test with a valid module
        module = {
            'title': 'Test Module',
            'content': [
                {'text': 'This is the first sentence.'},
                {'text': 'This is the second sentence.'}
            ]
        }
        result = get_module_text(module)
        expected = 'Test Module This is the first sentence. This is the second sentence.'
        self.assertEqual(result, expected)

        # Test with an empty module
        module = {}
        result = get_module_text(module)
        self.assertEqual(result, "")

        # Test with a module with no content
        module = {'title': 'Test Module'}
        result = get_module_text(module)
        self.assertEqual(result, "Test Module")

        # Test with a module with empty content
        module = {'title': 'Test Module', 'content': []}
        result = get_module_text(module)
        self.assertEqual(result, "Test Module")

        # Test with a module with invalid content
        module = {'title': 'Test Module', 'content': 'Not a list'}
        result = get_module_text(module)
        self.assertEqual(result, "Test Module")

    @patch('quizzes.client')
    def test_call_nebius_llm(self, mock_client):
        """Test call_nebius_llm with mocked API."""
        # Mock the OpenAI client response
        mock_response = MagicMock()
        mock_response.to_json.return_value = '{"choices": [{"message": {"content": "Test response"}}]}'
        mock_client.chat.completions.create.return_value = mock_response

        # Call the function
        result = call_nebius_llm(prompt="Test prompt")

        # Assert that the result is the expected response
        self.assertEqual(result, '{"choices": [{"message": {"content": "Test response"}}]}')

        # Verify that the client was called with the correct parameters
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args['model'], "deepseek-ai/DeepSeek-R1")
        self.assertEqual(call_args['messages'][0]['content'], "Test prompt")

    @patch('quizzes.client')
    def test_call_nebius_llm_error_handling(self, mock_client):
        """Test error handling in call_nebius_llm."""
        # Mock the OpenAI client to raise an exception
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        # Call the function
        result = call_nebius_llm(prompt="Test prompt")

        # Assert that the function returns None on error
        self.assertIsNone(result)

    @patch('quizzes.logging')
    def test_setup_logging(self, mock_logging):
        """Test logging functionality."""
        # Mock the logger
        mock_logger = MagicMock()
        mock_logging.getLogger.return_value = mock_logger
        mock_logger.handlers = []

        # Call the function
        result = setup_logging()

        # Assert that the function returns the logger
        self.assertEqual(result, mock_logger)

        # Verify that the logger was configured correctly
        mock_logging.getLogger.assert_called_once_with('quiz_generator')
        mock_logger.setLevel.assert_called_once_with(mock_logging.DEBUG)
        self.assertEqual(mock_logging.FileHandler.call_count, 1)
        self.assertEqual(mock_logging.StreamHandler.call_count, 1)


class TestQuizGeneration(unittest.TestCase):
    """Tests for the quiz generation functions in the Quizzes module."""

    def setUp(self):
        """Set up a test environment before each test."""
        self.test_db_path = 'quizes.db'
        self.original_path = quizzes.QUIZ_CACHE_DB
        quizzes.QUIZ_CACHE_DB = self.test_db_path

        # Initialize the cache
        self.cache = QuizCache(self.test_db_path)

    def tearDown(self):
        """Clean up after each test."""
        # Delete the test database file
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        # Restore the original database path
        quizzes.QUIZ_CACHE_DB = self.original_path

    def test_gen_prompt(self):
        """Test gen_prompt generates the correct prompt."""
        # Call the function
        result = gen_prompt("Test text", difficulty="easy", num_questions=3)

        # Assert that the result contains the expected elements
        self.assertIn("Create 3 easy multiple-choice questions", result)
        self.assertIn("Test text", result)
        self.assertIn("Format question as JSON array", result)

    @patch('quizzes.call_nebius_llm')
    def test_course_designer_agent_generate_quiz_questions(self, mock_call_nebius):
        """Test CourseDesignerAgent.generate_quiz_questions with mocked API."""
        # Mock the API response
        mock_response = json.dumps({
            'choices': [
                {
                    'message': {
                        'content': '''```json
[
  {
    "question": "Test question?",
    "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
    "correct_answer": "A",
    "explanation": "Test explanation"
  }
]```'''
                    }
                }
            ]
        })
        mock_call_nebius.return_value = mock_response

        # Create an agent
        agent = CourseDesignerAgent()

        # Call the function
        result = agent.generate_quiz_questions("Test text", "medium")

        # Assert that the result contains the expected question
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['question'], "What is the main focus of Test text?")
        self.assertEqual(result[0]['correct_answer'], "A")

        # Verify that the API was called with the correct parameters
        mock_call_nebius.assert_called_once()
        call_args = mock_call_nebius.call_args[0]
        self.assertEqual(call_args[0], "deepseek-ai/DeepSeek-V3")

    @patch('quizzes.call_nebius_llm')
    def test_course_designer_agent_fallback(self, mock_call_nebius):
        """Test the fallback mechanism when API fails."""
        # Mock the API to return None
        mock_call_nebius.return_value = None

        # Create an agent
        agent = CourseDesignerAgent()

        # Call the function
        result = agent.generate_quiz_questions("Test text", "medium")

        # Assert that the result is empty (fallback behavior)
        self.assertEqual(len(result), 0)

    @patch('quizzes.QuizCache')
    def test_get_quiz_from_cache(self, mock_quiz_cache):
        """Test get_quiz retrieves from cache correctly."""
        # Mock the cache to return cached questions
        mock_cache_instance = MagicMock()
        mock_quiz_cache.return_value = mock_cache_instance

        cached_questions = [
            {
                "question": "Cached question?",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "A",
                "explanation": "Cached explanation"
            }
        ]
        mock_cache_instance.get_cached_quiz.return_value = cached_questions

        # Call the function
        result = get_quiz("test_video_id", "Test Module", "medium")

        # Assert that the result is the cached questions
        self.assertEqual(result, cached_questions)

        # Verify that the cache was queried with the correct parameters
        mock_cache_instance.get_cached_quiz.assert_called_once_with("test_video_id", "Test Module")

    @patch('quizzes.QuizCache')
    @patch('quizzes.generate_all_module_quizzes')
    def test_get_quiz_generates_new(self, mock_generate_all, mock_quiz_cache):
        """Test get_quiz generates new questions when not in cache."""
        # Mock the cache to return None (not found)
        mock_cache_instance = MagicMock()
        mock_quiz_cache.return_value = mock_cache_instance
        mock_cache_instance.get_cached_quiz.return_value = None

        # Mock generate_all_module_quizzes to return new questions
        generated_quizzes = [
            {
                'module_title': 'Test Module',
                'questions': [
                    {
                        "question": "Generated question?",
                        "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                        "correct_answer": "B",
                        "explanation": "Generated explanation"
                    }
                ]
            },
            {
                'module_title': 'Other Module',
                'questions': []
            }
        ]
        mock_generate_all.return_value = generated_quizzes

        # Call the function
        result = get_quiz("test_video_id", "Test Module", "medium")

        # Assert that the result is the generated questions for the correct module
        self.assertEqual(result, generated_quizzes[0]['questions'])

        # Verify that generate_all_module_quizzes was called with the correct parameters
        mock_generate_all.assert_called_once_with("test_video_id", "medium")

    @patch('quizzes.get_cached_modules')
    @patch('quizzes.CourseDesignerAgent')
    @patch('quizzes.QuizCache')
    def test_generate_all_module_quizzes(self, mock_quiz_cache, mock_agent_class, mock_get_cached_modules):
        """Test generate_all_module_quizzes for multiple modules."""
        # Mock get_cached_modules to return test modules
        modules = [
            {
                'title': 'Module 1',
                'content': [{'text': 'Content 1'}]
            },
            {
                'title': 'Module 2',
                'content': [{'text': 'Content 2'}]
            }
        ]
        mock_get_cached_modules.return_value = modules

        # Mock CourseDesignerAgent to return test questions
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        questions1 = [
            {
                "question": "Question 1?",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "A",
                "explanation": "Explanation 1"
            }
        ]
        questions2 = [
            {
                "question": "Question 2?",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "B",
                "explanation": "Explanation 2"
            }
        ]
        mock_agent.generate_quiz_questions.side_effect = [questions1, questions2]

        # Mock QuizCache
        mock_cache_instance = MagicMock()
        mock_quiz_cache.return_value = mock_cache_instance

        # Call the function
        result = generate_all_module_quizzes("test_video_id", "medium")

        # Assert that the result contains quizzes for both modules
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['module_title'], 'Module 1')
        self.assertEqual(result[0]['questions'], questions1)
        self.assertEqual(result[1]['module_title'], 'Module 2')
        self.assertEqual(result[1]['questions'], questions2)

        # Verify that the agent was called with the correct parameters
        self.assertEqual(mock_agent.generate_quiz_questions.call_count, 2)

        # Verify that the cache was used to save the generated quizzes
        self.assertEqual(mock_cache_instance.save_quiz_to_cache.call_count, 2)

    @patch('quizzes.get_cached_modules')
    def test_generate_all_module_quizzes_no_modules(self, mock_get_cached_modules):
        """Test generate_all_module_quizzes when no modules are found."""
        # Mock get_cached_modules to return None
        mock_get_cached_modules.return_value = None

        # Call the function and assert that it raises a ValueError
        with self.assertRaises(ValueError):
            generate_all_module_quizzes("test_video_id", "medium")


if __name__ == '__main__':
    unittest.main()
