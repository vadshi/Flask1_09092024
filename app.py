from typing import Any
from flask import Flask, jsonify, request, g, abort
from random import choice
from http import HTTPStatus
from pathlib import Path
import sqlite3
from werkzeug.exceptions import HTTPException
# imports for sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String


class Base(DeclarativeBase):
    pass


BASE_DIR = Path(__file__).parent
path_to_db = BASE_DIR / "quotes.db"  # <- тут путь к БД

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'main.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(model_class=Base)
db.init_app(app)



class QuoteModel(db.Model):
    __tablename__ = 'quotes'

    id: Mapped[int] = mapped_column(primary_key=True)
    author: Mapped[str] = mapped_column(String(32), unique=False, index=True)
    text: Mapped[str] = mapped_column(String(255))
  
    def __init__(self, author, text, rating):
        self.author = author
        self.text  = text
        self.rating = rating

    def to_dict(self):
        return {
            "id": self.id,
            "author": self.author,
            "text": self.text
        }

@app.errorhandler(HTTPException)
def handle_exeption(e):
    """Функция для перехвата HTTP ошибок и возврата в виде JSON."""
    return jsonify({"message": e.description}), e.code



# URL: /quotes
@app.route("/quotes")
def get_quotes() -> list[dict[str, Any]]:
    """ Функция неявно преобразовывает список словарей в JSON."""
    quotes_db = db.session.scalars(db.select(QuoteModel)).all()
    quotes = []
    for quote in quotes_db:
        quotes.append(quote.to_dict())
    return jsonify(quotes), 200


@app.route("/quotes/<int:quote_id>")
def get_quote(quote_id: int) -> dict:
    """ Функция возвращает цитату по значению ключа id=quote_id."""
    select_quote = "SELECT * FROM quotes WHERE id = ?"
    cursor = get_db().cursor()
    cursor.execute(select_quote, (quote_id,))
    quote_db = cursor.fetchone()  # Получаем одну запись из БД
    if quote_db:
        keys = ("id", "author", "text", "rating")
        quote = dict(zip(keys, quote_db))
        return jsonify(quote), 200 
    return {"error": f"Quote with id={quote_id} not found"}, 404               


@app.get("/quotes/count")
def quotes_count():
    """Function for task3 of Practice part1."""
    select_count = "SELECT count(*) as count FROM quotes"
    cursor = get_db().cursor()
    cursor.execute(select_count)
    count = cursor.fetchone()
    if count:
        return jsonify(count=count[0]), 200
    abort(503)  # вернем ошибку 503


@app.route("/quotes", methods=['POST'])
def create_quote():
    new_quote = request.json
    insert_quote = "INSERT INTO quotes (author, text, rating) VALUES (?, ?, ?)"
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute(insert_quote, (new_quote['author'], new_quote['text'], new_quote['rating']))
    answer = cursor.lastrowid  # Получаем из БД id новой цитаты
    connection.commit()
    new_quote['id'] = answer
    return jsonify(new_quote), 201


@app.route("/quotes/<int:quote_id>", methods=["PUT"])
def edit_quote(quote_id):
    new_data = request.json
    attributes: set = set(new_data.keys()) & {'author', 'rating', 'text'}

    if "rating" in attributes and new_data["rating"] not in range(1, 6):
        # Валидируем новое значени рейтинга и случае успеха обновляем данные
        attributes.remove("rating")
    if attributes:
        update_quotes = f"UPDATE quotes SET {', '.join(attr + '=?' for attr in attributes)} WHERE id=?"
        params = tuple(new_data.get(attr) for attr in attributes) + (quote_id,)
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute(update_quotes, params)
        rows = cursor.rowcount  
        if rows:
            connection.commit()
            cursor.close()
            responce, status_code = get_quote(quote_id)
            if status_code == 200:
                return responce, HTTPStatus.OK
        connection.rollback()
    else:
        responce, status_code = get_quote(quote_id)
        if status_code == 200:
            return responce, HTTPStatus.OK
    abort(404, f"Quote with id={quote_id} not found.")


@app.route("/quotes/<int:quote_id>", methods=["DELETE"])
def delete_quote(quote_id: int):
    delete_sql = f"DELETE FROM quotes WHERE id = ?"
    params = (quote_id,)
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute(delete_sql, params)  
    rows = cursor.rowcount  # Кол-во измененных строк
    if rows:
        connection.commit()
        cursor.close()         
        return jsonify({"message": f"Quote with id {quote_id} has deleted."}), 200
    connection.rollback()
    abort(404, f"Quote with id={quote_id} not found")


# @app.route("/quotes/filter")
# def filter_quotes():
#    """TODO: change to work with database."
#    filtered_quotes = quotes.copy()
#    # request.args хранит данные, полученные из query parameters
#    for key, value in request.args.items():
#       if key not in ("author", "rating"):
#          return f"Invalid key {key}", HTTPStatus.BAD_REQUEST
#       if key == "rating":
#          value = int(value)
#       filtered_quotes = [quote for quote in filtered_quotes if quote.get(key) == value]
#       # ======== the same as 136 ==========
#       # res_quotes = []
#       # for quote in filtered_quotes:
#       #    if quote[key] == value:
#       #       res_quotes.append(quote)
#       # filtered_quotes = res_quotes.copy() # Делаю независимую копию списка
#       # ===================================
#    return filtered_quotes


if __name__ == "__main__":
   app.run(debug=True)