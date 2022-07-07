from ast import If
from calendar import c
from crypt import methods
from gettext import Catalog
from hashlib import new
from http.client import NETWORK_AUTHENTICATION_REQUIRED
import json
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


def paginate_response(request, options):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in options]
    currently_displayed_questions = questions[start:end] 
    
    return currently_displayed_questions


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
        response.headers.add('Access-control-Allow-headers', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Headers', 'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    """
    @done:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/categories', methods=["GET"])
    def get_categories():
        categories = Category.query.order_by(Category.id).all()

        if not categories:
            abort(404)

        categoryList = [category.format() for category in categories]

        return jsonify({
            "success": True,
            "categories": categoryList
        }), 200

    """
    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    @app.route('/questions', methods=["GET"])
    def get_questions():
        try:
            questions = Question.query.order_by(Question.id).all()
            categories = Category.query.order_by(Category.id).all()

            # questions_db = paginate_response(request, Question)
            currently_displayed_questions = paginate_response(request, questions)

            if len(currently_displayed_questions) == 0:
                abort(404)

            return jsonify({
                "success": True,
                "questions": currently_displayed_questions,
                "total_questions": len(Question.query.all()),
                "categories": [category.format() for category in categories],
                "current_category": "History"
            }), 200
        except BaseException as e:
            db.session.rollback()
            print(e) 
            abort(422)
        finally:
            db.session.close()


    """

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<int:question_id>', methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()
            if not question:
                abort(404)
            else:
                question.delete()
                options = Question.query.order_by(Question.id).all()
                categories = Category.query.order_by(Category.id).all()
                currently_displayed_questions = paginate_response(request, options)

                return jsonify({
                    "success": True,
                    "questions": currently_displayed_questions,
                    "deleted_question": question_id,
                    "total_questions": len(Question.query.all()),
                    "categories": [categories.format() for category in categories],
                    "current_category": "History"
                })
        except BaseException as e:
            db.session.rollback()
            print(e) 
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
        try:
            request = request.get_json()

            question = request.get('question')
            answer = request.get('answer')
            difficulty = request.get('difficulty')
            category = request.get('category')

            if not question or not answer or not category or not difficulty:
                abort(400)
            options = Question.query.order_by(Question.id).all()
            categories = Category.query.order_by(Category.id).all()

            new_question = Question(question = question, answer = answer, difficulty = difficulty, category = category)
            new_question.insert()
            currently_displaced_questions = paginate_response(request, options)

            # this is wia I am next tin to do is to return jsonify
            return jsonify({
                "questions": currently_displaced_questions,
                "total_questions": len(Question.query.all()),
                "categories":  [category.format() for category in categories],
                "currentCategory": 'History'
            })
        except BaseException as e:
            db.session.rollback()
            print(e)
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
        try:
            request = request.get_json()
            searchKeyword = request.get('searchTerm', None)
            options = Question.query.filter(Question.question.ilike(f'%{searchKeyword}%')).all()
            currently_displaced_questions = paginate_response(request, options)
            return jsonify({
                "questions": currently_displaced_questions,
                "total_questions": len(currently_displaced_questions),
                "current_category": "History"
            })
        
        except BaseException as e:
            print(e)
        
    
    """
    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:category_id>/questions', methods=["GET"])
    def get_category_questions(category_id):
        category = Category.query.filter(id = category_id).one_or_none()
        if not category:
            abort(422)
        
        options = Question.query.filter(Question.category == category_id).order_by(Question.id).all()
        currently_displaced_questions = paginate_response(request, options)
        return jsonify({
            "questions": currently_displaced_questions,
            "total_questions": len(Question.query.all()),
            "currentCategory": category.type
        })


    """
    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=["POST"])
    def play_quiz():
        request = request.get_json()

        previous_questions = request.get('previous_questions', None)
        quiz_category = request.get('quiz_category', None)

        if "previous_questions" in request:
            pass
        else:
            abort(400)

        if "quiz_category" in request:
            pass
        else:
            abort(400)


        if quiz_category['type'] == 'click':
            questions = Question.query.order_by('id').all()
            category = Category.query.filter_by(id = '1').first()
        else:
            questions = Question.query.filter(Question.category == quiz_category['type']).all()
            category = Category.query.filter_by(id = quiz_category['type']).first()

        if questions == []:
            abort(404)

        try:

            filter_questions = []

            # If the previous_question list is empty, no need to filter the questions from the previous questions
            if len(previous_questions) == 0:
                filter_questions = questions

            # If the prevoius_question list is not empty loop through the questions data to remove each of them
            for p in previous_questions:
                filter_questions = filter(lambda a: a.id != p, questions)
                questions = list(filter_questions)
                

            # # Format tha rest of the question data so it can be sent using jsonify
            selection = [question.format() for question in questions]

            # If the question data is not empty, randomly select one question from the list
            if len(selection) != 0: 
                random_selection = random.randrange(len(selection))
                selection = selection[random_selection]
            else:
                selection = []

            return jsonify(
                {
                "success": True,
                "question": selection,
                "currentCategory": category.type
            }
            )

        except Exception as e:
            print(e)
            abort(422)

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

    @app.errorhandler(405)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 405, "message": "method not allowed"}),
            405,
        )
    @app.errorhandler(500)
    def server_error(error):
        return (
            jsonify({"success": False, "error": 500, "message": "Internal server error"}),
            500,
        )

    return app
