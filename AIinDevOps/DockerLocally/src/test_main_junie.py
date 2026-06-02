import unittest
import json
from unittest.mock import patch

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

class TestFlaskApplication(unittest.TestCase):
    """Tests for the Flask application routes."""
    
    def setUp(self):
        """Set up a test environment before each test."""
        # Configure the Flask app for testing
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_index_route(self):
        """Test that the index route returns the correct template."""
        # Make a request to the index route
        response = self.client.get('/')
        
        # Assert that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Assert that the response contains expected content
        self.assertIn(b'<!DOCTYPE html>', response.data)
        self.assertIn(b'<title>', response.data)
        
        # Check that the default video ID is included
        self.assertIn(b'UEtBMyzLBFY', response.data)
    
    def test_index_route_with_start_time(self):
        """Test that the index route handles the start time parameter."""
        # Make a request to the index route with a start time
        response = self.client.get('/?t=30')
        
        # Assert that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the start time is included in the response
        self.assertIn(b'start=30', response.data)
    
    @patch('main.transcribe_youtube_video')
    @patch('main.structure_transcript')
    def test_modules_route_success(self, mock_structure, mock_transcribe):
        """Test that the modules route returns structured modules."""
        # Mock the transcribe_youtube_video function
        mock_transcript = {
            'embed_url': 'https://www.youtube.com/embed/test_video_id',
            'transcript': [{'text': 'Test transcript'}]
        }
        mock_transcribe.return_value = mock_transcript
        
        # Mock the structure_transcript function
        mock_modules = [
            {
                'title': 'Test Module',
                'content': [{'text': 'Test content'}],
                'start_time': 0,
                'end_time': 10
            }
        ]
        mock_structure.return_value = mock_modules
        
        # Make a request to the modules route
        response = self.client.get('/modules?video_id=test_video_id')
        
        # Assert that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Assert that the response contains the expected modules
        self.assertIn('modules', data)
        self.assertEqual(data['modules'], mock_modules)
        
        # Verify that the functions were called with the correct parameters
        mock_transcribe.assert_called_once_with('https://www.youtube.com/watch?v=test_video_id')
        mock_structure.assert_called_once_with(mock_transcript)
    
    def test_modules_route_missing_video_id(self):
        """Test that the modules route handles missing video ID."""
        # Make a request to the modules route without a video ID
        response = self.client.get('/modules')
        
        # Assert that the response is a bad request
        self.assertEqual(response.status_code, 400)
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Assert that the response contains an error message
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Video ID is required')
    
    @patch('main.transcribe_youtube_video')
    def test_modules_route_transcription_error(self, mock_transcribe):
        """Test that the modules route handles transcription errors."""
        # Mock the transcribe_youtube_video function to raise an exception
        mock_transcribe.side_effect = Exception("Transcription error")
        
        # Make a request to the modules route
        response = self.client.get('/modules?video_id=test_video_id')
        
        # Assert that the response is a server error
        self.assertEqual(response.status_code, 500)
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Assert that the response contains an error message
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Transcription error')
    
    @patch('main.get_quiz')
    def test_generate_quiz_route_success(self, mock_get_quiz):
        """Test that the generate_quiz route returns a quiz."""
        # Mock the get_quiz function
        mock_questions = [
            {
                "question": "Test question?",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "A",
                "explanation": "Test explanation"
            }
        ]
        mock_get_quiz.return_value = mock_questions
        
        # Make a request to the generate_quiz route
        response = self.client.get('/generate_quiz?video_id=test_video_id&module_title=Test%20Module&difficulty=medium')
        
        # Assert that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Assert that the response contains the expected quiz
        self.assertIn('quiz', data)
        self.assertEqual(data['quiz'], mock_questions)
        
        # Verify that the function was called with the correct parameters
        mock_get_quiz.assert_called_once_with('test_video_id', 'Test Module', 'medium')
    
    def test_generate_quiz_route_missing_parameters(self):
        """Test that the generate_quiz route handles missing parameters."""
        # Make a request to the generate_quiz route without required parameters
        response = self.client.get('/generate_quiz')
        
        # Assert that the response is a bad request
        self.assertEqual(response.status_code, 400)
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Assert that the response contains an error message
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Both video_id and module_title are required')
        
        # Test with video_id but without module_title
        response = self.client.get('/generate_quiz?video_id=test_video_id')
        self.assertEqual(response.status_code, 400)
        
        # Test with module_title but without video_id
        response = self.client.get('/generate_quiz?module_title=Test%20Module')
        self.assertEqual(response.status_code, 400)
    
    @patch('main.get_quiz')
    def test_generate_quiz_route_error(self, mock_get_quiz):
        """Test that the generate_quiz route handles errors."""
        # Mock the get_quiz function to raise an exception
        mock_get_quiz.side_effect = Exception("Quiz generation error")
        
        # Make a request to the generate_quiz route
        response = self.client.get('/generate_quiz?video_id=test_video_id&module_title=Test%20Module')
        
        # Assert that the response is a server error
        self.assertEqual(response.status_code, 500)
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Assert that the response contains an error message
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Quiz generation error')


if __name__ == '__main__':
    unittest.main()
