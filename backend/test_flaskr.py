import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = 'postgresql+psycopg2://postgres:teslim@localhost:5432/trivia'
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
    def test_endpoint_not_available(self):
        test = self.client().get('/question')
        data = json.loads(test.data)

        self.assertEqual(test.status_code, 404)
        self.assertEqual(data['error'], 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Requested resource can not be found')

    def test_get_questions_by_category(self):
        test = self.client().get('/categories/1/questions')
        data = json.loads(test.data)

        self.assertEqual(test.status_code, 200)
        self.assertTrue(len(data[0]['questions']) > 0)
        self.assertTrue(data[0]['total_questions'] > 0)

    def test_get_questions_by_category_400(self):
        test = self.client().get('/categories/134/questions')
        data = json.loads(test.data)

        self.assertEqual(test.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 404)

    def test_create_question(self):
        question = {
            'question': 'Do you love udacity?',
            'answer': 'Yes i really do!',
            'category': '1',
            'difficulty': 1
        }

        check = self.client().post('/questions', json=question)
        data = json.loads(check.data)
        self.assertEqual(check.status_code, 200)
        self.assertTrue(data[0]['success'])

    def test_create_question_404(self):
        question = {
            'question': 'Do you love udacity?',
            'answer': 'Yes i really do!',
            'difficulty': 1
        }
        # tried posting a question with a missing parameter
        check = self.client().post('/questions', json=question)
        data = json.loads(check.data)
        self.assertEqual(check.status_code, 400)
        self.assertEqual(data['success'], False)

    def test_search_question(self):
        search_term = {
            'searchTerm': 'udacity',
        }

        check = self.client().get('/questions', json=search_term)
        data = json.loads(check.data)
        self.assertEqual(check.status_code, 200)
        self.assertTrue(len(data['questions']) > 0)
        self.assertTrue(data['total_questions'] > 0)

    def test_search_question_error(self):
        # not provide a search term

        check = self.client().post('/questions')
        data = json.loads(check.data)

        self.assertEqual(check.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Bad request')
    def test_get_categories(self):
        category = {
            'type': 'Adult Stuff'
        }
        check = self.client().post('/categories', json=category)
        check = self.client().get('/categories')
        data = json.loads(check.data)
        self.assertEqual(check.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(len(data['categories']) > 0)

    def test_error_405_get_all_categories(self):
        # sending a different method to the categories url
        check = self.client().put('/categories')
        data = json.loads(check.data)
        self.assertEqual(check.status_code, 405)
        self.assertEqual(data['error'], 405)
        self.assertEqual(data['message'], "Method not allowed for requested url")
        self.assertEqual(data['success'], False)

        # ----------------------------------------------------------------------------#
        # Tests for /questions GET
        # ----------------------------------------------------------------------------#

    def test_get_all_questions_paginated(self):
        check = self.client().get('/questions?page=1')
        data = json.loads(check.data)
        self.assertEqual(check.status_code, 200)
        self.assertTrue(data['total_questions'] > 0)

    def test_get_all_questions_paginated_error(self):
        # try to get all questions with a page that does not exist
        check = self.client().get('/questions?page=12452512')
        data = json.loads(check.data)
        self.assertEqual(check.status_code, 404)
        self.assertEqual(data['error'], 404)
        self.assertEqual(data['message'], "Requested resource can not be found")
        self.assertEqual(data['success'], False)

    def test_delete_question(self):
        # post a question so it can be deleted
        question = {
            'question': 'Do you love udacity?',
            'answer': 'Yes i really do!',
            'category': '1',
            'difficulty': 1
        }

        check = self.client().post('/questions', json=question)
        data = json.loads(check.data)
        question_id = data[0]['question_id']  # contains id of the new question

        # delete the question just created
        check = self.client().delete(f'/questions/{question_id}')
        data = json.loads(check.data)
        self.assertEqual(check.status_code, 200)
        self.assertTrue(data[0]['success'])


    def test_404_delete_question(self):
        # deletes a question that does not exist
        check = self.client().delete(f'/questions/{1234}')
        data = json.loads(check.data)

        self.assertEqual(check.status_code, 404)
        self.assertEqual(data['error'], 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Requested resource can not be found')

        # ----------------------------------------------------------------------------#
        # Tests for /quizzes POST
        # ----------------------------------------------------------------------------#

    def test_play_quiz_by_category(self):
        quiz = {
            'previous_questions': [1, 2, 3],
            'quiz_category': {
                'type': 'Science',
                'id': '1'
            }
        }
        check = self.client().post('/quizzes', json=quiz)
        data = json.loads(check.data)

        self.assertEqual(check.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(data['question']['question'])
        # check if the question is not in the previous question
        self.assertTrue(data['question']['id'] not in quiz['previous_questions'])

    def test_error_400_play_quiz(self):
        # play quiz with no given parameter
        check = self.client().post('/quizzes')
        data = json.loads(check.data)

        self.assertEqual(check.status_code, 400)
        self.assertEqual(data['error'], 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'Bad request')



        
        



# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()