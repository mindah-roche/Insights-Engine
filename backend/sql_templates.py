import re

def generate_sql_from_template(question: str) -> str:
    q = question.lower().strip()

    # --- Descriptive Summaries ---
    if re.search(r"(how many|number of)\s+users", q):
        return "-- Count of users\nSELECT COUNT(*) AS total_users FROM users;"

    if re.search(r"total revenue", q):
        return """
        -- Total revenue from all orders
        SELECT SUM(o.quantity * p.price) AS total_revenue
        FROM orders o
        JOIN products p ON o.product_id = p.id;
        """

    # --- Top/Bottom Rankings ---
    if re.search(r"(highest|top).*revenue.*category", q) or re.search(r"which category has the highest revenue", q):
        return """
        -- Category with the highest revenue
        SELECT p.category, SUM(o.quantity * p.price) AS revenue
        FROM orders o
        JOIN products p ON o.product_id = p.id
        GROUP BY p.category
        ORDER BY revenue DESC
        LIMIT 1;
        """

    if re.search(r"top.*(customers|users)", q):
        return """
        -- Top 5 users by total spending
        SELECT u.name, SUM(o.quantity * p.price) AS total_spent
        FROM orders o
        JOIN users u ON o.user_id = u.id
        JOIN products p ON o.product_id = p.id
        GROUP BY u.id
        ORDER BY total_spent DESC
        LIMIT 5;
        """

    if re.search(r"(most popular|top selling) products?", q):
        return """
        -- Top selling products by quantity
        SELECT p.name AS product_name, SUM(o.quantity) AS total_sold
        FROM orders o
        JOIN products p ON o.product_id = p.id
        GROUP BY p.id
        ORDER BY total_sold DESC
        LIMIT 5;
        """

    # --- Time Trends ---
    if re.search(r"revenue over time", q):
        return """
        -- Daily revenue trend
        SELECT DATE(o.order_date) AS day, SUM(o.quantity * p.price) AS revenue
        FROM orders o
        JOIN products p ON o.product_id = p.id
        GROUP BY day
        ORDER BY day;
        """

    if re.search(r"orders per day", q):
        return """
        -- Orders per day
        SELECT DATE(order_date) AS day, COUNT(*) AS order_count
        FROM orders
        GROUP BY day
        ORDER BY day;
        """

    if re.search(r"monthly revenue", q):
        return """
        -- Monthly revenue trend
        SELECT DATE_FORMAT(order_date, '%Y-%m') AS month, SUM(o.quantity * p.price) AS revenue
        FROM orders o
        JOIN products p ON o.product_id = p.id
        GROUP BY month
        ORDER BY month;
        """

    # --- Filtered Results ---
    if re.search(r"(orders\s+)?with quantity\s+>\s*\d+", q):
        num = re.findall(r"quantity\s*>\s*(\d+)", q)
        if num:
            return f"""
            -- Orders with quantity greater than {num[0]}
            SELECT o.id AS order_id, p.name AS product_name, o.quantity
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.quantity > {num[0]};
            """

    # --- Compare Users by Order Count ---
    if re.search(r"compare users by number of orders", q) or re.search(r"users by order count", q):
        return """
        -- Number of orders by user
        SELECT u.name, COUNT(o.id) AS total_orders
        FROM users u
        JOIN orders o ON u.id = o.user_id
        GROUP BY u.id
        ORDER BY total_orders DESC;
        """

    if re.search(r"users.*more than \d+ orders", q):
        num = re.findall(r"more than (\d+)", q)
        if num:
            return f"""
            -- Users with more than {num[0]} orders
            SELECT u.name, COUNT(o.id) AS total_orders
            FROM users u
            JOIN orders o ON u.id = o.user_id
            GROUP BY u.id
            HAVING total_orders > {num[0]};
            """

    if re.search(r"orders.*between .* and .*", q):
        dates = re.findall(r"between (.+?) and (.+)", q)
        if dates:
            start_date, end_date = dates[0]
            return f"""
            -- Orders between {start_date.strip()} and {end_date.strip()}
            SELECT o.id AS order_id, u.name AS user_name, p.name AS product_name, o.quantity, o.order_date
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN products p ON o.product_id = p.id
            WHERE o.order_date BETWEEN '{start_date.strip()}' AND '{end_date.strip()}';
            """

    # --- Group Counts ---
    if re.search(r"orders by category", q):
        return """
        -- Number of orders per product category
        SELECT p.category, COUNT(o.id) AS total_orders
        FROM orders o
        JOIN products p ON o.product_id = p.id
        GROUP BY p.category;
        """

    if re.search(r"users by signup date", q):
        return """
        -- New users by signup date
        SELECT DATE(created_at) AS signup_date, COUNT(*) AS new_users
        FROM users
        GROUP BY signup_date
        ORDER BY signup_date;
        """

    return "-- No matching SQL template found for the question."
