import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

class TestEndToEnd(unittest.TestCase):
    """End-to-end tests for the YouTube Learning Platform application."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Configure the Flask app for testing
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Create temporary database files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.transcriber_db = os.path.join(self.temp_dir.name, 'transcriptions.db')
        self.modules_db = os.path.join(self.temp_dir.name, 'modules.db')
        self.quizzes_db = os.path.join(self.temp_dir.name, 'quizzes.db')
        
        # Set up patchers for database paths
        self.transcriber_patcher = patch('transcriber.Transcriptions_CACHE_DB', self.transcriber_db)
        self.modules_patcher = patch('modules.MODULES_CACHE_DB', self.modules_db)
        self.quizzes_patcher = patch('quizzes.QUIZ_CACHE_DB', self.quizzes_db)
        
        # Start the patchers
        self.transcriber_patcher.start()
        self.modules_patcher.start()
        self.quizzes_patcher.start()
        
        # Initialize databases
        import transcriber
        import modules
        import quizzes
        transcriber.init_database()
        modules.init_course_cache()
        quizzes.QuizCache(self.quizzes_db)
    
    def tearDown(self):
        """Clean up after each test."""
        # Stop the patchers
        self.transcriber_patcher.stop()
        self.modules_patcher.stop()
        self.quizzes_patcher.stop()
        
        # Remove temporary directory and files
        self.temp_dir.cleanup()
    
    @patch('transcriber.whisper')
    @patch('transcriber.yt_dlp.YoutubeDL')
    @patch('modules.TitleGenerator')
    @patch('quizzes.call_nebius_llm')
    def test_complete_workflow(self, mock_call_nebius, mock_title_generator_class, mock_ytdl, mock_whisper):
        """Test the complete workflow from video URL to quiz generation."""
        # Mock YoutubeDL extract_info
        mock_info = {'id': 'test_vid_id', 'title': 'Test Video', 'duration': 120}
        mock_ytdl_instance = MagicMock()
        mock_ytdl_instance.extract_info.return_value = mock_info
        mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance
        
        # Mock whisper model
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'segments': [
                {'id': 1, 'text': 'This is the first segment.', 'start': 0, 'end': 10},
                {'id': 2, 'text': 'This is the second segment.', 'start': 10, 'end': 20}
            ]
        }
        mock_whisper.load_model.return_value = mock_model
        
        # Mock the TitleGenerator
        mock_generator = MagicMock()
        mock_generator.generate_title.return_value = "Generated Title"
        mock_title_generator_class.return_value = mock_generator
        
        # Mock the Nebius LLM API
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
        
        # Step 1: Access the index page
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)
        
        # Step 2: Request modules for a video
        response = self.client.get('/modules?video_id=test_vid_id')
        self.assertEqual(response.status_code, 200)
        
        # Parse the JSON response
        data = json.loads(response.data)
        self.assertIn('modules', data)
        self.assertEqual(len(data['modules']), 1)
        self.assertEqual(data['modules'][0]['title'], "Generated Title")
        
        # Step 3: Generate a quiz for a module
        module_title = data['modules'][0]['title']
        response = self.client.get(f'/generate_quiz?video_id=test_vid_id&module_title={module_title}&difficulty=medium')
        self.assertEqual(response.status_code, 200)
        
        # Parse the JSON response
        data = json.loads(response.data)
        self.assertIn('quiz', data)
        self.assertEqual(len(data['quiz']), 1)
        self.assertEqual(data['quiz'][0]['question'], "What is the main focus of Generated Title?")
        self.assertEqual(data['quiz'][0]['correct_answer'], "A")
        
        # Verify that all the mocks were called
        mock_whisper.load_model.assert_called_once()
        mock_model.transcribe.assert_called_once()
        mock_generator.generate_title.assert_called_once()
        mock_call_nebius.assert_called_once()
    
    @patch('transcriber.whisper')
    @patch('transcriber.yt_dlp.YoutubeDL')
    def test_error_handling_invalid_video(self, mock_ytdl, mock_whisper):
        """Test error handling for invalid video URLs."""
        # Mock YoutubeDL to raise an exception
        mock_ytdl_instance = MagicMock()
        mock_ytdl_instance.extract_info.side_effect = Exception("Invalid URL")
        mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance
        
        # Request modules for an invalid video
        response = self.client.get('/modules?video_id=invalid_video_id')
        
        # Assert that the response is a server error
        self.assertEqual(response.status_code, 500)
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Assert that the response contains an error message
        self.assertIn('error', data)
    
    @patch('transcriber.whisper')
    @patch('transcriber.yt_dlp.YoutubeDL')
    @patch('modules.TitleGenerator')
    @patch('quizzes.call_nebius_llm')
    def test_caching_mechanism(self, mock_call_nebius, mock_title_generator_class, mock_ytdl, mock_whisper):
        """Test that the caching mechanism works correctly across the application."""
        # Mock YoutubeDL extract_info
        mock_info = {'id': 'test_vid_id', 'title': 'Test Video', 'duration': 120}
        mock_ytdl_instance = MagicMock()
        mock_ytdl_instance.extract_info.return_value = mock_info
        mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance
        
        # Mock whisper model
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'segments': [
                {'id': 1, 'text': 'This is the first segment.', 'start': 0, 'end': 10},
                {'id': 2, 'text': 'This is the second segment.', 'start': 10, 'end': 20}
            ]
        }
        mock_whisper.load_model.return_value = mock_model
        
        # Mock the TitleGenerator
        mock_generator = MagicMock()
        mock_generator.generate_title.return_value = "Generated Title"
        mock_title_generator_class.return_value = mock_generator
        
        # Mock the Nebius LLM API
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
        
        # First request to populate the cache
        response = self.client.get('/modules?video_id=test_vid_id')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        module_title = data['modules'][0]['title']
        
        response = self.client.get(f'/generate_quiz?video_id=test_vid_id&module_title={module_title}&difficulty=medium')
        self.assertEqual(response.status_code, 200)
        
        # Reset the mock call counts
        mock_whisper.load_model.reset_mock()
        mock_model.transcribe.reset_mock()
        mock_generator.generate_title.reset_mock()
        mock_call_nebius.reset_mock()
        
        # Second request should use cached data
        response = self.client.get('/modules?video_id=test_vid_id')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(f'/generate_quiz?video_id=test_vid_id&module_title={module_title}&difficulty=medium')
        self.assertEqual(response.status_code, 200)
        
        # Verify that the mocks were not called again (using cached data)
        mock_whisper.load_model.assert_not_called()
        mock_model.transcribe.assert_not_called()
        mock_generator.generate_title.assert_not_called()
        mock_call_nebius.assert_not_called()


if __name__ == '__main__':
    unittest.main()