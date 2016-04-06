from flask import Blueprint, jsonify
from flask.views import View

from models import User, Category, Movie, Comment

api = Blueprint('api', __name__)

class APIView(View):
    def __init__(self, model_class):
        self.model = model_class

    def dispatch_request(self):
        result = [row.to_json() for row in self.model.query.all()]
        return jsonify({"result": result})

api.add_url_rule('/user', view_func=APIView.as_view('user', User))
api.add_url_rule('/category', view_func=APIView.as_view('category', Category))
api.add_url_rule('/movie', view_func=APIView.as_view('movie', Movie))
api.add_url_rule('/comment', view_func=APIView.as_view('comment', Comment))
