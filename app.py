from flask import Flask, render_template, request, redirect, flash, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from config import MONGO_URI, SECRET_KEY
from datetime import datetime

app = Flask(__name__)

app.config["MONGO_URI"] = MONGO_URI
app.secret_key = SECRET_KEY

mongo = PyMongo(app)
db = mongo.db


# ==========================
# HOME
# ==========================

@app.route("/")
def home():
    products = list(db.products.find())
    return render_template("index.html", products=products)


# ==========================
# REGISTER
# ==========================

@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register-user", methods=["POST"])
def register_user():

    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    user = db.users.find_one({"email": email})

    if user:
        flash("Email already exists!", "danger")
        return redirect("/register")

    password = generate_password_hash(password)

    db.users.insert_one({
        "name": name,
        "email": email,
        "password": password
    })

    flash("Registration Successful", "success")
    return redirect("/login")


# ==========================
# LOGIN
# ==========================

@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/login-user", methods=["POST"])
def login_user():

    email = request.form["email"]
    password = request.form["password"]

    user = db.users.find_one({"email": email})

    if user and check_password_hash(user["password"], password):

        session["user_id"] = str(user["_id"])
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]

        flash("Login Successful", "success")
        return redirect("/")

    flash("Invalid Email or Password", "danger")
    return redirect("/login")


# ==========================
# LOGOUT
# ==========================

@app.route("/logout")
def logout():

    session.clear()

    flash("Logged Out Successfully", "success")

    return redirect("/")


# ==========================
# ADMIN DASHBOARD
# ==========================

@app.route("/admin")
def admin():

    products = list(db.products.find())

    return render_template(
        "admin_dashboard.html",
        products=products
    )


# ==========================
# ADD PRODUCT
# ==========================

@app.route("/add-product", methods=["GET", "POST"])
def add_product():

    if request.method == "POST":

        name = request.form["name"]
        category = request.form["category"]
        price = float(request.form["price"])
        image = request.form["image"]
        description = request.form["description"]

        db.products.insert_one({

            "name": name,
            "category": category,
            "price": price,
            "image": image,
            "description": description

        })

        flash("Product Added Successfully")

        return redirect("/admin")

    return render_template("add_product.html")


# ==========================
# UPDATE PRODUCT
# ==========================

@app.route("/update-product/<id>", methods=["GET", "POST"])
def update_product(id):

    product = db.products.find_one({"_id": ObjectId(id)})

    if request.method == "POST":

        db.products.update_one(

            {"_id": ObjectId(id)},

            {
                "$set": {

                    "name": request.form["name"],
                    "category": request.form["category"],
                    "price": float(request.form["price"]),
                    "image": request.form["image"],
                    "description": request.form["description"]

                }
            }

        )

        flash("Product Updated Successfully")

        return redirect("/admin")

    return render_template(
        "update_product.html",
        product=product
    )


# ==========================
# DELETE PRODUCT
# ==========================

@app.route("/delete-product/<id>")
def delete_product(id):

    db.products.delete_one({
        "_id": ObjectId(id)
    })

    flash("Product Deleted Successfully")

    return redirect("/admin")


# ==========================
# PRODUCTS
# ==========================

@app.route("/products")
def products():

    products = list(db.products.find())

    return render_template(
        "products.html",
        products=products
    )


# ==========================
# PRODUCT DETAILS
# ==========================

@app.route("/product/<id>")
def product_details(id):

    product = db.products.find_one({
        "_id": ObjectId(id)
    })

    if not product:
        flash("Product Not Found", "danger")
        return redirect("/products")

    return render_template(
        "product_details.html",
        product=product
    )


# ==========================
# ADD TO CART
# ==========================

@app.route("/add-to-cart/<id>")
def add_to_cart(id):

    if "user_email" not in session:
        flash("Please Login First", "warning")
        return redirect("/login")

    product = db.products.find_one({
        "_id": ObjectId(id)
    })

    if not product:
        flash("Product Not Found", "danger")
        return redirect("/products")

    cart_item = db.cart.find_one({
        "user": session["user_email"],
        "product_id": id
    })

    if cart_item:

        db.cart.update_one(
            {"_id": cart_item["_id"]},
            {
                "$inc": {
                    "quantity": 1
                }
            }
        )

        flash("Product quantity updated", "success")

    else:

        db.cart.insert_one({

            "user": session["user_email"],
            "product_id": id,
            "name": product["name"],
            "price": product["price"],
            "image": product["image"],
            "quantity": 1

        })

        flash("Product Added To Cart", "success")

    return redirect("/cart")


# ==========================
# CART
# ==========================

@app.route("/cart")
def cart():

    if "user_email" not in session:

        return redirect("/login")

    items = list(

        db.cart.find({

            "user": session["user_email"]

        })

    )

    total = sum(
    item["price"] * item["quantity"]
    for item in items
)

    return render_template(

        "cart.html",

        items=items,

        total=total

    )
    
@app.route("/increase-cart/<id>")
def increase_cart(id):

    if "user_email" not in session:
        return redirect("/login")

    db.cart.update_one(
        {
            "_id": ObjectId(id)
        },
        {
            "$inc": {
                "quantity": 1
            }
        }
    )

    return redirect("/cart")

@app.route("/decrease-cart/<id>")
def decrease_cart(id):

    if "user_email" not in session:
        return redirect("/login")

    item = db.cart.find_one({
        "_id": ObjectId(id)
    })

    if item:

        if item["quantity"] > 1:

            db.cart.update_one(
                {
                    "_id": ObjectId(id)
                },
                {
                    "$inc": {
                        "quantity": -1
                    }
                }
            )

        else:

            db.cart.delete_one({
                "_id": ObjectId(id)
            })

    return redirect("/cart")

@app.route("/remove-cart/<id>")
def remove_cart(id):

    if "user_email" not in session:
        return redirect("/login")

    db.cart.delete_one({
        "_id": ObjectId(id)
    })

    flash("Item Removed", "success")

    return redirect("/cart")




# ==========================
# CHECKOUT
# ==========================

@app.route("/checkout")
def checkout():

    if "user_email" not in session:
        return redirect("/login")

    items = list(
        db.cart.find({
            "user": session["user_email"]
        })
    )

    total = sum(
        item["price"] * item["quantity"]
        for item in items
    )

    return render_template(
        "checkout.html",
        items=items,
        total=total
    )
    
@app.route("/place-order", methods=["POST"])
def place_order():

    if "user_email" not in session:
        return redirect("/login")

    items = list(
        db.cart.find({
            "user": session["user_email"]
        })
    )

    total = sum(
        item["price"] * item["quantity"]
        for item in items
    )

    db.orders.insert_one({

        "user": session["user_email"],

        "fullname": request.form["fullname"],

        "phone": request.form["phone"],

        "address": request.form["address"],

        "city": request.form["city"],

        "state": request.form["state"],

        "pincode": request.form["pincode"],

        "products": items,

        "total": total,

        "status": "Pending",

        "date": datetime.now()

    })

    db.cart.delete_many({
        "user": session["user_email"]
    })

    flash("Order Placed Successfully", "success")

    return redirect("/orders")


# ==========================
# ORDERS
# ==========================

@app.route("/orders")
def orders():

    if "user_email" not in session:
        return redirect("/login")

    orders = list(
        db.orders.find({
            "user": session["user_email"]
        })
    )

    return render_template(
        "orders.html",
        orders=orders
    )

    return render_template(

        "orders.html",

        orders=orders

    )

@app.route("/profile")
def profile():

    if "user_email" not in session:
        return redirect("/login")

    user = db.users.find_one({
        "email": session["user_email"]
    })

    return render_template(
        "profile.html",
        user=user
    )
    
@app.route("/update-profile", methods=["POST"])
def update_profile():

    if "user_email" not in session:
        return redirect("/login")

    db.users.update_one(
        {"email": session["user_email"]},
        {
            "$set": {
                "name": request.form["name"],
                "phone": request.form["phone"],
                "address": request.form["address"]
            }
        }
    )

    flash("Profile Updated Successfully")

    return redirect("/profile")

@app.route("/change-password", methods=["POST"])
def change_password():

    if "user_email" not in session:
        return redirect("/login")

    user = db.users.find_one({
        "email": session["user_email"]
    })

    old_password = request.form["old_password"]
    new_password = request.form["new_password"]

    if not check_password_hash(user["password"], old_password):

        flash("Old Password Incorrect")

        return redirect("/profile")

    db.users.update_one(
        {"email": session["user_email"]},
        {
            "$set": {
                "password": generate_password_hash(new_password)
            }
        }
    )

    flash("Password Changed Successfully")

    return redirect("/profile")



# ==========================
# RUN APP
# ==========================

if __name__ == "__main__":
    app.run(debug=True)