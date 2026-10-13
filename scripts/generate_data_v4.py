import psycopg2
from faker import Faker
import random
from pymongo import MongoClient
from datetime import datetime

fake = Faker()
fake.unique.clear()

conn = psycopg2.connect(
    dbname='ecommercedb',
    user='postgres',
    password='123',
    host='localhost',
    port='5432'
)
cur = conn.cursor()

client = MongoClient("mongodb://localhost:27017/")
db = client["ecommercedb"]


tables = [
    'orderitem', 'customerorder', 'customer', 'address', 'street', 'city', 'country',
    'brand', 'category', 'productcategory', 'product',
    'orderstatus', 'paymentmethod', 'review'
]
for table in tables:
    cur.execute(f'TRUNCATE TABLE {table} CASCADE;')
conn.commit()
print("Visos lentelės ištuštintos.")


db.orders.drop()
db.customers.drop()
db.products.drop()
db.categories.drop()
db.brands.drop()
db.review.drop()


N_COUNTRIES = 10
N_CITIES = 100
N_STREETS = 250
N_BRANDS = 130
N_CATEGORIES = 25
N_PRODUCTS = 5000
N_CUSTOMERS = 5000
N_ORDERS = 9000
N_REVIEWS = 30000

countries_pg, cities_pg, streets_pg = [], [], []
countries_mongo, cities_mongo, streets_mongo = [], [], []

print("Generating countries, cities, streets...")



for _ in range(N_COUNTRIES):
    country_name = fake.country()
    cur.execute("SELECT countryID FROM country WHERE countryName = %s;", (country_name,))
    res = cur.fetchone()
    if not res:
        cur.execute("INSERT INTO country (countryName) VALUES (%s) RETURNING countryID;", (country_name,))
        country_id = cur.fetchone()[0]
    else:
        country_id = res[0]

    countries_pg.append({"countryID": country_id, "countryName": country_name})
    countries_mongo.append(country_name)


for _ in range(N_CITIES):
    city_name = fake.city()
    country = random.choice(countries_pg)
    cur.execute(
        "INSERT INTO city (cityName, countryID) VALUES (%s, %s) RETURNING cityID;",
        (city_name, country["countryID"])
    )
    city_id = cur.fetchone()[0]
    cities_pg.append({"cityID": city_id, "cityName": city_name, "countryID": country["countryID"]})
    cities_mongo.append(city_name)


for _ in range(N_STREETS):
    street_name = fake.street_name()
    city = random.choice(cities_pg)
    cur.execute(
        "INSERT INTO street (streetName, cityID) VALUES (%s, %s) RETURNING streetID;",
        (street_name, city["cityID"])
    )
    street_id = cur.fetchone()[0]
    streets_pg.append({"streetID": street_id, "streetName": street_name, "cityID": city["cityID"]})
    streets_mongo.append(street_name)

conn.commit()
print("Countries, cities, streets generated.")


city_by_id = {c["cityID"]: c for c in cities_pg}
country_by_id = {c["countryID"]: c for c in countries_pg}


brands_pg, brands_mongo = [], []
print("Generating brands...")

for _ in range(N_BRANDS):
    brand_name = fake.company()
    cur.execute("INSERT INTO brand (brandName) VALUES (%s) RETURNING brandID;", (brand_name,))
    brand_id = cur.fetchone()[0]
    brands_pg.append({"brandID": brand_id, "brandName": brand_name})
    brands_mongo.append({"brandName": brand_name})

conn.commit()
print("Brands generated.")


db.brands.insert_many(brands_mongo)
db.brands.create_index("brandName", unique=False)


categories_pg, categories_mongo = [], []
print("Generating categories...")

for _ in range(N_CATEGORIES):
    category_name = fake.word().capitalize()
    cur.execute("INSERT INTO category (categoryName) VALUES (%s) RETURNING categoryID;", (category_name,))
    category_id = cur.fetchone()[0]
    categories_pg.append({"categoryID": category_id, "categoryName": category_name})
    categories_mongo.append({"categoryName": category_name})

conn.commit()
print("Categories generated.")


db.categories.insert_many(categories_mongo)
db.categories.create_index("categoryName", unique=False)


products_pg = []
products_mongo = []
product_cat_map = {}  

print("Generating products...")

for _ in range(N_PRODUCTS):
    product_name = fake.word().capitalize() + " " + fake.word().capitalize()
    description = fake.text(max_nb_chars=150)
    price = round(random.uniform(10, 1000), 2)
    stock = random.randint(0, 100)

    brand = random.choice(brands_pg)


    cur.execute(
        "INSERT INTO product (productName, description, price, stock, brandID) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING productID;",
        (product_name, description, price, stock, brand["brandID"])
    )
    product_id = cur.fetchone()[0]

    products_pg.append({
        "productID": product_id,
        "productName": product_name,
        "description": description,
        "price": price,
        "stock": stock,
        "brandID": brand["brandID"]
    })

    chosen_cats_pg = random.sample(categories_pg, k=random.randint(1, 3))
    product_cat_map[product_id] = [c["categoryID"] for c in chosen_cats_pg]
    prod_categories_mongo = [{"categoryName": c["categoryName"]} for c in chosen_cats_pg]


    product_mongo = {
        "productID": product_id,
        "productName": product_name,
        "description": description,
        "price": price,
        "stock": stock,
        "brandName": brand["brandName"],         
        "categories": prod_categories_mongo       
    }
    products_mongo.append(product_mongo)

conn.commit()

for p in products_pg:
    for cid in product_cat_map[p["productID"]]:
        cur.execute(
            "INSERT INTO productCategory (productID, categoryID) VALUES (%s, %s);",
            (p["productID"], cid)
        )
conn.commit()

print("Inserting products into MongoDB...")
db.products.insert_many(products_mongo)
print("Products inserted into MongoDB.")

# ---- CUSTOMERS ----
customers_pg, customers_mongo = [], []
print("Generating customers...")

for _ in range(N_CUSTOMERS):
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = fake.unique.email()
    phone = fake.phone_number()[:15]

    street = random.choice(streets_pg)
    city = city_by_id[street["cityID"]]
    country = country_by_id[city["countryID"]]

    cur.execute(
        "INSERT INTO address (houseNo, apartNo, postalCode, streetID) "
        "VALUES (%s, %s, %s, %s) RETURNING addressID;",
        (fake.building_number(), random.choice([None, fake.building_number()]), fake.postcode(), street["streetID"])
    )
    address_id = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO customer (firstName, secondName, email, phone, addressID) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING customerID;",
        (first_name, last_name, email, phone, address_id)
    )
    customer_id = cur.fetchone()[0]

    customers_pg.append({
        "customerID": customer_id,
        "firstName": first_name,
        "secondName": last_name,
        "email": email,
        "phone": phone,
        "addressID": address_id
    })

    # Mongo: address denormalizuota (palikta tavo logika)
    address_mongo = {
        "houseNo": fake.building_number(),
        "apartNo": random.choice([None, fake.building_number()]),
        "postalCode": fake.postcode(),
        "street": street["streetName"],
        "city": city["cityName"],
        "country": country["countryName"]
    }

    customer_mongo = {
        "firstName": first_name,
        "secondName": last_name,
        "email": email,
        "phone": phone,
        "address": address_mongo
    }
    customers_mongo.append(customer_mongo)

conn.commit()
print("Customers generated.")

print("Inserting customers into MongoDB...")
db.customers.insert_many(customers_mongo)
customers_by_email = {
    customer["email"]: customer
    for customer in customers_mongo
}
print("Customers inserted into MongoDB.")

# ---- PAYMENT METHODS & ORDER STATUSES ----
def insert_payment_methods():
    methods = ['Credit Card', 'PayPal', 'Bank Transfer', 'Cash on Delivery']
    for method in methods:
        cur.execute("INSERT INTO paymentMethod (methodName) VALUES (%s) RETURNING methodID;", (method,))
        _ = cur.fetchone()[0]
    conn.commit()

def insert_order_statuses():
    statuses = ['Pending', 'Shipped', 'Delivered', 'Cancelled']
    for status in statuses:
        cur.execute("INSERT INTO orderStatus (statusName) VALUES (%s) RETURNING statusID;", (status,))
        _ = cur.fetchone()[0]
    conn.commit()

insert_payment_methods()
insert_order_statuses()
print("Methods and statuses generated.")

# Užsikraunam map'us
cur.execute("SELECT statusID, statusName FROM orderStatus;")
status_map = {name: sid for sid, name in cur.fetchall()}
cur.execute("SELECT methodID, methodName FROM paymentMethod;")
pay_map = {name: mid for mid, name in cur.fetchall()}

# ---- ORDERS ----
print("Generating orders...")

for _ in range(N_ORDERS):
    customer_pg = random.choice(customers_pg)
    # (palikta tavo logika: randam mongo customer pagal email)
    customer_mongo = customers_by_email[customer_pg["email"]]

    n_items = random.randint(1, 10)
    order_products_pg = random.sample(products_pg, n_items)

    items_pg = []
    items_mongo = []
    total_pg = 0

    order_date = fake.date_time_between(start_date=datetime(2024, 1, 1), end_date=datetime.now())
    status_name = random.choice(list(status_map.keys()))
    payment_method_name = random.choice(list(pay_map.keys()))

    for p in order_products_pg:
        quantity = random.randint(1, 5)
        discount = round(random.uniform(0, p["price"] * 0.2), 2)
        line_total = round(quantity * (p["price"] - discount), 2)
        total_pg += line_total

        items_pg.append({
            "productID": p["productID"],
            "quantity": quantity,
            "discount": discount,
            "lineTotal": line_total,
            "unitPrice": p["price"]
        })

        items_mongo.append({
            "productName": p["productName"],
            "unitPrice": p["price"],
            "quantity": quantity,
            "discount": discount,
            "lineTotal": line_total
        })

    # Shipping address (PG)
    street = random.choice(streets_pg)
    city = city_by_id[street["cityID"]]
    country = country_by_id[city["countryID"]]

    cur.execute(
        "INSERT INTO address (houseNo, apartNo, postalCode, streetID) VALUES (%s, %s, %s, %s) RETURNING addressID;",
        (fake.building_number(), random.choice([None, fake.building_number()]), fake.postcode(), street["streetID"])
    )
    shipping_address_id = cur.fetchone()[0]

    status_id = status_map[status_name]
    payment_method_id = pay_map[payment_method_name]

    cur.execute(
        """INSERT INTO customerOrder (customerID, orderDate, statusID, shippingAddressID, totalAmount, paymentMethodID)
           VALUES (%s, %s, %s, %s, %s, %s)
           RETURNING orderID;""",
        (customer_pg["customerID"], order_date, status_id, shipping_address_id, round(total_pg, 2), payment_method_id)
    )
    order_id = cur.fetchone()[0]

    for item in items_pg:
        cur.execute(
            """INSERT INTO orderitem (orderID, productID, quantity, unitPrice, discount)
               VALUES (%s, %s, %s, %s, %s);""",
            (order_id, item["productID"], item["quantity"], item["unitPrice"], item["discount"])
        )

    shipping_address = {
        "street": street["streetName"],
        "houseNo": fake.building_number(),
        "apartNo": random.choice([None, fake.building_number()]),
        "postalCode": fake.postcode(),
        "city": city["cityName"],
        "country": country["countryName"]
    }

    order_mongo = {
        "customer": {
            "firstName": customer_mongo["firstName"],
            "secondName": customer_mongo["secondName"],
            "email": customer_mongo["email"]
        },
        "orderDate": order_date,
        "status": status_name,
        "paymentMethod": payment_method_name,
        "shippingAddress": shipping_address,
        "items": items_mongo,
        "totalAmount": round(total_pg, 2)
    }
    db.orders.insert_one(order_mongo)

# ---- REVIEWS ----
print("Generating reviews...")

review_data_pg = []
review_documents_mongo = []

for _ in range(N_REVIEWS):
    customer = random.choice(customers_pg)
    product = random.choice(products_pg)

    rating = random.randint(1, 5)
    comment = fake.sentence(nb_words=random.randint(5, 15))
    review_date = fake.date_time_between(start_date='-1y', end_date='now')

    review_data_pg.append((customer["customerID"], product["productID"], rating, comment, review_date))

    review_doc_mongo = {
        "customerID": customer["customerID"],
        "product": {
            "productID": product["productID"],
            "productName": product["productName"],
            "brandID": product["brandID"]
        },
        "rating": rating,
        "comment": comment,
        "reviewDate": review_date
    }
    review_documents_mongo.append(review_doc_mongo)

cur.executemany(
    """INSERT INTO review (customerID, productID, rating, comment, reviewDate)
       VALUES (%s, %s, %s, %s, %s)""",
    review_data_pg
)
conn.commit()

db["review"].insert_many(review_documents_mongo)

print("Reviews generated.")
print("Orders generated and inserted into both DBs.")
