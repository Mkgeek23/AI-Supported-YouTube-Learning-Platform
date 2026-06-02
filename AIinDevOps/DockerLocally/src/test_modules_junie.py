import unittest
import sqlite3
import os
import json
from unittest.mock import patch, MagicMock

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import modules
from modules import (
    init_course_cache,
    get_cached_modules,
    save_modules_to_cache,
    extract_video_id,
    structure_transcript,
    TitleGenerator,
    generate_module_title
)

class TestModulesDatabaseOperations(unittest.TestCase):
    """Tests for the database operations in the Modules module."""

    def setUp(self):
        """Set up test environment before each test."""
        self.test_db_path = 'modules.db'
        self.original_path = modules.MODULES_CACHE_DB
        modules.MODULES_CACHE_DB = self.test_db_path

    def tearDown(self):
        """Clean up after each test."""
        # Delete the test database file
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

        # Restore the original database path
        modules.MODULES_CACHE_DB = self.original_path

    def test_init_course_cache(self):
        """Test that init_course_cache creates the correct schema."""
        # Initialize the database
        init_course_cache()

        # Connect to the database and check if the table exists
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        # Query to check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='course_modules'")
        table_exists = cursor.fetchone() is not None

        # Check if the table has the correct columns
        cursor.execute("PRAGMA table_info(course_modules)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]

        conn.close()

        # Assert that the table exists
        self.assertTrue(table_exists, "The course_modules table was not created")

        # Assert that all expected columns exist
        expected_columns = ['video_id', 'modules', 'created_at']
        for column in expected_columns:
            self.assertIn(column, column_names, f"Column {column} is missing from the course_modules table")

    def test_get_cached_modules(self):
        """Test that get_cached_modules retrieves correct data."""
        # Initialize the database
        init_course_cache()

        # Connect to the database and insert test data
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        # Test data
        video_id = "test_vid_id"
        modules_data = [
            {
                'title': 'Module 1',
                'content': [{'text': 'Content 1'}],
                'start_time': 0,
                'end_time': 60
            }
        ]

        # Insert test data
        cursor.execute(
            "INSERT INTO course_modules (video_id, modules, created_at) VALUES (?, ?, datetime('now'))",
            (video_id, json.dumps(modules_data))
        )
        conn.commit()
        conn.close()

        # Retrieve the data using the function
        result = get_cached_modules(video_id)

        # Assert that the result matches the test data
        self.assertIsNotNone(result, "No result returned from get_cached_modules")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], modules_data[0]['title'])
        self.assertEqual(result[0]['content'], modules_data[0]['content'])
        self.assertEqual(result[0]['start_time'], modules_data[0]['start_time'])
        self.assertEqual(result[0]['end_time'], modules_data[0]['end_time'])

    def test_save_modules_to_cache(self):
        """Test that save_modules_to_cache saves data correctly."""
        # Initialize the database
        init_course_cache()

        # Test data
        video_id = "test_vid_id"
        modules_data = [
            {
                'title': 'Module 1',
                'content': [{'text': 'Content 1'}],
                'start_time': 0,
                'end_time': 60
            }
        ]

        # Save the data using the function
        save_modules_to_cache(video_id, modules_data)

        # Connect to the database and retrieve the saved data
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT modules FROM course_modules WHERE video_id = ?", (video_id,))
        result = cursor.fetchone()
        conn.close()

        # Assert that the saved data matches the test data
        self.assertIsNotNone(result, "No data was saved to the database")
        saved_modules = json.loads(result[0])
        self.assertEqual(len(saved_modules), 1)
        self.assertEqual(saved_modules[0]['title'], modules_data[0]['title'])
        self.assertEqual(saved_modules[0]['content'], modules_data[0]['content'])
        self.assertEqual(saved_modules[0]['start_time'], modules_data[0]['start_time'])
        self.assertEqual(saved_modules[0]['end_time'], modules_data[0]['end_time'])


class TestModuleStructuring(unittest.TestCase):
    """Tests for the module structuring functions in the Modules module."""

    def setUp(self):
        """Set up test environment before each test."""
        # Use an in-memory database for testing
        self.test_db_path = 'modules.db'
        self.original_path = modules.MODULES_CACHE_DB
        modules.MODULES_CACHE_DB = self.test_db_path

        # Initialize the database
        init_course_cache()

    def tearDown(self):
        """Clean up after each test."""
        # Delete the test database file
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

        # Restore the original database path
        modules.MODULES_CACHE_DB = self.original_path

    def test_extract_video_id(self):
        """Test extract_video_id with various URL formats."""
        # Test with standard YouTube URL
        url = "https://www.youtube.com/watch?v=test_vid_id"
        self.assertEqual(extract_video_id(url), "test_vid_id")

        # Test with embed URL
        url = "https://www.youtube.com/embed/test_vid_id"
        self.assertEqual(extract_video_id(url), "test_vid_id")

        # Test with shortened URL
        url = "https://youtu.be/test_vid_id"
        self.assertEqual(extract_video_id(url), "test_vid_id")

        # Test with invalid URL
        url = "https://example.com"
        self.assertIsNone(extract_video_id(url))

    @patch('modules.generate_module_title')
    def test_structure_transcript(self, mock_generate_title):
        """Test structure_transcript correctly divides content."""
        # Mock the generate_module_title function
        mock_generate_title.return_value = "Test Module Title"

        # Create a test transcript
        transcript = {
            'embed_url': 'https://www.youtube.com/embed/test_vid_id',
            'transcript': [
                {'id': 1, 'text': 'Content 1', 'start': 0, 'end': 10},
                {'id': 2, 'text': 'Content 2', 'start': 10, 'end': 20},
                {'id': 3, 'text': 'Content 3', 'start': 20, 'end': 30},
                # Add more entries to exceed the CHUNK_SIZE
                {'id': 4, 'text': 'Content 4', 'start': 600, 'end': 610},
                {'id': 5, 'text': 'Content 5', 'start': 610, 'end': 620}
            ]
        }

        # Call the function
        result = structure_transcript(transcript)

        # Assert that the result is structured correctly
        self.assertIsNotNone(result, "No result returned from structure_transcript")
        self.assertEqual(len(result), 2, "Expected 2 modules to be created")

        # Check first module
        self.assertEqual(result[0]['title'], "Test Module Title")
        self.assertEqual(result[0]['start_time'], 0)
        self.assertEqual(len(result[0]['content']), 3)

        # Check second module
        self.assertEqual(result[1]['title'], "Test Module Title")
        self.assertEqual(result[1]['start_time'], 600)
        self.assertEqual(len(result[1]['content']), 2)

    @patch('modules.get_cached_modules')
    def test_caching_mechanism(self, mock_get_cached):
        """Test that the caching mechanism works correctly."""
        # Mock the get_cached_modules function to return cached data
        cached_modules = [
            {
                'title': 'Cached Module',
                'content': [{'text': 'Cached Content'}],
                'start_time': 0,
                'end_time': 60
            }
        ]
        mock_get_cached.return_value = cached_modules

        # Create a test transcript
        transcript = {
            'embed_url': 'https://www.youtube.com/embed/test_vid_id',
            'transcript': [
                {'id': 1, 'text': 'Content 1', 'start': 0, 'end': 10}
            ]
        }

        # Call the function
        result = structure_transcript(transcript)

        # Assert that the result is the cached data
        self.assertEqual(result, cached_modules)

        # Verify that get_cached_modules was called with the correct video_id
        mock_get_cached.assert_called_once_with('test_vid_id')


class TestTitleGeneration(unittest.TestCase):
    """Tests for the title generation functions in the Modules module."""

    @patch('modules.TitleGenerator')
    def test_generate_module_title(self, mock_title_generator_class):
        """Test generate_module_title with various inputs."""
        # Mock the TitleGenerator class
        mock_generator = MagicMock()
        mock_generator.generate_title.return_value = "Generated Title"
        mock_title_generator_class.return_value = mock_generator

        # Test data
        content = [
            {'text': 'This is the first sentence.'},
            {'text': 'This is the second sentence.'}
        ]

        # Call the function
        result = generate_module_title(content)

        # Assert that the result is the generated title
        self.assertEqual(result, "Generated Title")

        # Verify that the generator was called with the correct text
        expected_text = 'This is the first sentence. This is the second sentence.'
        mock_generator.generate_title.assert_called_once_with(expected_text[:1024])

    @patch('modules.TitleGenerator')
    def test_fallback_mechanism(self, mock_title_generator_class):
        """Test fallback mechanism when model fails."""
        # Mock the TitleGenerator class to simulate a failure
        mock_generator = MagicMock()
        mock_generator.generate_title.return_value = None
        mock_generator.model = None  # Simulate model loading failure
        mock_title_generator_class.return_value = mock_generator

        # Test data
        content = [
            {'text': 'This is a test sentence.'}
        ]

        # Call the function
        result = generate_module_title(content)

        # Assert that the result is the fallback title
        self.assertEqual(result, 'This is a test sentence.')


if __name__ == '__main__':
    unittest.main()
