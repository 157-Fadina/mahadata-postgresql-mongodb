import csv
import time
from datetime import datetime
from pathlib import Path

import psycopg2
from pymongo import MongoClient


# 1. Konfigurasi koneksi PostgreSQL.
PG_CONFIG = {
    "dbname": "ecommercedb",
    "user": "postgres",
    "password": "123",
    "host": "localhost",
    "port": "5432",
}

# 2. Koneksi MongoDB.
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DATABASE = "ecommercedb"

# 3. Query SQL untuk mencari produk.
SQL_TEST2 = """
SELECT
    p.productID,
    p.productName,
    p.price,
    b.brandName
FROM product p
INNER JOIN brand b
    ON p.brandID = b.brandID
WHERE b.brandName LIKE 'A%'
  AND p.price BETWEEN 100 AND 300;
"""

# 4. Query SQL untuk analisis pesanan.
SQL_TEST4 = """
SELECT
    c.customerID,
    c.firstName,
    c.secondName,
    o.orderID,
    o.orderDate,
    SUM(oi.unitPrice * oi.quantity) AS order_total
FROM customer c
INNER JOIN customerorder o
    ON c.customerID = o.customerID
INNER JOIN orderitem oi
    ON o.orderID = oi.orderID
WHERE o.orderDate BETWEEN DATE '2024-01-01'
                      AND DATE '2024-12-31'
GROUP BY
    c.customerID,
    c.firstName,
    c.secondName,
    o.orderID,
    o.orderDate
HAVING SUM(oi.unitPrice * oi.quantity) > 300;
"""


def run_postgresql(cursor, query_type):
    sql = {
        "select_test2": SQL_TEST2,
        "select_test4": SQL_TEST4,
    }[query_type]

    start = time.perf_counter()

    cursor.execute(sql)
    rows = cursor.fetchall()

    elapsed_ms = (time.perf_counter() - start) * 1000

    return elapsed_ms, len(rows)


def run_mongodb(db, query_type):
    """Jalankan query MongoDB dan ukur waktu eksekusi + pengambilan hasil."""

    start = time.perf_counter()

    if query_type == "select_test2":
        filter_query = {
            "brandName": {"$regex": "^A"},
            "price": {"$gte": 100, "$lte": 300},
        }

        projection = {
            "_id": 0,
            "productID": 1,
            "productName": 1,
            "price": 1,
            "brandName": 1,
        }

        rows = list(
            db.products.find(filter_query, projection)
        )

    elif query_type == "select_test4":
        pipeline = [
            {
                "$match": {
                    "orderDate": {
                        "$gte": datetime(2024, 1, 1),
                        "$lte": datetime(2024, 12, 31),
                    }
                }
            },
            {"$unwind": "$items"},
            {
                "$group": {
                    "_id": "$_id",
                    "orderDate": {"$first": "$orderDate"},
                    "customer": {"$first": "$customer"},
                    "order_total": {
                        "$sum": {
                            "$multiply": [
                                "$items.unitPrice",
                                "$items.quantity",
                            ]
                        }
                    },
                }
            },
            {
                "$match": {
                    "order_total": {"$gt": 300}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "orderDate": 1,
                    "order_total": 1,
                    "firstName": "$customer.firstName",
                    "secondName": "$customer.secondName",
                }
            },
        ]

        rows = list(db.orders.aggregate(pipeline))

    else:
        raise ValueError(f"Query tidak dikenal: {query_type}")

    elapsed_ms = (time.perf_counter() - start) * 1000

    return elapsed_ms, len(rows)


def main():
    output_dir = Path("results/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "benchmark_results.csv"

    # Hubungkan ke kedua database.
    pg_conn = psycopg2.connect(**PG_CONFIG)
    mongo_client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
    )

    try:
        # Pastikan MongoDB bisa diakses.
        mongo_client.admin.command("ping")

        mongo_db = mongo_client[MONGO_DATABASE]
        pg_cursor = pg_conn.cursor()

        query_types = [
            "select_test2",
            "select_test4",
        ]

        with output_file.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "stage",
                    "db",
                    "query_type",
                    "attempt",
                    "is_warmup",
                    "time_ms",
                    "rows",
                ],
            )
            writer.writeheader()

            for query_type in query_types:
                for attempt in range(1, 16):

                    # Ganti urutan database secara bergantian
                    # untuk mengurangi bias akibat urutan eksekusi.
                    if attempt % 2 == 1:
                        db_order = ["PostgreSQL", "MongoDB"]
                    else:
                        db_order = ["MongoDB", "PostgreSQL"]

                    for db_name in db_order:
                        if db_name == "PostgreSQL":
                            time_ms, row_count = run_postgresql(
                                pg_cursor,
                                query_type,
                            )
                        else:
                            time_ms, row_count = run_mongodb(
                                mongo_db,
                                query_type,
                            )

                        result = {
                            "stage": "I",
                            "db": db_name,
                            "query_type": query_type,
                            "attempt": attempt,
                            "is_warmup": attempt <= 2,
                            "time_ms": round(time_ms, 4),
                            "rows": row_count,
                        }

                        writer.writerow(result)

                        print(
                            f"{query_type} | {db_name} | "
                            f"Percobaan {attempt} | "
                            f"{time_ms:.2f} ms | "
                            f"{row_count} baris"
                        )

        pg_cursor.close()
        print(f"\nPengujian selesai. Hasil disimpan di: {output_file}")

    finally:
        pg_conn.close()
        mongo_client.close()


if __name__ == "__main__":
    main()