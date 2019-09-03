from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'grades.sqlite')
db = SQLAlchemy(app)
ma = Marshmallow(app)


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    player = db.Column(db.String(25))
    level = db.Column(db.Integer)
    score = db.Column(db.Integer)

    def __init__(self, player, level, score):
        self.player = player
        self.level = level
        self.score = score

class GameSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ('id', 'timestamp', 'player', 'level', 'score')


game_schema = GameSchema()
games_schema = GameSchema(many=True)


# endpoint to create new game
@app.route("/game", methods=["POST"])
def add_game():
    player = request.json['player']
    level = request.json['level']
    score = request.json['score']

    new_game = Game(player, level, score)

    db.session.add(new_game)
    db.session.commit()

    return game_schema.jsonify(new_game) 


# endpoint to show highscores 
@app.route("/highscores", methods=["GET"])
def get_game():
    all_games = db.session.query(Game).order_by(Game.score.desc()).limit(10)
    result = games_schema.dump(all_games)
    print(result)
    return jsonify(result)


# endpoint to show player games
@app.route("/highscores/<player>", methods=["GET"])
def game_detail(player):
    game = db.session.query(Game).filter(Game.player == player).order_by(Game.score.desc()).limit(10)
    result = games_schema.dump(game)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=False)
