# import time

from flask import Flask

app = Flask(__name__)
# time.sleep(600)


@app.route("/")
def hello():
    print("database connection test using sql driver 17")
    # Supply SQL login password and use below

    return "Simple POC to check if working"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5015)
