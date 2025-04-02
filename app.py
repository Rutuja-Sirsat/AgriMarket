from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.secret_key = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///farmer1.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Products(db.Model):
    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fid = db.Column(db.Integer, db.ForeignKey('farmers.fid'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)

    def __repr__(self) -> str:
        return f"{self.product_id} - {self.product_name}"

class Farmers(db.Model):
    fid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"{self.fid} - {self.email}"

class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self) -> str:
        return f"{self.user_id} - {self.email}"

class ShoppingCart(db.Model):
    cart_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'))
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self) -> str:
        return f"{self.cart_id} - {self.product_id} - {self.quantity}"

#Tables are created
with app.app_context():
    db.create_all()

#Home route

@app.route('/')
def first():
    return render_template('first.html')

@app.route('/farmer_signup', methods=['GET','POST'])
def farmer():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Password match validation
        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return render_template('farmersignup.html')

        new_farmer = Farmers(username=username, email=email, password=password)

        try:
            # Add and commit to the database
            db.session.add(new_farmer)
            db.session.commit()
            
            return redirect('/farmer_login') 
        except Exception as e:
            db.session.rollback() 
            flash(f"Error: {str(e)}", "error")
            return render_template('farmersignup.html')

    return render_template('farmersignup.html')

@app.route('/farmer_login', methods=['GET', 'POST'])
def farmer_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Fetch the user from the database
        farmer = Farmers.query.filter_by(username=username).first()

        # Check if the user exists and the password is correct
        if farmer and farmer.password == password:  # Compare plain password
            # Set the user in session
            session['fid'] = farmer.fid
            
            return redirect('/farmer_dashboard')  # Redirect to a dashboard or homepage
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('farmerlogin.html')  # Render the login form

@app.route('/user_signup', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Password match validation
        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return render_template('usersignup.html')

        # Create a new user instance with the plain password
        new_user = Users(username=username, email=email, password=password)

        try:
            # Add and commit to the database
            db.session.add(new_user)
            db.session.commit()
           
            return redirect(url_for('user_login'))  
        except Exception as e:
            db.session.rollback()  # Rollback in case of error
            flash(f"Error: {str(e)}", "error")
            return render_template('usersignup.html')

    return render_template('usersignup.html')

@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Fetch the user from the database
        user = Users.query.filter_by(username=username).first()

        # Check if the user exists and the password is correct
        if user and user.password == password:
            # Set the user in session
            session['user_id'] = user.user_id
            
            
            # Redirect using url_for
            return redirect(url_for('homepage'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('userlogin.html')

@app.route('/add_product', methods=['GET', 'POST'])
def addproduct():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        quantity = request.form['quantity']
        

        fid = session['fid']

        new_product = Products(product_name=name, category=category, price=price, quantity=quantity, fid=fid)

        try:
            # Add and commit to the database
            db.session.add(new_product)
            db.session.commit()
            
            return redirect('/farmer_dashboard')  
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
            return render_template('addproduct.html')
        
    return render_template('addproduct.html')

@app.route('/my_products')
def my_products():
    #For Retrieve the farmer's id from the session
    fid = session.get('fid')

    if not fid:
        flash('Please log in first!', 'warning')
        return redirect(url_for('farmer_login'))

    # Query products associated with this farmer
    products = Products.query.filter_by(fid=fid).all()

    return render_template('myproducts.html', products=products)



@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    # Retrieve the farmer's id from the session
    fid = session.get('fid')

    if not fid:
        flash('Please log in first!', 'warning')
        return redirect(url_for('farmer_login'))

    # Fetch the product by its ID and make sure the logged-in farmer owns it
    product = Products.query.filter_by(product_id=product_id, fid=fid).first()

    if not product:
        flash('Product not found or you do not have permission to edit this product.', 'danger')
        return redirect(url_for('my_products'))

    if request.method == 'POST':
        # Get updated price and quantity from the form
        product.price = request.form['price']
        product.quantity = request.form['quantity']

        try:
            # Commit changes to the database
            db.session.commit()
            
            return redirect(url_for('my_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')

    return render_template('editproduct.html', product=product)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Products.query.get_or_404(product_id)
    try:
        db.session.delete(product)
        db.session.commit()
        
    except:
        db.session.rollback()
        flash('Error deleting product.', 'error')

    return redirect(url_for('my_products'))

@app.route('/farmer_dashboard')
def farmer_dashboard():
    # Ensure the farmer is logged in before showing the dashboard
    if 'fid' not in session:
        flash('Please log in first!', 'warning')
        return redirect(url_for('farmer_login'))

    return render_template('farmer_dashboard.html')


@app.route('/show')
def show():
    alluser = Users.query.all()
    print(alluser)
    return "This show page"

@app.route('/products')
def products():
    # Fetch all products from the database
    all_products = Products.query.all()
    return render_template('products.html', products=all_products)


@app.route('/homepage')
def homepage():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        flash('Please log in to add products to your cart.', 'danger')
        return redirect(url_for('user_login'))

    user_id = session['user_id']
    product_id = request.form['product_id']
    quantity = int(request.form['quantity'])

    product = Products.query.get(product_id)

    # Check if the product has enough quantity
    if product.quantity < quantity:
        flash(f"Only {product.quantity} items available. Please reduce the quantity.", 'danger')
        return redirect(url_for('products'))


    # Check if the product is already in the cart
    existing_cart_item = ShoppingCart.query.filter_by(user_id=user_id, product_id=product_id).first()

    if existing_cart_item:

        existing_cart_item.quantity += int(quantity)
    else:
        
        new_cart_item = ShoppingCart(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(new_cart_item)
    
    # Decrease the available quantity of the product
    product.quantity -= quantity

    db.session.commit()
    
    return redirect(url_for('products'))

@app.route('/view_cart')
def view_cart():
    if 'user_id' not in session:
        flash('Please log in to view your cart.', 'danger')
        return redirect(url_for('user_login'))

    user_id = session['user_id']
    cart_items = ShoppingCart.query.filter_by(user_id=user_id).all()

    products_in_cart = []
    total_price = 0

    for item in cart_items:
        product = Products.query.get(item.product_id)

        # Check if the product exists in the Products table
        if not product:
            flash(f"Product with ID {item.product_id} not found.", 'danger')
            continue  # Skip this iteration if product is None

        total = product.price * item.quantity
        total_price += total
        products_in_cart.append({
            'product_name': product.product_name,
            'quantity': item.quantity,
            'price_per_item': product.price,
            'price': total
        })

    return render_template('cart.html', cart_items=products_in_cart, total_price=total_price)





if __name__ == '__main__':
    app.run(debug=True)