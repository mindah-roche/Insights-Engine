import re

def generate_sql_from_template(question: str) -> str | None:
    q = question.lower().strip()

    # --- Descriptive summaries ---
    if re.search(r"\bhow many users\b", q):
        return "SELECT COUNT(*) AS user_count FROM users;"
    
    if re.search(r"\bhow many orders\b", q):
        return "SELECT COUNT(*) AS order_count FROM orders;"

    if re.search(r"\bhow many products\b", q):
        return "SELECT COUNT(*) AS product_count FROM products;"
    
    if re.search(r"\btotal revenue\b", q):
        return "SELECT SUM(o.quantity * p.price) AS total_revenue FROM orders o JOIN products p ON o.product_id = p.id;"

    # --- Rankings & group summaries ---
    if re.search(r"\bwhich category has the highest revenue\b", q):
        return """SELECT p.category, SUM(o.quantity * p.price) AS revenue
FROM orders o JOIN products p ON o.product_id = p.id
GROUP BY p.category
ORDER BY revenue DESC
LIMIT 1;"""

    if re.search(r"\bmost ordered product\b", q):
        return """SELECT p.name, SUM(o.quantity) AS total_ordered
FROM orders o JOIN products p ON o.product_id = p.id
GROUP BY p.name
ORDER BY total_ordered DESC
LIMIT 1;"""

    # --- Time trends ---
    if re.search(r"\brevenue over time\b", q):
        return """SELECT o.order_date, SUM(o.quantity * p.price) AS revenue
FROM orders o JOIN products p ON o.product_id = p.id
GROUP BY o.order_date
ORDER BY o.order_date;"""

    if re.search(r"\border count over time\b", q):
        return """SELECT o.order_date, COUNT(*) AS order_count
FROM orders o
GROUP BY o.order_date
ORDER BY o.order_date;"""

    # --- Filters ---
    if re.search(r"\borders with quantity > (\d+)", q):
        match = re.search(r"quantity > (\d+)", q)
        qty = match.group(1) if match else "1"
        return f"SELECT * FROM orders WHERE quantity > {qty};"

    if re.search(r"\bproducts in category ['\"]?(\w+)['\"]?", q):
        match = re.search(r"category ['\"]?(\w+)['\"]?", q)
        cat = match.group(1) if match else "General"
        return f"SELECT * FROM products WHERE category = '{cat}';"

    # --- Comparisons ---
    if re.search(r"\bcompare revenue by category\b", q):
        return """SELECT p.category, SUM(o.quantity * p.price) AS revenue
FROM orders o JOIN products p ON o.product_id = p.id
GROUP BY p.category
ORDER BY revenue DESC;"""

    if re.search(r"\bcompare users by number of orders\b", q):
        return """SELECT u.name, COUNT(o.id) AS order_count
FROM users u JOIN orders o ON u.id = o.user_id
GROUP BY u.name
ORDER BY order_count DESC;"""

    return None
