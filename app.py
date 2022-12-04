import os

from cs50 import SQL
from flask import Flask, flash, url_for, render_template, redirect, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from helpers import apology, login_required

UPLOAD_FOLDER = './static/saved/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Confirgure CS50 Library to use SQLite database
db = SQL("sqlite:///bid.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():
    user_id = session["user_id"]
    allItems = db.execute("SELECT * FROM items WHERE ownerId = ? AND saleStatus = ?", user_id, "available")
    for item in allItems:
        item['filename'] = f"./static/saved/{item['filename']}"
        item['bidNumber'] = db.execute("SELECT COUNT(*) FROM bids WHERE sellerId = ? AND itemId = ? AND offerStatus = ?", user_id, item['id'], "active")
        item['bidNumber'] = item['bidNumber'][0]['COUNT(*)']
        # item['bids'] = [1,2,3,4]
        item['allBids'] = db.execute("SELECT * FROM bids WHERE sellerId = ? AND itemId = ? AND offerStatus = ?", user_id, item['id'], "active")
        for item in item['allBids']:
            bidderName = db.execute("SELECT username FROM users WHERE id = ?", item['bidderId'])
            bidderName = bidderName[0]['username']
            item['bidderName'] = bidderName
    
    print(allItems)
    

    
    

    # bidNumber = db.execute("SELECT COUNT(*) WHERE sellerId = ? AND itemId = ? AND offerStatus = ?", user_id, itemId, "active")
    
    
    return render_template("index.html", allItems=allItems)

@app.route("/login", methods=["POST", "GET"])
def login():
    # Forget any user_id
    session.clear()

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["passwordHash"], request.form.get("password")):
            return apology("invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username")
        if not request.form.get("password"):
            return apology("must provide password")
        elif not request.form.get("confirmation"):
            return apology("must confirm password")
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match")
        names2 = db.execute("SELECT DISTINCT(username) FROM users")
        names = []
        for name in names2:
            names.append(name['username'])
        if request.form.get("username") in names:
            return apology("Username already taken")
        hash = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, passwordHash) VALUES(?, ?)", request.form.get("username"), hash)
        user_id = db.execute("SELECT id FROM users WHERE username = ?", request.form.get("username"))
        session["user_id"] = user_id[0]['id']

        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



#--------------------------------------------------------------------------------------

@app.route("/forsale", methods=["GET", "POST"])
def forsale():
    if request.method == "POST":
        user_id = session["user_id"]
        allItems = db.execute("SELECT * FROM items WHERE ownerId != ? AND saleStatus = ?", user_id, "available")
        for item in allItems:
            item['filename'] = f"./static/saved/{item['filename']}"
        
        for key in request.form:
            if key.startswith('biditem'):
                itemId = key.partition('--')[-1]
                value = request.form[key]
                value = '${:,.2f}'.format(float(value))
        
        sellerId = db.execute("SELECT ownerId FROM items WHERE id = ?", itemId)
        sellerId = sellerId[0]['ownerId']
        
        db.execute("INSERT INTO bids (itemId, bidderId, sellerId, offerPrice, offerStatus, datetime) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)", itemId, user_id, sellerId, value, "active")
    

        return render_template("forsale.html", allItems=allItems)
    else:
        user_id = session["user_id"]
        allItems = db.execute("SELECT * FROM items WHERE ownerId != ? AND saleStatus = ?", user_id, "available")
        for item in allItems:
            item['filename'] = f"./static/saved/{item['filename']}"
        return render_template("forsale.html", allItems=allItems)

@app.route("/offers")
def offers():
    user_id = session["user_id"]
    # allItems = db.execute("SELECT * FROM items WHERE ownerId = ? AND saleStatus = ?", user_id, "available")
    # for item in allItems:
    #     item['filename'] = f"./static/saved/{item['filename']}"
    
    allBids = db.execute("SELECT * FROM bids WHERE sellerId = ? AND offerStatus = ?", user_id, "active")
    for bid in allBids:
        print(bid)


    return render_template("offers.html")

@app.route("/transactions")
def transactions():
    return render_template("transactions.html")

@app.route("/createsale", methods=["GET", "POST"])
def createsale():
    user_id = session["user_id"]
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return apology("No file selected!")
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return apology("Filename invalid")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            itemName = request.form.get("item-name")
            itemDescription = request.form.get("item-description")
            itemPrice = request.form.get("item-price")
            itemStatus = "available"
            db.execute("INSERT INTO items (name, description, filename, ownerId, askingPrice, saleStatus) VALUES(?, ?, ?, ?, ?, ?)", itemName, itemDescription, filename, user_id, itemPrice, itemStatus)

            message="Item Successfully Uploaded!"
            return render_template("index.html", message=message)
    else:
        thing = "Fresh load!"
        return render_template("createsale.html", thing=thing)

@app.route("/yourbids")
def yourbids():
    return render_template("yourbids.html")




















#---------------------------------------------------------
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# @app.route('/createsale', methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         # check if the post request has the file part
#         if 'file' not in request.files:
#             flash('No file part')
#             return apology("No file included")
#         file = request.files['file']
#         # If the user does not select a file, the browser submits an
#         # empty file without a filename.
#         if file.filename == '':
#             flash('No selected file')
#             return apology("No file included")
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#             thing="Successful upload!"
#             return render_template("createsale.html", thing=thing)
#     return '''
#     <!doctype html>
#     <title>Upload new File</title>
#     <h1>Upload new File</h1>
#     <form method=post enctype=multipart/form-data>
#       <input type=file name=file>
#       <input type=submit value=Upload>
#     </form>
#     '''