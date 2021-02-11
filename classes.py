from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from faker import Faker
import random

fake = Faker()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root2:root@localhost/inventory_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)


def add_customers():
    for _ in range(25):
        customer = Customer(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.email(),
            username=fake.unique.user_name(),
            password=fake.password(),
            phone_number=fake.phone_number(),
            active=random.choices([True, False], [90, 10])[0]
        )
        db.session.add(customer)
    db.session.commit()


def add_stores():
    for _ in range(10):
        store = Store(
            store_name=fake.company(),
            address=fake.address(),
            city=fake.city(),
            state=fake.state(),
            active=random.choices([True, False], [90, 10])[0]
        )
        db.session.add(store)
    db.session.commit()


def add_products():
    for _ in range(150):
        product = Product(
            product_name=fake.unique.word(),
            color=fake.color_name(),
            barcode=fake.ean(length=13)
        )
        db.session.add(product)
    db.session.commit()


def add_orders():
    customers = Customer.query.all()
    stores = Store.query.all()

    for _ in range(40):
        customer = random.choice(customers)
        store = random.choice(stores)
        order_date = fake.date_time_this_year()
        delivery_type = random.choices(['pickup', 'delivery'], [30, 70])[0]
        order_status = random.choices(['open', 'closed', 'canceled'], [5, 80, 15])[0]

        order = Order(
            store_id=store.store_id,
            order_date=order_date,
            customer_id=customer.customer_id,
            delivery_type=delivery_type,
            order_status=order_status
        )
        db.session.add(order)
    db.session.commit()


def add_users():
    for _ in range(35):
        user = User(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.email(),
            username=fake.unique.user_name(),
            password=fake.password(),
            phone_number=fake.phone_number(),
            active=random.choices([True, False], [90, 10])[0]

        )
        db.session.add(user)
    db.session.commit()


def create_user():
    user_datastore.create_user(email='admin@test.com', password='admin')
    db.session.commit()


def add_roles():
    for _ in range(2):
        role = Role(
            role_name=random.choices(['Store User', 'Store Admin'])[0]
        )
        db.session.add(role)
    db.session.commit()


def add_store_users():
    stores = Store.query.all()
    users = User.query.all()

    for store in stores:
        k = random.randint(1, 3)
        store_workers = random.sample(users, k)
        store.users.extend(store_workers)

    db.session.commit()


def add_user_roles():
    users = User.query.all()
    roles = Role.query.all()

    for user in users:
        k = random.randint(1, 1)
        roles_users = random.sample(roles, k)
        user.roles.extend(roles_users)

    db.session.commit()


def create_random_data():
    db.create_all()
    add_customers()
    add_stores()
    add_orders()
    add_products()
    add_users()
    add_roles()
    add_store_users()
    add_user_roles()





