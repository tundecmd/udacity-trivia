from calendar import c
from crypt import methods
from hashlib import new
from http.client import NETWORK_AUTHENTICATION_REQUIRED
from multiprocessing.connection import answer_challenge
from tkinter import N
from unicodedata import category

from models import Category
import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10


def paginate_response(request, Model):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    paginated_res = Model.query.all()[start:end]

    return [res.format() for res in paginated_res]


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @done: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app)

    """
    @done: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type, Authorization')
        response.headers.add(
            'Access-Control-Allow-Headers',
            'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    """
    @done:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/categories', methods=["GET"])
    def get_categories():
        categories_db = Category.query.all()
        if not categories_db:
            abort(404)
        categories = {}
        for category in categories_db:
            categories[f"{category.id}"] = category.type

        return jsonify({
            "categories": categories
        }), 200

    """
    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    @app.route('/questions', methods=["GET"])
    def get_questions():

        questions_db = paginate_response(request, Question)

        if not questions_db:
            abort(404)

        return jsonify({
            "questions": questions_db,
            "total_questions": Question.query.count(),
            "categories": {category.id: category.type for category in Category.query.all()},
            "current_category": "History"
        }), 200

    """

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<int:question_id>', methods=["DELETE"])
    def delete_question(question_id):
        question = Question.find_question_byId(question_id)
        if not question:
            abort(404)
        else:
            try:
                question.delete()
                return {"message": "question successfully deleted"}, 204
            except BaseException:
                db.session.rollback()
                abort(422)
            finally:
                db.session.close()

    """

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/questions', methods=["POST"])
    def create_question():
        request_body = request.get_json()

        question = request_body.get('question')
        answer = request_body.get('answer')
        difficulty = request_body.get('difficulty')
        category = request_body.get('category')

        if not question or not answer or not category or not difficulty:
            abort(400)
        new_question = Question(question, answer, difficulty, category)
        try:
            new_question.insert()
            return {
                "message": "success creating new question"
            }, 201
        except BaseException:
            db.session.rollback()
            abort(422)
        finally:
            db.session.close()

    """

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/searchquestions', methods=["POST"])
    def search_or_question():
        json_data = request.get_json(force=True)
        if len(json_data.keys()) <= 1:
            search_term = f"%{json_data.get('searchTerm')}%"
            if not search_term:
                abort(400)
            results = Question.query.filter(
                Question.question.ilike(search_term))

            response = {
                "questions": [
                    q.format() for q in results],
                "total_questions": results.count(),
                "current_category": "" if len(
                    results.all()) < 1 else Category.query.get(
                    results[0].category).type}
            return response
        else:
            answer = json_data.get('answer')
            question_ = json_data.get('question')
            difficulty = json_data.get('difficulty')
            category_id = json_data.get('category')
            if not (answer and question_ and difficulty and category_id):
                abort(400)
            category = Category.query.get(int(category_id))
            question = Question(
                answer=answer,
                question=question_,
                difficulty=difficulty,
                category=category)
            category.questions_in_category.append(question)
            db.session.commit()

            return {'question': question.question, 'answer': question.answer,
                    'difficulty': question.difficulty, 'category': category.id}

    """
    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:category_id>/questions', methods=["GET"])
    def get_category_questions(category_id):

        category_questions = [
            question.format() for question in Question.query.filter(
                Question.category == category_id).all()]

        if not category_questions:
            abort(404)

        return jsonify({
            "questions": category_questions,
            "total_questions": len(category_questions),
            "current_category": Category.query.filter(Category.id == category_id).first().type
        }), 200

    """
    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=["POST"])
    def play_quiz():
        previous_questions = request.get_json().get('previous_questions')
        quiz_category = request.get_json().get('quiz_category')

        if previous_questions is None or quiz_category is None:
            abort(400)
        if quiz_category["id"] == 0:
            category_questions = [question.format()
                                  for question in Question.query.all()]
        else:
            category_questions = [
                question.format() for question in Question.query.filter(
                    Question.category == quiz_category['id']).all()]

        while True:
            random_question = random.choice(category_questions)
            if random_question['id'] not in previous_questions:
                break
            else:
                return jsonify({
                    "question": None
                })

        return jsonify({
            "question": random_question
        }), 200

    @app.route('/*',
               methods=['GET',
                        'HEAD',
                        'POST',
                        'PUT',
                        'DELETE',
                        'CONNECT',
                        'OPTIONS',
                        'TRACE',
                        'PATCH'])
    def handle_inexistentRoutes():
        abort(404)

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "status": "fail",
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def cannot_proccess(error):
        return jsonify({
            "status": "fail",
            "message": "An error occured while processing your request"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "status": "fail",
            "message": "Invalid request body"
        }), 400

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            "status": "fail",
            "message": "Internal Server Error"
        }), 500

    return app
