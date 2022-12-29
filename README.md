# Bid Frenzy!
#### Video Demo:  <URL https://www.youtube.com/watch?v=07QwSRYMB6s>
#### Description:

It is a marketplace site where users can offer items for sale, as well as make, accept, and reject bids for those offers.\
It was created using HTML, CSS, Bootstrap, JavaScript, Python, SQLite3, and Flask. \

I created an HTML template called layout.html, and all other HTML pages extend this layout using the "extends" funcitonality provided by Flask. The Navbar was created using Bootstrap, as were many notifications that pop up when using the app.

Much of the Flask functionality was modeled on the code we used in a prior CS50 Flask project. I used a helpers.py page to define "login_required" and "apology", altered some using instruction from the Flask documentation site.

SQLite3 is embedded to provide a database for all information stored on this site. The database is updated using Python and SQL syntax within app.py

app.py defines the functions which provide all of the functionality of the site:

index() populates the main page of the site, where items the user has put up for sale are listed. This page can be loaded initially with a GET request, or via a POST request after accepting one of the bids on the item, which will refresh the page with the updated information. 

login() is the landing page if session.get("user_id") is None, as described in login_required(). It has a link to a register page. It is also loaded immediately when the user logs out. Logging in invokes the index() function, and loads the main page of the site.

register() utilizes werkzeug.security's generate_password_hash, which saves a hash for the password given during registration, and check_password_hash, which ensures the correct password has been provided at login.

logout() runs session.clear(), and hence redirects to the login page.

forsale() displays all items that are currently for sale (by any user other than the current user), and allows for the current user to bid on that item. It also displays whether the user has previously bid on the item.

transactions() displays all items bought and sold by the user. The functionality that determines whether "Bought" or "Sold" are currently being displayed is performed using JavaScript.

createsale() allows the user to upload a new item to be sold on the site, and allows for photos of the object.

yourbids() displays all past bids by the user, whether the bid was accepted, denied, or is still pending.

apology.html is a page which is loaded whenever the user has incorrectly used the platform. It displays a message suggesting the proper usage of the site.