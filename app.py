import os
import datetime

from cs50 import SQL
from flask import Flask, flash, url_for, render_template, redirect, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from helpers import apology, login_required

UPLOAD_FOLDER = './static/saved/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'heic'}

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

@app.route("/", methods=["POST", "GET"])
@login_required
def homepage():
    return index()

@app.route("/index", methods=["POST", "GET"])
@login_required
def index():
    # Get current user ID
    user_id = session["user_id"]
    # Get current username
    user_name = db.execute("SELECT username FROM users WHERE id = ?", user_id)
    user_name = user_name[0]['username']

    # This runs when you click a link to the page:
    if request.method == 'GET':
        # Get all owned, available items
        allItems = db.execute("SELECT * FROM items WHERE ownerId = ? AND saleStatus = ?", user_id, "available")
        for item in allItems:
            # Fix image url
            item['filename'] = f"./static/saved/{item['filename']}"
            # Get total number of bids per item
            item['bidNumber'] = db.execute("SELECT COUNT(*) FROM bids WHERE sellerId = ? AND itemId = ? AND offerStatus = ?", user_id, item['id'], "active")
            item['bidNumber'] = item['bidNumber'][0]['COUNT(*)']
            # Get all bids for current item
            item['allBids'] = db.execute("SELECT * FROM bids WHERE sellerId = ? AND itemId = ? AND offerStatus = ?", user_id, item['id'], "active")
            # For every bid on this one item...
            for bid in item['allBids']:
                # Get the name of the bidder
                bidderName = db.execute("SELECT username FROM users WHERE id = ?", bid['bidderId'])
                bidderName = bidderName[0]['username']
                bid['bidderName'] = bidderName

        # No message is displayed
        message = ""
        return render_template("index.html", allItems=allItems, user_name=user_name, message=message)
    else: 
        # You've clicked "Accept Bid" on index.html
        purchasedBid = request.form.to_dict()
        # Get the bidId associated with the button clicked
        for key, value in purchasedBid.items():
            purchasedBidId = value
        purchasedBidId = int(purchasedBidId)
        # Get the itemId for the button clicked
        itemId = db.execute("SELECT itemId FROM bids WHERE id = ?", purchasedBidId)
        itemId = itemId[0]['itemId']
        
        # Update SQL bids table to reflect approved sale
        db.execute("UPDATE bids SET offerStatus = 'sold' WHERE id = ?", int(purchasedBidId))
        db.execute("UPDATE bids SET offerStatus = 'unavailable' WHERE id != ? AND itemId = ?", int(purchasedBidId), itemId)
        x = datetime.datetime.now()
        current_date = x.strftime("%a") + ' ' + x.strftime("%b") + ' ' + x.strftime("%d") + ' ' + x.strftime("%Y") + ' ' + x.strftime("%X")
        db.execute("UPDATE bids SET saleDate = ? WHERE id = ?", current_date, int(purchasedBidId))

        # Update SQL items table to reflect approved sale
        db.execute("UPDATE items SET saleStatus = 'sold' WHERE id = ?", int(itemId))

        # This is all repeated. Clean this up.
        allItems = db.execute("SELECT * FROM items WHERE ownerId = ? AND saleStatus = ?", user_id, "available")
        for item in allItems:
            item['filename'] = f"./static/saved/{item['filename']}"
            item['bidNumber'] = db.execute("SELECT COUNT(*) FROM bids WHERE sellerId = ? AND itemId = ? AND offerStatus = ?", user_id, item['id'], "active")
            item['bidNumber'] = item['bidNumber'][0]['COUNT(*)']
            item['allBids'] = db.execute("SELECT * FROM bids WHERE sellerId = ? AND itemId = ? AND offerStatus = ?", user_id, item['id'], "active")
            for bid in item['allBids']:
                bidderName = db.execute("SELECT username FROM users WHERE id = ?", bid['bidderId'])
                bidderName = bidderName[0]['username']
                bid['bidderName'] = bidderName

        ## This is for writing the string after selling the item
        itemName = db.execute("SELECT name FROM items WHERE id = ?", itemId)
        itemName = itemName[0]['name']
        itemBuyerId = db.execute("SELECT bidderId FROM bids WHERE id = ?", purchasedBidId)
        itemBuyerId = itemBuyerId[0]['bidderId']
        itemBuyerName = db.execute("SELECT username FROM users WHERE id = ?", itemBuyerId)
        itemBuyerName = itemBuyerName[0]['username']
        itemPrice = db.execute("SELECT offerPrice FROM bids WHERE id = ?", purchasedBidId)
        itemPrice = itemPrice[0]['offerPrice']

        message = f"{itemName} has been sold to {itemBuyerName} for {itemPrice}"
        # return render_template("index.html", message=message)
        
        return render_template("index.html", allItems=allItems, user_name=user_name, message=message)

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
        return redirect("/index")

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
    user_id = session["user_id"]
    allItems = db.execute("SELECT * FROM items WHERE ownerId != ? AND saleStatus = ?", user_id, "available")

    ## Have I bid on this item before?
    pastBids = db.execute("SELECT * FROM bids WHERE bidderId = ?", user_id)
    for item in allItems:
            item['filename'] = f"./static/saved/{item['filename']}"
            sellerName = db.execute("SELECT username FROM users WHERE id = ?", item['ownerId'])[0]['username']
            item['sellerName'] = sellerName
            pastBids = db.execute("SELECT * FROM bids WHERE bidderId = ? AND itemId = ?", user_id, item['id'])
            if len(pastBids) > 0:
                item['pastBids'] = pastBids
        
            
    
    ## When item is bid on:
    if request.method == "POST":
        for key in request.form:
            if key.startswith('biditem'):
                itemId = key.partition('--')[-1]
                value = request.form[key]
                if value == '':
                    return apology('Must provide bid amount')
                value = '${:,.2f}'.format(float(value))
        
        sellerId = db.execute("SELECT ownerId FROM items WHERE id = ?", itemId)
        sellerId = sellerId[0]['ownerId']
        
        x = datetime.datetime.now()
        current_date = x.strftime("%a") + ' ' + x.strftime("%b") + ' ' + x.strftime("%d") + ' ' + x.strftime("%Y") + ' ' + x.strftime("%X")
        
        db.execute("INSERT INTO bids (itemId, bidderId, sellerId, offerPrice, offerStatus, datetime) VALUES (?, ?, ?, ?, ?, ?)", itemId, user_id, sellerId, value, "active", current_date)

        ## Have to replicate this code to get the updated database after the Insert above. Fix this.
        allItems = db.execute("SELECT * FROM items WHERE ownerId != ? AND saleStatus = ?", user_id, "available")
        pastBids = db.execute("SELECT * FROM bids WHERE bidderId = ?", user_id)
        for item in allItems:
            item['filename'] = f"./static/saved/{item['filename']}"
            sellerName = db.execute("SELECT username FROM users WHERE id = ?", item['ownerId'])[0]['username']
            item['sellerName'] = sellerName
            pastBids = db.execute("SELECT * FROM bids WHERE bidderId = ? AND itemId = ?", user_id, item['id'])
            if len(pastBids) > 0:
                item['pastBids'] = pastBids

        message='You have made a bid!'
        return render_template("forsale.html", allItems=allItems, message=message)
    
    else:
        message=''
        return render_template("forsale.html", allItems=allItems, message=message)

@app.route("/transactions", methods=["GET", "POST"])
def transactions():
    # if request.method == "GET":
        user_id = session["user_id"]
        # Get all items you've sold
        soldItems = db.execute("SELECT * FROM items WHERE ownerId = ? AND salestatus = 'sold'", user_id)
        if len(soldItems) > 0:
            for item in soldItems:
                item['filename'] = f"./static/saved/{item['filename']}"
                itemId = item['id']
                saleInfo = db.execute("SELECT * FROM bids WHERE itemId = ? AND offerStatus = 'sold'", itemId)
                if len(saleInfo) > 0:
                    item['bidsInfo'] = saleInfo[0]
                    item['bidsInfo']['bidderName'] = db.execute("SELECT username FROM users WHERE id = ?", item['bidsInfo']['bidderId'])[0]['username']
                else: 
                    soldItems = False
        else:
            soldItems = False

        ## Write script to show all purchased items
        boughtItems = db.execute("SELECT * FROM items JOIN bids ON items.id = bids.itemId WHERE bids.bidderId = ? AND bids.offerStatus = 'sold' AND items.saleStatus = 'sold'", user_id)
        if len(boughtItems) > 0:
            for item in boughtItems:
                item['filename'] = f"./static/saved/{item['filename']}"
                itemId = item['id']
                sellerName = db.execute("SELECT username FROM users WHERE id = ?", item['ownerId'])
                item['sellerName'] = sellerName[0]['username']
                

        ## Capture select dropdown
        

        boughtItems = boughtItems
        return render_template("transactions.html", soldItems = soldItems, boughtItems=boughtItems)
    
    # else:
    #     return render_template("transactions.html", soldItems = soldItems)
        

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
        if request.form.get("item-name") == '':
            return apology("Must enter item name")
        if request.form.get("item-description") == '':
            return apology("Must enter item description")
        if request.form.get("item-price") == '':
            return apology("Must enter item price")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            itemName = request.form.get("item-name")
            itemDescription = request.form.get("item-description")
            itemPrice = request.form.get("item-price")
            itemPrice = '${:,.2f}'.format(float(itemPrice))
            print("hi yes", itemPrice)
            itemStatus = "available"
            db.execute("INSERT INTO items (name, description, filename, ownerId, askingPrice, saleStatus) VALUES(?, ?, ?, ?, ?, ?)", itemName, itemDescription, filename, user_id, itemPrice, itemStatus)

            message="Your sale is now live!"
            return render_template("createsale.html", message=message)
    else:
        message = ''
        return render_template("createsale.html", message=message)

@app.route("/yourbids")
def yourbids():
    user_id = session["user_id"]
    your_bids = db.execute("SELECT * FROM bids LEFT JOIN items ON bids.itemId = items.id WHERE bids.bidderId = ?", user_id)
    for item in your_bids:
        item['filename'] = f"./static/saved/{item['filename']}"
    
    return render_template("yourbids.html", your_bids=your_bids)




















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