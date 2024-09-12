from typing import Any
from flask import Flask, jsonify, request
from random import choice
from http import HTTPStatus
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).parent
path_to_db = BASE_DIR / "store.db"  # <- тут путь к БД

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

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
   connection = sqlite3.connect("store.db")
   cursor = connection.cursor()
   cursor.execute(select_quotes)
   quotes_db = cursor.fetchall() # get list[tuple]
   cursor.close()
   connection.close()
   # Подготовка данных для отправки в правильном формате
   # Необходимо выполнить преобразование:
   # list[tuple] -> list[dict]
   keys = ("id", "author", "text")
   quotes = []
   for quote_db in quotes_db:
      quote = dict(zip(keys, quote_db))
      quotes.append(quote)
   return jsonify(quotes), 200


@app.route("/params/<value>")  # Это пример динамического URL'а
def param_example(value: str):
    return jsonify(param=value)

# /quotes/1
# /quotes/2
# /quotes/3
# /quotes/4
# ....
# /quotes/n
@app.route("/quotes/<int:quote_id>")
def get_quote(quote_id: int) -> dict:
   """ Функция возвращает цитату по значению ключа id=quote_id."""
   for quote in quotes:
      if quote["id"] == quote_id:
         return jsonify(quote), 200 
   return {"error": f"Quote with id={quote_id} not found"}, 404               


@app.get("/quotes/count")
def quotes_count():
   """Function for task3 of Practice part1."""
   return jsonify(count=len(quotes))


@app.route("/quotes/random", methods=["GET"])
def random_quote() -> dict:
   """Function for task4 of Practice part1."""
   return jsonify(choice(quotes))


@app.route("/quotes", methods=['POST'])
def create_quote():
   """ Функция создает новую цитату в списке."""
   new_quote = request.json  # json -> dict
   last_quote = quotes[-1] # Последняя цитата в списке
   new_id = last_quote["id"] + 1
   new_quote["id"] = new_id
   # Мы проверяем наличие ключа rating и его валидность(от 1 до 5)
   rating = new_quote.get("rating")
   if rating is None or rating not in range(1, 6):
      new_quote["rating"] = 1
   quotes.append(new_quote)
   return jsonify(new_quote), 201


@app.route("/quotes/<int:quote_id>", methods=["PUT"])
def edit_quote(quote_id):
   new_data = request.json
   if not set(new_data.keys()) - set(('author', 'rating', 'text')):
      for quote in quotes:
         if quote["id"] == quote_id:
            if "rating" in new_data and new_data["rating"] not in range(1, 6):
               # Валидируем новое значени рейтинга и случае успеха обновляем данные
               new_data.pop("rating")
            quote.update(new_data)
            return jsonify(quote), HTTPStatus.OK
   else:
      return {"error": "Send bad data to update"}, HTTPStatus.BAD_REQUEST 
   return {"error": f"Quote with id={quote_id} not found."}, 404


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
   app.run(debug=True)