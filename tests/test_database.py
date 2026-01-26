from backend.database.queries import (
    get_most_recent_date,
    get_daily_sales_metrics,
    get_stockout_events
)

print("Testing database connection...")
print(f"Most recent date: {get_most_recent_date()}")
print(f"Sales metrics: {get_daily_sales_metrics()}")
print(f"Stockouts: {get_stockout_events()}")
print("✅ Database layer working!")