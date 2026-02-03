"""
Script to add order_items table and populate it with data.

This script:
1. Creates the order_items table if it doesn't exist
2. Populates it with items for existing orders

Run this script to enable product-level sales analysis for the sales agent.
"""

import psycopg2
import random
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.settings import Settings

# Product IDs (same as in seed script)
PRODUCTS = list(range(1, 16))


def main():
    print("🔄 Connecting to database...")
    
    # Use docker-compose defaults directly since Settings may have incorrect values
    db_name = "ecommerce_db"
    db_user = "user"
    db_password = "password@123"
    db_host = "localhost"
    db_port = "5432"
    
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    
    cur = conn.cursor()
    
    # Step 1: Create the order_items table
    print("📋 Creating order_items table...")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        item_id SERIAL PRIMARY KEY,
        order_id INT NOT NULL,
        product_id INT NOT NULL,
        quantity INT NOT NULL DEFAULT 1,
        unit_price NUMERIC NOT NULL,
        item_total NUMERIC NOT NULL
    );
    
    CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
    CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);
    """)
    conn.commit()
    print("✅ order_items table created")
    
    # Step 2: Check if table already has data
    cur.execute("SELECT COUNT(*) FROM order_items")
    existing_count = cur.fetchone()[0]
    
    if existing_count > 0:
        print(f"⚠️  order_items table already has {existing_count} records")
        response = input("Do you want to clear and repopulate? (y/n): ")
        if response.lower() != 'y':
            print("❌ Aborted. No changes made.")
            cur.close()
            conn.close()
            return
        
        cur.execute("TRUNCATE order_items RESTART IDENTITY")
        conn.commit()
        print("🗑️  Cleared existing order_items data")
    
    # Step 3: Get all existing orders
    print("📊 Fetching existing orders...")
    cur.execute("""
        SELECT order_id, order_value, product_count 
        FROM orders 
        ORDER BY order_id
    """)
    orders = cur.fetchall()
    print(f"   Found {len(orders)} orders")
    
    # Step 4: Generate order items for each order
    print("🔧 Generating order items...")
    items_created = 0
    
    for order_id, order_value, product_count in orders:
        # Use product_count if available, otherwise random
        num_items = product_count if product_count and product_count > 0 else random.randint(1, 4)
        num_items = min(num_items, len(PRODUCTS))  # Don't exceed available products
        
        # Select random products (no duplicates within same order)
        selected_products = random.sample(PRODUCTS, num_items)
        
        # Distribute order value among items
        remaining_value = float(order_value)
        
        for i, product_id in enumerate(selected_products):
            quantity = random.randint(1, 3)
            
            # Last item gets remaining value, others get proportional share
            if i == len(selected_products) - 1:
                item_total = round(remaining_value, 2)
            else:
                # Random portion of remaining value
                item_total = round(random.uniform(0.2, 0.5) * remaining_value, 2)
                item_total = min(item_total, remaining_value - 10)  # Keep some for remaining items
            
            remaining_value -= item_total
            unit_price = round(item_total / quantity, 2)
            
            cur.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, unit_price, item_total)
                VALUES (%s, %s, %s, %s, %s)
            """, (order_id, product_id, quantity, unit_price, item_total))
            
            items_created += 1
        
        # Commit every 100 orders
        if order_id % 100 == 0:
            conn.commit()
    
    conn.commit()
    print(f"✅ Created {items_created} order items")
    
    # Step 5: Verify the data
    print("\n📈 Top 5 products by quantity sold:")
    cur.execute("""
        SELECT 
            product_id, 
            SUM(quantity) as total_quantity,
            SUM(item_total) as total_revenue,
            COUNT(DISTINCT order_id) as order_count
        FROM order_items
        GROUP BY product_id
        ORDER BY total_quantity DESC
        LIMIT 5
    """)
    
    for row in cur.fetchall():
        print(f"   Product {row[0]}: {row[1]} units sold, ₹{row[2]:.2f} revenue, {row[3]} orders")
    
    cur.close()
    conn.close()
    
    print("\n✅ order_items table populated successfully!")
    print("   The sales agent can now answer product-level questions like:")
    print("   - 'What are the top 5 products that got sold?'")
    print("   - 'Which products generate the most revenue?'")


if __name__ == "__main__":
    main()
