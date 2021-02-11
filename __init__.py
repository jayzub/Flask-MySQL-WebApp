from flask import Flask, flash, render_template, redirect, url_for, session, request, abort
from passlib.hash import sha256_crypt
from pymysql import escape_string as thwart
from functools import wraps
from datetime import datetime, timedelta
import gc
import pymysql
from flask_wtf import FlaskForm
from wtforms import Form, TextField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_sqlalchemy import SQLAlchemy
from faker import Faker
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, expose, AdminIndexView
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, current_user
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand


import random


app = Flask(__name__)
app.config.from_pyfile('config.py')


db = SQLAlchemy(app)
fake = Faker()

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)


def connection():#
    conn = pymysql.connect(host="localhost", user="root2", passwd='root', db="inventory_db")
    c = conn.cursor()

    return c, conn


class CustomerSignupForm(FlaskForm):
    email = TextField('Email', [DataRequired()])
    password = PasswordField('Password', [DataRequired(), EqualTo('confirm_password', message="Passwords must match.")])
    confirm_password = PasswordField('Confirm Password')
    accept_terms = BooleanField('I accept the Terms of Service and Privacy Notice', [DataRequired()])
    submit = SubmitField('Sign Up')


class CustomerLoginForm(FlaskForm):
    email = TextField('Email', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log in')


class AdminMixin:
    def is_accessible(self):
        return current_user.has_role('superuser')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('security.login', next=request.url))


class Category(db.Model):
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(50), nullable=False)
    create_date = db.Column(db.DateTime(), default=datetime.now())

    subcategories = db.relationship('Subcategory', backref='category', lazy='dynamic')
    products = db.relationship('Product', backref='category', lazy='dynamic')

    def __repr__(self):
        return '<Category: %r>' % self.category_name


class CategoryView(AdminMixin, ModelView):
    form_excluded_columns = ['create_date']
    can_view_details = True
    create_modal = True
    edit_modal = True


class Subcategory(db.Model):
    subcategory_id = db.Column(db.Integer, primary_key=True)
    subcategory_name = db.Column(db.String(50), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=False)
    create_date = db.Column(db.DateTime(), default=datetime.now())

    products = db.relationship('Product', backref='subcategory', lazy='dynamic')

    def __repr__(self):
        return '<Subcategory: %r>' % self.subcategory_name


class SubcategoryView(ModelView):
    form_excluded_columns = ['create_date']
    can_view_details = True
    column_filters = ['category.category_name']
    create_modal = True
    edit_modal = True


store_users = db.Table('store_users',
                       db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                       db.Column('store_id', db.Integer, db.ForeignKey('store.store_id'))
                       )


roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
                       )


class Order(db.Model):
    __tablename__ = "order"

    order_id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.ForeignKey('store.store_id'), nullable=False)
    order_date = db.Column(db.DateTime(), default=datetime.now())
    customer_id = db.Column(db.Integer(), db.ForeignKey('customer.customer_id'), nullable=False)
    delivery_type = db.Column(db.String(10))
    order_status = db.Column(db.String(10), default='open')

    products = db.relationship("OrderProduct", cascade="all, delete-orphan", backref="order")

    def __init__(self, customer_id, store_id, order_date, delivery_type, order_status):
        self.customer_id = customer_id
        self.store_id = store_id
        self.order_date = order_date
        self.delivery_type = delivery_type
        self.order_status = order_status

    def __repr__(self):
        return "Order (%r)" % self.order_id


class OrderView(ModelView):
    form_excluded_columns = ['order_date']
    can_view_details = True
    column_filters = ['store.store_name', 'delivery_type', 'order_status', 'order_date']
    form_choices = {
        'delivery_type': [
            ('Delivery', 'Delivery'),
            ('Pickup', 'Pickup')
        ],
        'order_status': [
            ('open', 'open'),
            ('closed', 'closed'),
            ('cancelled', 'cancelled')
        ]
    }


class Product(db.Model):
    __tablename__ = "product"

    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(50), nullable=False)
    barcode = db.Column(db.String(50))
    brand = db.Column(db.String(100))
    color = db.Column(db.String(50))
    product_size = db.Column(db.String(50))
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'))
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategory.subcategory_id'))
    product_image = db.Column(db.Text())
    product_description = db.Column(db.Text())
    create_date = db.Column(db.DateTime(), default=datetime.now())

    def __init__(self, product_name, color, barcode, product_image):
        self.product_name = product_name
        self.color = color
        self.barcode = barcode
        self.product_image = product_image

    def __repr__(self):
        return "Product (%r)" % self.product_name


class ProductView(ModelView):
    form_excluded_columns = ['create_date']
    column_exclude_list = ['product_description']
    can_view_details = True
    column_searchable_list = ['product_name', 'barcode']
    column_filters = ['category.category_name', 'subcategory.subcategory_name', 'brand']


class StoreProduct(db.Model):
    __tablename__ = "store_product"

    store_id = db.Column(db.Integer, db.ForeignKey("store.store_id"), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.product_id"), primary_key=True)
    price = db.Column(db.Float, nullable=False)
    qty_in_stock = db.Column(db.Integer)

    def __init__(self, store_product, price, store_id):
        self.store_product = store_product
        self.price = price or store_product.price
        self.store_id = store_id or store_product.store_id

    product = db.relationship(Product, lazy="joined")

    def __repr__(self):
        return '<Product: %r>' % self.product.product_name


class StoreProductView(ModelView):
    can_view_details = True
    column_filters = ['product', 'store']


class Store(db.Model):
    __tablename__ = "store"

    store_id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.Text())
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    logo = db.Column(db.Text())
    active = db.Column(db.Boolean(), default=True)
    create_date = db.Column(db.DateTime(), default=datetime.now())

    orders = db.relationship('Order', backref='store', lazy='dynamic')
    products = db.relationship('StoreProduct', cascade="all, delete-orphan", backref="store")
    users = db.relationship('User', secondary=store_users, backref=db.backref('store', lazy='dynamic'))

    def __init__(self, store_name, address, city, state, active):
        self.store_name = store_name
        self.address = address
        self.city = city
        self.state = state
        self.active = active

    def __repr__(self):
        return "Store (%r)" % self.store_name


class StoreView(ModelView):
    form_excluded_columns = ['create_date']
    can_view_details = True
    column_searchable_list = ['store_name']


class OrderProduct(db.Model):
    __tablename__ = "order_product"

    order_id = db.Column(db.Integer, db.ForeignKey("order.order_id"), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.product_id"), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)

    def __init__(self, product, quantity):
        self.product.product_name = product
        self.quantity = quantity

    product = db.relationship(Product, lazy="joined")

    def __repr__(self):
        return '<Product: %r>' % self.product.product_name


class OrderProductView(ModelView):
    can_view_details = True
    column_filters = ['product', 'order_id']


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))

    def __repr__(self):
        return '<Role: %r>' % self.name


class RoleView(ModelView):
    can_view_details = True
    create_modal = True
    edit_modal = True


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(150), nullable=False, unique=True)
    username = db.Column(db.String(150))
    password = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(50))
    active = db.Column(db.Boolean(), default=True)
    create_date = db.Column(db.DateTime(), default=datetime.now())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return '<User: %r>' % self.username


class UserView(ModelView):
    form_excluded_columns = ['create_date']
    column_exclude_list = ['password']
    can_view_details = True
    column_searchable_list = ['username', 'email', 'first_name', 'last_name']
    column_editable_list = column_searchable_list
    column_filters = ['active']
    create_modal = True
    edit_modal = True
    can_export = True


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


class Customer(db.Model):
    customer_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(150), nullable=False, unique=True)
    username = db.Column(db.String(150))
    password = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(50))
    active = db.Column(db.Boolean(), default=True)
    create_date = db.Column(db.DateTime(), default=datetime.now())

    orders = db.relationship('Order', backref='customer', lazy='dynamic')

    def __repr__(self):
        return '<Customer: %r>' % self.username


class CustomerView(ModelView):
    form_excluded_columns = ['create_date']
    column_exclude_list = ['password']
    can_view_details = True
    column_searchable_list = ['username', 'email', 'first_name', 'last_name']
    column_filters = ['active']
    can_export = True


def revenue_past_x_days(x_days=7):
    x = (
        db.session.query(db.func.sum(StoreProduct.price * OrderProduct.quantity)).join(Product).join(OrderProduct)
        .join(Order).filter(
            (Order.order_date > (datetime.now() - timedelta(days=x_days))) & Order.store_id == StoreProduct.store_id)
        .scalar()
    )
    if x:
        return '{:,.2f}'.format(x)
    else:
        return 0.00


# fix this function.
def top_selling_products():
    top_products = db.session.query(OrderProduct, Product, StoreProduct).select_from(OrderProduct).join(Product).join(StoreProduct).order_by(StoreProduct.price.desc()).limit(5).all()
    return top_products


"""def get_units_sold(product):
    units_sold = db.session.query(db.func.sum(OrderProduct.quantity)).filter(OrderProduct == product).scalar()
    return units_sold"""


class AdminView(AdminMixin, ModelView):
    pass


class HomeAdminView(AdminIndexView):
    @login_required
    @expose('/')
    def index(self):
        try:
            open_orders = Order.query.filter_by(order_status='open').all()
            store_count = Store.query.count()
            customer_count = Customer.query.count()
            order_count = Order.query.count()
            user_count = User.query.count()
            product_count = Product.query.count()
            return self.render('admin/index.html', store_count=store_count, customer_count=customer_count,
                               order_count=order_count, user_count=user_count, product_count=product_count,
                               revenue_past_14_days=revenue_past_x_days(14), revenue_past_7_days=revenue_past_x_days(7),
                               revenue_past_1_days=revenue_past_x_days(1), top_selling_products=top_selling_products(),
                               open_orders=open_orders
                               )
        except Exception as e:
            return str(e)


@app.route("/admin/logout/")
def admin_logout():
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for('products'))


class SettingsView(BaseView):
    @login_required
    @expose('/')
    def settings(self):
        return self.render('admin/settings.html')


class SPView(BaseView):
    @login_required
    @expose('/')
    def store_products(self):
        try:
            store_products = db.session.query(Product, StoreProduct).join(StoreProduct).all()
        except Exception as e:
            return str(e)
        return self.render('admin/store_products.html', store_products=store_products)


admin = Admin(app, name='Control Panel', template_mode='bootstrap4', index_view=HomeAdminView())
admin.add_view(ProductView(Product, db.session, name='Products', category="Inventory"))
admin.add_view(CategoryView(Category, db.session, name='Categories', category="Inventory"))
admin.add_view(SubcategoryView(Subcategory, db.session, name='Subcategories', category="Inventory"))
admin.add_view(CustomerView(Customer, db.session, name='Customers'))
admin.add_view(StoreView(Store, db.session, name='Stores', category="Stores"))
admin.add_view(OrderView(Order, db.session, name='Orders', category="Orders"))
admin.add_view(UserView(User, db.session, menu_icon_type='fa', menu_icon_value='fa-users', name='Users', category="Users"))
admin.add_view(AdminView(Role, db.session, name='Roles', category="Users"))
admin.add_view(SPView(name='Store Product', endpoint='store_products'))
admin.add_view(SettingsView(name='Settings', endpoint='settings'))
admin.add_view(OrderProductView(OrderProduct, db.session, category="Orders"))
admin.add_view(StoreProductView(StoreProduct, db.session, category="Stores"))


@app.errorhandler(404)
def page_not_found(e):
    return render_template("2/404.html", error=e)


@app.errorhandler(405)
def method_not_allowed(e):
    return render_template("2/405.html", error=e)


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("2/500.html", error=e)


@app.route('/store_page/')
def store_page():
    try:
        return render_template("2/store/store_page.html")
    except Exception as e:
        return render_template("2/500.html", error=e)


@app.route('/signup_customer/', methods=["GET", "POST"])
def signup_customer():
    try:
        form = CustomerSignupForm()
        if request.method == "POST":
            email = form.email.data
            password = sha256_crypt.encrypt((str(form.password.data)))
            now = datetime.now()
            formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
            x = Customer.query.filter_by(email=thwart(email)).first()

            if x:
                error = "That email is already registered. Sign in or choose another email."
                flash(error)
                return render_template("2/signup_customer.html", title='Customer Signup', form=form)
            else:
                new_customer = Customer(
                    email=thwart(email),
                    password=thwart(password),
                    username=thwart(email),
                    active=1,
                    create_date=formatted_date
                )

                db.session.add(new_customer)
                db.session.commit()
                session['logged_in'] = True
                session['email'] = email
                flash("Thanks for signing up!")
                return redirect(url_for('dashboard'))

        return render_template('2/signup_customer.html', title='Customer Signup', form=form)

    except Exception as e:
        return str(e)


@app.route('/login_customer/', methods=["GET", "POST"])
def login_customer():
    try:
        form = CustomerLoginForm()
        if request.method == "POST":
            email = form.email.data
            password = form.password.data

            account = Customer.query.filter_by(email=thwart(email)).first()

            if account and sha256_crypt.verify(password, account.password):
                if account.active is True:
                    session['logged_in'] = True
                    session['email'] = email
                    flash('Logged in successfully!')
                    return redirect(url_for('dashboard'))
                else:
                    flash("Account is not active")
            else:
                flash("Invalid credentials. Try again")
        return render_template('2/login_customer.html', title='Login Customer', form=form)
    except Exception as e:
        return str(e)


def customer_login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login_customer'))
    return wrap


@app.route("/logout/")
def logout():
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for('products'))


@app.route('/dashboard/')
@customer_login_required
def dashboard():
    try:
        return render_template("2/dashboard.html")
    except Exception as e:
        return render_template("2/500.html", error=e)


@app.route('/')
@app.route('/products/')
def products():
    try:
        c, conn = connection()
        c.execute("SELECT barcode, product_name, product_size, product_image, store_name, price, MIN(price) as "
                  "min_price, stock_count FROM PRODUCTS JOIN STORE_PRICES on PRODUCTS.product_id= "
                  "STORE_PRICES.product_id JOIN STORES on STORES.store_id= STORE_PRICES.store_id GROUP BY barcode")
        rows = c.fetchall()

        c.execute("SELECT barcode, store_name, price FROM STORE_PRICES JOIN STORES on STORES.store_id = "
                  "STORE_PRICES.store_id JOIN PRODUCTS on PRODUCTS.product_id = STORE_PRICES.product_id ORDER BY price")
        rows_2 = c.fetchall()
        return render_template('2/products.html', title='Products', products=rows, subs=rows_2)
    except Exception as e:
        return str(e)
    finally:
        c.close()
        conn.close()


@app.route('/search/', methods=['GET', 'POST'])
def search():
    c, conn = connection()
    if request.method == "POST":
        find_item = "%" + request.form['item'] + "%"
        find_barcode = request.form['item']
        # search by Barcode or ItemName
        c.execute("SELECT barcode, product_name, product_size, product_image, store_name, price, stock_count FROM "
                  "PRODUCTS JOIN STORE_PRICES on STORE_PRICES.product_id= PRODUCTS.product_id JOIN STORES on "
                  "STORE_PRICES.store_id= STORES.store_id WHERE barcode LIKE %s or product_name LIKE %s ORDER BY price",
                  (find_barcode, find_item))
        rows = c.fetchall()
        # all in the search box will return all the tuples
        if len(rows) == 0:
            return redirect(url_for('search'))
        return render_template('2/search.html', title='Search', products=rows)
    return render_template('2/search.html')


@app.route('/search/<find>')
def search_find(find):
    c, conn = connection()
    # search by Barcode or ItemName
    c.execute("SELECT barcode, product_name, product_size, product_image, store_name, price, stock_count FROM PRODUCTS "
              "JOIN STORE_PRICES on STORE_PRICES.product_id= PRODUCTS.product_id JOIN STORES on STORE_PRICES.store_id= "
              "STORES.store_id WHERE barcode LIKE %s or product_name LIKE %s ORDER BY price", (find, find))
    rows = c.fetchall()
    # all in the search box will return all the tuples
    if len(rows) == 0:
        return redirect(url_for('search'))
    return render_template('2/search.html', title='Search', products=rows)


@app.route('/search_related/', methods=['GET', 'POST'])
def search_related():
    c, conn = connection()
    if request.method == "POST":
        find = request.form['item']
        # search by Barcode or ItemName
        c.execute("SELECT barcode, product_name, product_size, product_image, store_name, price, MIN(price) as "
                  "min_price, stock_count FROM PRODUCTS JOIN STORE_PRICES on STORE_PRICES.product_id= "
                  "PRODUCTS.product_id JOIN STORES on STORES.store_id = STORE_PRICES.store_id WHERE category_id = "
                  "(SELECT category_id from PRODUCTS WHERE barcode LIKE %s OR product_name LIKE %s) GROUP BY barcode",
                  (find, find))
        rows = c.fetchall()

        c.execute("SELECT barcode, store_name, price FROM STORE_PRICES JOIN STORES on STORES.store_id = "
                  "STORE_PRICES.store_id JOIN PRODUCTS on PRODUCTS.product_id = STORE_PRICES.product_id ORDER BY price")
        rows_2 = c.fetchall()
        # all in the search box will return all the tuples
        if len(rows) == 0:
            return redirect(url_for('products'))
        return render_template('2/search_related.html', title='Search Related', products=rows, subs=rows_2)
    return render_template('2/search_related.html')


@app.route('/add', methods=['POST'])
def add_product_to_cart():
    c = None
    try:
        quantity = int(request.form['quantity'])
        barcode = request.form['barcode']
        store_name = request.form['store_name']
        # validate the received values
        if quantity and barcode and store_name and request.method == 'POST':
            c, conn = connection()
            c.execute("SELECT barcode, product_name, product_size, product_image, store_name, price FROM "
                      "PRODUCTS JOIN STORE_PRICES ON STORE_PRICES.product_id = PRODUCTS.product_id JOIN STORES ON "
                      "STORES.store_id = STORE_PRICES.store_id WHERE barcode = %s AND store_name = %s", (barcode, store_name))
            row = c.fetchone()

            itemArray = {row[0]: {'product_name': row[1], 'barcode': row[0], 'quantity': quantity, 'product_image': row[3], 'store_name': row[4], 'price': float(row[5])}}
            store_array = {row[4]: itemArray}

            all_total_price = 0
            all_total_quantity = 0

            session.modified = True
            if 'store_cart' in session:
                if row[4] in session['store_cart']:
                    for store, store_items in session['store_cart'].items():
                        if row[4] == store:
                            for item, item_details in store_items.items():
                                if row[0] in session['store_cart'][store]:
                                    if row[0] == item:
                                        old_quantity = item_details['quantity']
                                        total_quantity = old_quantity + quantity
                                        item_details['quantity'] = total_quantity
                                else:
                                    session['store_cart'][store] = array_merge(session['store_cart'][store], itemArray)
                else:
                    session['store_cart'] = array_merge(session['store_cart'], store_array)
            else:
                session['store_cart'] = store_array

            flash("Product added to cart")
            return redirect(request.referrer)
        else:
            return 'Error while adding item to cart'
    except Exception as e:
        print(e)
    finally:
        c.close()
        conn.close()


@app.route('/empty')
def empty_cart():
    try:
        session.clear()
        return redirect(url_for('products'))
    except Exception as e:
        print(e)


@app.route('/empty_all')
def empty_all_carts():
    try:
        session.clear()
        return redirect(url_for('products'))
    except Exception as e:
        print(e)


@app.route('/delete/<string:barcode>')
def delete_product(barcode):
    try:
        all_total_quantity = 0
        session.modified = True

        for item in session['cart_item'].items():
            if item[0] == barcode:
                session['cart_item'].pop(item[0], None)
                if 'cart_item' in session:
                    for key, value in session['cart_item'].items():
                        individual_quantity = int(session['cart_item'][key]['quantity'])
                        all_total_quantity = all_total_quantity + individual_quantity
                break

        if all_total_quantity == 0:
            session.clear()
        else:
            session['all_total_quantity'] = all_total_quantity

        return redirect(request.referrer)
    except Exception as e:
        print(e)


def array_merge(first_array, second_array):
    if isinstance(first_array, list) and isinstance(second_array, list):
        return first_array + second_array
    elif isinstance(first_array, dict) and isinstance(second_array, dict):
        return dict(list(first_array.items()) + list(second_array.items()))
    elif isinstance(first_array, set) and isinstance(second_array, set):
        return first_array.union(second_array)
    return False


@app.route('/product_card/')
def product_card():
    try:
        return render_template("2/product_card.html")
    except Exception as e:
        return render_template("2/product_card.html", error=e)


if __name__ == "__main__":
    app.run()
