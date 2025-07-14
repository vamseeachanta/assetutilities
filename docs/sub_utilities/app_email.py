"""
step 1: rename filename from app_email.py to app.py prior to running
step2: Use below link to downgrade security for gmail account which is used to send emails.
https://myaccount.google.com/u/1/lesssecureapps
"""

from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)
mail = Mail(app)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = "myID@gmail.com"
app.config["MAIL_PASSWORD"] = "****"
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
mail = Mail(app)


@app.route("/")
def index():
    msg = Message("Hello", sender="myID@gmail.com", recipients=["abc@gmail.com"])
    msg.body = "Hello Flask message sent from Flask-Mail"
    mail.send(msg)
    return "Sent"


if __name__ == "__main__":
    app.run(debug=True)
