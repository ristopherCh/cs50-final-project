from flask import Flask, render_template, request

# Configure application
app = Flask(__name__)

@app.route("/")
def index():
    name = "Jim"
    return render_template("index.html", name=name)

@app.route("/forsale")
def forsale():
    return render_template("forsale.html")

@app.route("/offers")
def offers():
    return render_template("offers.html")

@app.route("/transactions")
def transactions():
    return render_template("transactions.html")

@app.route("/createsale")
def createsale():
    return render_template("createsale.html")

@app.route("/yourbids")
def yourbids():
    return render_template("yourbids.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")