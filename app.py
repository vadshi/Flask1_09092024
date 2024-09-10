from flask import Flask

app = Flask(__name__)


@app.route("/")  # Это первый URL, который мы будет обрабатывать
def hello_world():  # Эта функция-обработчик будет вызвана при запросе этого урла.
    return "Hello, World!"


if __name__ == "__main__":
    app.run(debug=True)
