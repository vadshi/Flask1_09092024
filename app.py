from flask import Flask

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

about_me = {
   "name": "Вадим",
   "surname": "Шиховцов",
   "email": "vshihovcov@specialist.ru"
}


@app.route("/")  # Это первый URL, который мы будет обрабатывать
def hello_world():  # Эта функция-обработчик будет вызвана при запросе этого урла.
    return "Hello, World!"


@app.route("/about")
def about():
   return about_me


if __name__ == "__main__":
    app.run(debug=True)
