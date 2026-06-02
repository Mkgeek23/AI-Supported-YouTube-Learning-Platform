import unittest
import sqlite3
import os
import json
from unittest.mock import patch, MagicMock

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import transcriber
from transcriber import (
    init_database, 
    get_transcription_from_db, 
    save_transcription_to_db, 
    transcribe_youtube_video
)

class TestTranscriberDatabaseOperations(unittest.TestCase):
    """Tests for the database operations in the Transcriber module."""

    def setUp(self):
        """Set up test environment before each test."""
        self.test_db_path = 'transcriptions.db'
        self.original_path = transcriber.Transcriptions_CACHE_DB
        transcriber.Transcriptions_CACHE_DB = self.test_db_path

    def tearDown(self):
        """Clean up after each test."""
        # Delete the test database file
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

        # Restore the original database path
        transcriber.Transcriptions_CACHE_DB = self.original_path

    def test_init_database(self):
        """Test that init_database creates the correct schema."""
        # Initialize the database
        init_database()

        # Connect to the database and check if the table exists
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        # Query to check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transcriptions'")
        table_exists = cursor.fetchone() is not None

        # Check if the table has the correct columns
        cursor.execute("PRAGMA table_info(transcriptions)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]

        conn.close()

        # Assert that the table exists
        self.assertTrue(table_exists, "The transcriptions table was not created")

        # Assert that all expected columns exist
        expected_columns = ['video_id', 'title', 'embed_url', 'duration', 'transcript', 'created_at']
        for column in expected_columns:
            self.assertIn(column, column_names, f"Column {column} is missing from the transcriptions table")

    def test_get_transcription_from_db(self):
        """Test that get_transcription_from_db retrieves correct data."""
        # Initialize the database
        init_database()

        # Connect to the database and insert test data
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        # Test data
        video_id = "test_vid_id"
        title = "Test Video"
        embed_url = "https://www.youtube.com/embed/test_vid_id"
        duration = 120
        transcript = [{"id": 1, "text": "Test transcript"}]

        # Insert test data
        cursor.execute(
            "INSERT INTO transcriptions (video_id, title, embed_url, duration, transcript, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (video_id, title, embed_url, duration, json.dumps(transcript))
        )
        conn.commit()
        conn.close()

        # Retrieve the data using the function
        result = get_transcription_from_db(video_id)

        # Assert that the result matches the test data
        self.assertIsNotNone(result, "No result returned from get_transcription_from_db")
        self.assertEqual(result['title'], title)
        self.assertEqual(result['embed_url'], embed_url)
        self.assertEqual(result['duration'], duration)
        self.assertEqual(result['transcript'], transcript)

    def test_save_transcription_to_db(self):
        """Test that save_transcription_to_db saves data correctly."""
        # Initialize the database
        init_database()

        # Test data
        video_id = "test_vid_id"
        video_info = {
            'title': "Test Video",
            'embed_url': "https://www.youtube.com/embed/test_vid_id",
            'duration': 120,
            'transcript': [{"id": 1, "text": "Test transcript"}]
        }

        # Save the data using the function
        save_transcription_to_db(video_id, video_info)

        # Connect to the database and retrieve the saved data
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT title, embed_url, duration, transcript FROM transcriptions WHERE video_id = ?", (video_id,))
        result = cursor.fetchone()
        conn.close()

        # Assert that the saved data matches the test data
        self.assertIsNotNone(result, "No data was saved to the database")
        self.assertEqual(result[0], video_info['title'])
        self.assertEqual(result[1], video_info['embed_url'])
        self.assertEqual(result[2], video_info['duration'])
        self.assertEqual(json.loads(result[3]), video_info['transcript'])


class TestTranscriptionFunction(unittest.TestCase):
    """Tests for the transcription function in the Transcriber module."""

    def setUp(self):
        """Set up test environment before each test."""
        # Use an in-memory database for testing
        self.test_db_path = 'transcriptions.db'
        self.original_path = transcriber.Transcriptions_CACHE_DB
        transcriber.Transcriptions_CACHE_DB = self.test_db_path

        # Initialize the database
        init_database()

    def tearDown(self):
        """Clean up after each test."""
        # Delete the test database file
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

        # Restore the original database path
        transcriber.Transcriptions_CACHE_DB = self.original_path

        # Remove any temporary files created during tests
        if os.path.exists('temp_audio.wav'):
            os.remove('temp_audio.wav')

    @patch('transcriber.whisper')
    @patch('transcriber.yt_dlp.YoutubeDL')
    def test_transcribe_youtube_video_with_mocked_dependencies(self, mock_ytdl, mock_whisper):
        """Test transcribe_youtube_video with mocked dependencies."""
        # Mock YoutubeDL extract_info
        mock_info = {'id': 'test_vid_id', 'title': 'Test Video', 'duration': 120}
        mock_ytdl_instance = MagicMock()
        mock_ytdl_instance.extract_info.return_value = mock_info
        mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance

        # Mock whisper model
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'segments': [
                {'id': 1, 'text': 'Test transcript', 'start': 0, 'end': 10}
            ]
        }
        mock_whisper.load_model.return_value = mock_model

        # Call the function
        url = "https://www.youtube.com/watch?v=test_vid_id"
        result = transcribe_youtube_video(url)

        # Assert that the function returns the expected result
        self.assertIsNotNone(result, "No result returned from transcribe_youtube_video")
        self.assertEqual(result['title'], 'Test Video')
        self.assertEqual(result['embed_url'], 'https://www.youtube.com/embed/test_vid_id')
        self.assertEqual(result['duration'], 120)
        self.assertEqual(len(result['transcript']), 1)
        self.assertEqual(result['transcript'][0]['text'], 'Test transcript')

        # Verify that the model was called with the correct parameters
        mock_whisper.load_model.assert_called_once_with("base")
        mock_model.transcribe.assert_called_once()

    @patch('transcriber.whisper')
    @patch('transcriber.yt_dlp.YoutubeDL')
    def test_caching_mechanism(self, mock_ytdl, mock_whisper):
        """Test that the caching mechanism works correctly."""
        # Mock YoutubeDL extract_info
        mock_info = {'id': 'test_vid_id', 'title': 'Test Video', 'duration': 120}
        mock_ytdl_instance = MagicMock()
        mock_ytdl_instance.extract_info.return_value = mock_info
        mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance

        # Mock whisper model
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'segments': [
                {'id': 1, 'text': 'Test transcript', 'start': 0, 'end': 10}
            ]
        }
        mock_whisper.load_model.return_value = mock_model

        # Insert test data into the database to simulate cached data
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transcriptions (video_id, title, embed_url, duration, transcript, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
            ('test_vid_id', 'Cached Video', 'https://www.youtube.com/embed/test_vid_id', 120, json.dumps([{'id': 1, 'text': 'Cached transcript'}]))
        )
        conn.commit()
        conn.close()

        # Call the function
        url = "https://www.youtube.com/watch?v=test_vid_id"
        result = transcribe_youtube_video(url)

        # Assert that the function returns the cached data
        self.assertIsNotNone(result, "No result returned from transcribe_youtube_video")
        self.assertEqual(result['title'], 'Cached Video')
        self.assertEqual(result['transcript'][0]['text'], 'Cached transcript')

        # Verify that the model was not called (since we used cached data)
        mock_whisper.load_model.assert_not_called()

    @patch('transcriber.yt_dlp.YoutubeDL')
    def test_error_handling_for_invalid_urls(self, mock_ytdl):
        """Test error handling for invalid URLs."""
        # Mock YoutubeDL to raise an exception
        mock_ytdl_instance = MagicMock()
        mock_ytdl_instance.extract_info.side_effect = Exception("Invalid URL")
        mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance

        # Call the function with an invalid URL
        url = "https://www.youtube.com/watch?v=invalid_url"
        result = transcribe_youtube_video(url)

        # Assert that the function returns None for invalid URLs
        self.assertIsNone(result, "Function should return None for invalid URLs")


if __name__ == '__main__':
    unittest.main()
