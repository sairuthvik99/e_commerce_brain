import psycopg2
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker("en_IN")

conn = psycopg2.connect(
    dbname="",
    user="",
    password="",
    host="",
    port=""
)

cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    order_timestamp TIMESTAMP,
    customer_id INT,
    region TEXT,
    order_value NUMERIC,
    product_count INT,
    created_date DATE
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT,
    unit_price NUMERIC,
    item_total NUMERIC
);

CREATE TABLE IF NOT EXISTS inventory_snapshots (
    snapshot_id SERIAL PRIMARY KEY,
    product_id INT,
    snapshot_timestamp TIMESTAMP,
    available_stock INT,
    stock_threshold INT,
    is_out_of_stock BOOLEAN,
    out_of_stock_since TIMESTAMP
);

CREATE TABLE IF NOT EXISTS marketing_campaigns_daily (
    campaign_id INT,
    channel TEXT,
    date DATE,
    impressions INT,
    clicks INT,
    spend NUMERIC,
    conversions INT,
    campaign_status TEXT
);

CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id SERIAL PRIMARY KEY,
    created_timestamp TIMESTAMP,
    issue_category TEXT,
    sentiment TEXT,
    product_id INT,
    customer_id INT
);

CREATE TABLE IF NOT EXISTS daily_metrics (
    date DATE PRIMARY KEY,
    total_revenue NUMERIC,
    total_orders INT,
    avg_order_value NUMERIC,
    stockout_sku_count INT,
    total_complaints INT,
    marketing_spend NUMERIC,
    marketing_conversions INT
);
""")
conn.commit()

START_DATE = datetime.today().date() - timedelta(days=49)
DAYS = 50

REGIONS = ["Delhi", "Hyderabad", "Bangalore", "Mumbai", "Kochi", "Chennai"]
PRODUCTS = list(range(1, 16))
CUSTOMERS = list(range(1, 101))

CAMPAIGNS = list(range(1, 9))
CHANNELS = ["Google", "Meta", "Email"]


inventory_drop = range(10, 15)      # 5 days
marketing_drop = range(25, 28)      # 3 days
complaint_drop = range(48, 50)      # last 2 days

for day in range(DAYS):
    date = START_DATE + timedelta(days=day)

    for product in PRODUCTS:
        if day in inventory_drop:
            stock = 0
            out = True
            oos_since = date
        else:
            stock = random.randint(20, 100)
            out = False
            oos_since = None

        cur.execute("""
        INSERT INTO inventory_snapshots
        (product_id, snapshot_timestamp, available_stock,
         stock_threshold, is_out_of_stock, out_of_stock_since)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            product,
            datetime.combine(date, datetime.min.time()),
            stock,
            10,
            out,
            oos_since
        ))

for day in range(DAYS):
    date = START_DATE + timedelta(days=day)

    if day in inventory_drop or day in marketing_drop or day in complaint_drop:
        orders_today = random.randint(15, 25)
    else:
        orders_today = random.randint(45, 55)

    for _ in range(orders_today):
        # Generate product count for this order
        product_count = random.randint(1, 4)
        order_timestamp = fake.date_time_between(start_date=date, end_date=date + timedelta(days=1))
        customer_id = random.choice(CUSTOMERS)
        region = random.choice(REGIONS)
        
        # Generate order items first to calculate total order value
        order_items = []
        total_order_value = 0
        # Select random products for this order (no duplicates)
        selected_products = random.sample(PRODUCTS, min(product_count, len(PRODUCTS)))
        
        for product_id in selected_products:
            quantity = random.randint(1, 3)
            unit_price = round(random.uniform(200, 1500), 2)
            item_total = round(quantity * unit_price, 2)
            total_order_value += item_total
            order_items.append({
                'product_id': product_id,
                'quantity': quantity,
                'unit_price': unit_price,
                'item_total': item_total
            })
        
        # Insert the order
        cur.execute("""
        INSERT INTO orders
        (order_timestamp, customer_id, region,
         order_value, product_count, created_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING order_id
        """, (
            order_timestamp,
            customer_id,
            region,
            round(total_order_value, 2),
            product_count,
            date
        ))
        
        # Get the order_id for the inserted order
        order_id = cur.fetchone()[0]
        
        # Insert order items
        for item in order_items:
            cur.execute("""
            INSERT INTO order_items
            (order_id, product_id, quantity, unit_price, item_total)
            VALUES (%s, %s, %s, %s, %s)
            """, (
                order_id,
                item['product_id'],
                item['quantity'],
                item['unit_price'],
                item['item_total']
            ))

for day in range(DAYS):
    date = START_DATE + timedelta(days=day)

    for campaign in CAMPAIGNS:
        if day in marketing_drop:
            status = "paused"
            conversions = random.randint(0, 2)
        else:
            status = "active"
            conversions = random.randint(5, 20)

        cur.execute("""
        INSERT INTO marketing_campaigns_daily
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            campaign,
            random.choice(CHANNELS),
            date,
            random.randint(1000, 10000),
            random.randint(50, 500),
            round(random.uniform(1000, 10000), 2),
            conversions,
            status
        ))
for day in range(DAYS):
    date = START_DATE + timedelta(days=day)

    tickets = random.randint(8, 12) if day in complaint_drop else random.randint(0, 2)

    for _ in range(tickets):
        cur.execute("""
        INSERT INTO support_tickets
        (created_timestamp, issue_category, sentiment, product_id, customer_id)
        VALUES (%s, %s, %s, %s, %s)
        """, (
            fake.date_time_between(start_date=date, end_date=date + timedelta(days=1)),
            random.choice(["delivery", "product", "website"]),
            "negative" if day in complaint_drop else random.choice(["positive", "neutral"]),
            random.choice(PRODUCTS),
            random.choice(CUSTOMERS)
        ))
for day in range(DAYS):
    date = START_DATE + timedelta(days=day)

    total_orders = random.randint(20, 30) if day in inventory_drop else random.randint(45, 60)

    cur.execute("""
    INSERT INTO daily_metrics
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        date,
        round(total_orders * random.uniform(1200, 1800), 2),
        total_orders,
        round(random.uniform(1200, 1800), 2),
        random.randint(5, 10) if day in inventory_drop else random.randint(0, 2),
        random.randint(8, 12) if day in complaint_drop else random.randint(0, 2),
        round(random.uniform(5000, 20000), 2),
        random.randint(5, 20)
    ))


conn.commit()
cur.close()
conn.close()

print("✅ PostgreSQL seeded successfully")
