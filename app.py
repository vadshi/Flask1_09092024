from typing import Any
from flask import Flask, jsonify, request, g, abort
from random import choice
from http import HTTPStatus
from pathlib import Path
import sqlite3
from werkzeug.exceptions import HTTPException


BASE_DIR = Path(__file__).parent
path_to_db = BASE_DIR / "quotes.db"  # <- тут путь к БД

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(path_to_db)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.errorhandler(HTTPException)
def handle_exeption(e):
    """Функция для перехвата HTTP ошибок и возврата в виде JSON."""
    return jsonify({"message": e.description}), e.code


def new_table(name_db: str):
    create_table = """
    CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author TEXT NOT NULL,
    text TEXT NOT NULL,
    rating INTEGER NOT NULL
    );
    """
    connection = sqlite3.connect(name_db)
    cursor = connection.cursor()
    cursor.execute(create_table)
    connection.commit()
    cursor.close()
    connection.close()

# quotes = [
#    {
#        "id": 3,
#        "author": "Rick Cook",
#        "text": "Программирование сегодня — это гонка разработчиков программ, стремящихся писать программы с большей и лучшей идиотоустойчивостью, и вселенной, которая пытается создать больше отборных идиотов. Пока вселенная побеждает."
#    },
#    {
#        "id": 5,
#        "author": "Waldi Ravens",
#        "text": "Программирование на С похоже на быстрые танцы на только что отполированном полу людей с острыми бритвами в руках."
#    },
#    {
#        "id": 6,
#        "author": "Mosher’s Law of Software Engineering",
#        "text": "Не волнуйтесь, если что-то не работает. Если бы всё работало, вас бы уволили."
#    },
#    {
#        "id": 8,
#        "author": "Yoggi Berra",
#        "text": "В теории, теория и практика неразделимы. На практике это не так."
#    },

# ]


# URL: /quotes
@app.route("/quotes")
def get_quotes() -> list[dict[str, Any]]:
    """ Функция неявно преобразовывает список словарей в JSON."""
    select_quotes = "SELECT * FROM quotes"
    cursor = get_db().cursor()
    cursor.execute(select_quotes)
    quotes_db = cursor.fetchall() # get list[tuple]
    # Подготовка данных для отправки в правильном формате
    # Необходимо выполнить преобразование:
    # list[tuple] -> list[dict]
    keys = ("id", "author", "text", "rating")
    quotes = []
    for quote_db in quotes_db:
        quote = dict(zip(keys, quote_db))
        quotes.append(quote)
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
   for quote in quotes:
      if quote["id"] == quote_id:
         quotes.remove(quote)
         return jsonify({"message": f"Quote with id={quote_id} has deleted."}), 200 
   return {"error": f"Quote with id={quote_id} not found."}, 404  


@app.route("/quotes/filter")
def filter_quotes():
   filtered_quotes = quotes.copy()
   # request.args хранит данные, полученные из query parameters
   for key, value in request.args.items():
      if key not in ("author", "rating"):
         return f"Invalid key {key}", HTTPStatus.BAD_REQUEST
      if key == "rating":
         value = int(value)
      filtered_quotes = [quote for quote in filtered_quotes if quote.get(key) == value]
      # ======== the same as 136 ==========
      # res_quotes = []
      # for quote in filtered_quotes:
      #    if quote[key] == value:
      #       res_quotes.append(quote)
      # filtered_quotes = res_quotes.copy() # Делаю независимую копию списка
      # ===================================
   return filtered_quotes


if __name__ == "__main__":
   new_table('quotes.db')
   app.run(debug=True)