from typing import List

class QueryGenerator:
    """
    Class to generate seed corpus of SQL queries.
    """
    
    def generate_seed_queries(self) -> List[str]:
        """
        Generate a comprehensive seed corpus covering all SQL features.
        
        Returns:
            List of valid SQL queries
        """
        corpus = [
            # Basic SELECT queries
            "SELECT * FROM users;",
            "SELECT name, age FROM users WHERE age > 30;",
            "SELECT COUNT(*) FROM products WHERE price < 100;",
            "SELECT DISTINCT category FROM products;",
            
            # JOINs
            "SELECT u.name, p.name, o.quantity FROM users u JOIN orders o ON u.id = o.user_id JOIN products p ON o.product_id = p.id;",
            "SELECT u.name, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id;",
            "SELECT p.name, AVG(r.rating) as avg_rating FROM products p INNER JOIN reviews r ON p.id = r.product_id GROUP BY p.id;",
            
            # Subqueries
            "SELECT name FROM users WHERE id IN (SELECT user_id FROM orders WHERE quantity > 5);",
            "SELECT * FROM products WHERE price > (SELECT AVG(price) FROM products);",
            "SELECT u.name, (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) as order_count FROM users u;",
            
            # Aggregations and GROUP BY
            "SELECT category, COUNT(*), AVG(price) FROM products GROUP BY category;",
            "SELECT user_id, COUNT(*) as review_count FROM reviews GROUP BY user_id HAVING COUNT(*) > 3;",
            "SELECT p.category, MIN(p.price), MAX(p.price) FROM products p GROUP BY p.category;",
            
            # ORDER BY and LIMIT
            "SELECT * FROM users ORDER BY age DESC LIMIT 10;",
            "SELECT * FROM products ORDER BY price ASC, name DESC;",
            "SELECT * FROM orders ORDER BY order_date DESC LIMIT 5 OFFSET 10;",
            
            # INSERT queries
            "INSERT INTO users (name, email, age) VALUES ('John Doe', 'john@example.com', 35);",
            "INSERT INTO products (name, price, category, stock) VALUES ('New Product', 99.99, 'Electronics', 50);",
            "INSERT INTO orders (user_id, product_id, quantity, order_date) VALUES (1, 2, 3, '2024-04-21');",
            
            # UPDATE queries
            "UPDATE users SET age = age + 1 WHERE id = 1;",
            "UPDATE products SET price = price * 0.9 WHERE category = 'Electronics';",
            "UPDATE orders SET quantity = 10 WHERE id = 5;",
            
            # DELETE queries
            "DELETE FROM reviews WHERE rating < 2;",
            "DELETE FROM orders WHERE user_id = 5;",
            "DELETE FROM products WHERE stock = 0;",
            
            # Complex queries with CASE
            "SELECT name, CASE WHEN age < 18 THEN 'Minor' WHEN age >= 65 THEN 'Senior' ELSE 'Adult' END as age_group FROM users;",
            
            # Window functions
            "SELECT name, price, AVG(price) OVER (PARTITION BY category) as avg_category_price FROM products;",
            
            # WITH clause (CTEs)
            "WITH active_users AS (SELECT user_id FROM orders GROUP BY user_id HAVING COUNT(*) > 5) SELECT u.* FROM users u JOIN active_users au ON u.id = au.user_id;",
            
            # Transactions
            "BEGIN TRANSACTION; UPDATE products SET stock = stock - 1 WHERE id = 1; INSERT INTO orders (user_id, product_id, quantity) VALUES (1, 1, 1); COMMIT;",
            
            # Indexes (though not DML/DQL)
            "CREATE INDEX idx_temp ON reviews(rating);",
            "DROP INDEX idx_temp;",
            
            # UNION and set operations
            "SELECT name FROM users UNION SELECT name FROM products;",
            "SELECT category FROM products EXCEPT SELECT DISTINCT category FROM products WHERE stock = 0;",
            
            # Date and string functions
            "SELECT * FROM orders WHERE strftime('%Y', order_date) = '2024';",
            "SELECT UPPER(name), LENGTH(email) FROM users;",
            
            # NULL handling
            "SELECT * FROM products WHERE category IS NULL;",
            "SELECT COALESCE(age, 0) FROM users;",
            
            # HAVING (requires GROUP BY)
            "SELECT category, COUNT(*) FROM products GROUP BY category HAVING COUNT(*) > 10;",
            
            # Self-joins
            "SELECT a.name as user1, b.name as user2 FROM users a, users b WHERE a.id < b.id AND a.age = b.age;",
        ]
        
        return corpus
    