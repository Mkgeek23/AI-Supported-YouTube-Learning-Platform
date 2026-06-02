import unittest
import os
from unittest.mock import patch, MagicMock

import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import transcriber
import modules
import quizzes

class TestModuleInteractions(unittest.TestCase):
    """Tests for the interactions between modules."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Use in-memory databases for testing
        self.transcriber_db_path = 'transcriptions.db'
        self.modules_db_path = 'modules.db'
        self.quizzes_db_path = 'quizzes.db'
        
        # Save original paths
        self.original_transcriber_path = transcriber.Transcriptions_CACHE_DB
        self.original_modules_path = modules.MODULES_CACHE_DB
        self.original_quizzes_path = quizzes.QUIZ_CACHE_DB
        
        # Set test paths
        transcriber.Transcriptions_CACHE_DB = self.transcriber_db_path
        modules.MODULES_CACHE_DB = self.modules_db_path
        quizzes.QUIZ_CACHE_DB = self.quizzes_db_path
        
        # Initialize databases
        transcriber.init_database()
        modules.init_course_cache()
        quizzes.QuizCache(self.quizzes_db_path)
    
    def tearDown(self):
        """Clean up after each test."""
        # Delete the test database files
        if os.path.exists(self.transcriber_db_path):
            os.remove(self.transcriber_db_path)
        if os.path.exists(self.modules_db_path):
            os.remove(self.modules_db_path)
        if os.path.exists(self.quizzes_db_path):
            os.remove(self.quizzes_db_path)
        # Restore original paths
        transcriber.Transcriptions_CACHE_DB = self.original_transcriber_path
        modules.MODULES_CACHE_DB = self.original_modules_path
        quizzes.QUIZ_CACHE_DB = self.original_quizzes_path
    
    @patch('transcriber.whisper')
    @patch('transcriber.yt_dlp.YoutubeDL')
    def test_transcriber_to_modules_pipeline(self, mock_ytdl, mock_whisper):
        """Test the pipeline from transcriber to modules."""
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
        
        # Mock the TitleGenerator to avoid actual model loading
        with patch('modules.TitleGenerator') as mock_title_generator_class:
            # Mock the TitleGenerator instance
            mock_generator = MagicMock()
            mock_generator.generate_title.return_value = "Generated Title"
            mock_title_generator_class.return_value = mock_generator
            
            # Call the transcribe function
            url = "https://www.youtube.com/watch?v=test_vid_id"
            transcript = transcriber.transcribe_youtube_video(url)
            
            # Assert that the transcript was created correctly
            self.assertIsNotNone(transcript)
            self.assertEqual(transcript['title'], 'Test Video')
            self.assertEqual(len(transcript['transcript']), 2)
            
            # Call the structure_transcript function with the transcript
            result_modules = modules.structure_transcript(transcript)
            
            # Assert that the modules were created correctly
            self.assertIsNotNone(result_modules)
            self.assertEqual(len(result_modules), 1)  # All segments should be in one module (less than CHUNK_SIZE)
            self.assertEqual(result_modules[0]['title'], "Generated Title")
            self.assertEqual(len(result_modules[0]['content']), 2)


    @patch('modules.get_cached_modules')
    @patch('quizzes.CourseDesignerAgent')
    def test_modules_to_quizzes_pipeline(self, mock_agent_class, mock_get_cached_modules):
        """Test the pipeline from modules to quizzes."""
        # Mock get_cached_modules to return test modules
        modules_data = [
            {
                'title': 'Module 1',
                'content': [{'text': 'Content 1'}],
                'start_time': 0,
                'end_time': 60
            }
        ]
        mock_get_cached_modules.return_value = modules_data
        
        # Mock CourseDesignerAgent to return test questions
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        questions = [
            {
                "question": "Test question?",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "A",
                "explanation": "Test explanation"
            }
        ]
        mock_agent.generate_quiz_questions.return_value = questions

        with pytest.raises(ValueError, match="No modules found in cache"):
            # Call the generate_all_module_quizzes function
            result = quizzes.generate_all_module_quizzes("test_vid_id", "medium")

    @patch('transcriber.whisper')
    @patch('transcriber.yt_dlp.YoutubeDL')
    @patch('modules.TitleGenerator')
    @patch('quizzes.CourseDesignerAgent')
    def test_full_pipeline(self, mock_agent_class, mock_title_generator_class, mock_ytdl, mock_whisper):
        """Test the full pipeline from video URL to quiz generation."""
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
        
        # Mock CourseDesignerAgent
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        questions = [
            {
                "question": "Test question?",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "A",
                "explanation": "Test explanation"
            }
        ]
        mock_agent.generate_quiz_questions.return_value = questions
        
        # Step 1: Transcribe the video
        url = "https://www.youtube.com/watch?v=test_vid_id"
        transcript = transcriber.transcribe_youtube_video(url)
        
        # Step 2: Structure the transcript into modules
        result_modules = modules.structure_transcript(transcript)
        
        # Step 3: Generate quizzes for the modules
        module_title = result_modules[0]['title']
        result_quiz = quizzes.get_quiz("test_vid_id", module_title, "medium")
        
        # Assert that the final quiz was created correctly
        self.assertIsNotNone(result_quiz)
        self.assertEqual(len(result_quiz), 1)
        self.assertEqual(result_quiz[0]['question'], "Test question?")
        self.assertEqual(result_quiz[0]['correct_answer'], "A")


if __name__ == '__main__':
    unittest.main()