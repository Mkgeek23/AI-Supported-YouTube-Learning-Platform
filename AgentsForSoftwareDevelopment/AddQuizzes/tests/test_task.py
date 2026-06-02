import unittest
from unittest.mock import patch, MagicMock
from flask import json

from task import app


class TestQuizAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_generate_quiz_missing_params(self):
        response = self.app.get('/generate_quiz')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Both video_id and module_title are required')

    @patch('task.generate_quiz')
    def test_generate_quiz_failure(self, mock_generate_quiz):
        # Configure mock to raise an exception
        mock_generate_quiz.side_effect = Exception("Test error")

        response = self.app.get('/generate_quiz?video_id=test123&module_title=module_1')
        self.assertEqual(response.status_code, 500)
