from typing import Any
from flask import Flask, jsonify
from random import choice


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

about_me = {
   "name": "Вадим",
   "surname": "Шиховцов",
   "email": "vshihovcov@specialist.ru"
}

quotes = [
   {
       "id": 3,
       "author": "Rick Cook",
       "text": "Программирование сегодня — это гонка разработчиков программ, стремящихся писать программы с большей и лучшей идиотоустойчивостью, и вселенной, которая пытается создать больше отборных идиотов. Пока вселенная побеждает."
   },
   {
       "id": 5,
       "author": "Waldi Ravens",
       "text": "Программирование на С похоже на быстрые танцы на только что отполированном полу людей с острыми бритвами в руках."
   },
   {
       "id": 6,
       "author": "Mosher’s Law of Software Engineering",
       "text": "Не волнуйтесь, если что-то не работает. Если бы всё работало, вас бы уволили."
   },
   {
       "id": 8,
       "author": "Yoggi Berra",
       "text": "В теории, теория и практика неразделимы. На практике это не так."
   },

]


@app.route("/")  # Это первый URL, который мы будет обрабатывать
def hello_world():  # Эта функция-обработчик будет вызвана при запросе этого урла.
    return jsonify(hello="Hello, World!"), 200


@app.route("/about")  # Это статический URL
def about():
   return jsonify(about_me), 200


# URL: /quotes
@app.route("/quotes")
def get_quotes() -> list[dict[str, Any]]:
   """ Функция неявно преобразовывает список словарей в JSON."""
   return quotes  


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


if __name__ == "__main__":
   app.run(debug=True)