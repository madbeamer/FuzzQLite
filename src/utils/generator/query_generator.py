from typing import List

class QueryGenerator:
    """
    Enhanced class to generate SQL queries with improved SQLite grammar coverage.
    """
    
    def generate_queries(self) -> List[str]:
        """
        Generate SQL queries covering most SQL features.
        
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
            "SELECT u.name, r.comment FROM users u CROSS JOIN reviews r WHERE u.id = r.user_id;",
            "SELECT u.name, p.name FROM users u NATURAL JOIN orders o NATURAL JOIN products p;",
            "SELECT u.name, p.name FROM users u LEFT OUTER JOIN orders o ON u.id = o.user_id LEFT OUTER JOIN products p ON o.product_id = p.id;",
            "SELECT p.name, r.rating FROM products p RIGHT OUTER JOIN reviews r ON p.id = r.product_id;",
            "SELECT p.name, r.rating FROM products p FULL OUTER JOIN reviews r ON p.id = r.product_id;",
            "SELECT u1.id AS user1_id, u1.name AS user1_name, u2.id AS user2_id, u2.name AS user2_name, u1.age FROM users u1 JOIN users u2 ON u1.age = u2.age AND u1.id < u2.id ORDER BY u1.age, u1.name, u2.name;",
            
            # Subqueries
            "SELECT name FROM users WHERE id IN (SELECT user_id FROM orders WHERE quantity > 5);",
            "SELECT * FROM products WHERE price > (SELECT AVG(price) FROM products);",
            "SELECT u.name, (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) as order_count FROM users u;",
            "SELECT * FROM users WHERE EXISTS (SELECT 1 FROM orders WHERE orders.user_id = users.id);",
            "SELECT * FROM users WHERE NOT EXISTS (SELECT 1 FROM orders WHERE orders.user_id = users.id);",
            "SELECT * FROM users WHERE age > ALL (SELECT age FROM users WHERE id < 5);",
            "SELECT * FROM users WHERE age > ANY (SELECT age FROM users WHERE id < 5);",
            "SELECT * FROM users WHERE age > SOME (SELECT age FROM users WHERE id < 5);",
            
            # Aggregations and GROUP BY
            "SELECT category, COUNT(*), AVG(price) FROM products GROUP BY category;",
            "SELECT user_id, COUNT(*) as review_count FROM reviews GROUP BY user_id HAVING COUNT(*) > 3;",
            "SELECT p.category, MIN(p.price), MAX(p.price) FROM products p GROUP BY p.category;",
            "SELECT p.category, SUM(p.price) FROM products p GROUP BY p.category;",
            "SELECT p.category, GROUP_CONCAT(p.name, ', ') FROM products p GROUP BY p.category;",
            "SELECT u.id, u.name, COUNT(*), SUM(o.quantity), AVG(o.quantity) FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name;",
            "SELECT COUNT(DISTINCT category) FROM products;",
            
            # ORDER BY and LIMIT
            "SELECT * FROM users ORDER BY age DESC LIMIT 10;",
            "SELECT * FROM products ORDER BY price ASC, name DESC;",
            "SELECT * FROM orders ORDER BY order_date DESC LIMIT 5 OFFSET 10;",
            "SELECT * FROM users ORDER BY age NULLS FIRST;",
            "SELECT * FROM users ORDER BY age NULLS LAST;",
            "SELECT * FROM users ORDER BY name COLLATE NOCASE;",
            
            # INSERT queries
            "INSERT INTO users (name, email, age) VALUES ('John Doe', 'john@example.com', 35);",
            "INSERT INTO products (name, price, category, stock) VALUES ('New Product', 99.99, 'Electronics', 50);",
            "INSERT INTO orders (user_id, product_id, quantity, order_date) VALUES (1, 2, 3, '2024-04-21');",
            "INSERT INTO users (name, email, age) VALUES ('Jane Smith', 'jane@example.com', 28), ('Bob Johnson', 'bob@example.com', 42);",
            "INSERT INTO products SELECT id+100, name || ' (Copy)', price*1.1, category, stock FROM products;",
            "INSERT OR REPLACE INTO users (id, name, email, age) VALUES (1, 'Updated User', 'updated@example.com', 40);",
            "INSERT OR IGNORE INTO users (id, name, email, age) VALUES (1, 'Ignored User', 'ignored@example.com', 45);",
            "INSERT INTO users (name, email, age, joined_date) VALUES ('Alex Smith', 'alex@example.com', 28, date('now')) RETURNING id, name, joined_date;",
            "INSERT INTO products (name, price, category, stock) VALUES 'Wireless Earbuds', 129.99, 'Electronics', 30)ON CONFLICT(name) DO UPDATE SET stock = stock + 30, price = CASE WHEN price > 129.99 THEN 129.99 ELSE price END;",
            
            # UPDATE queries
            "UPDATE users SET age = age + 1 WHERE id = 1;",
            "UPDATE products SET price = price * 0.9 WHERE category = 'Electronics';",
            "UPDATE orders SET quantity = 10 WHERE id = 5;",
            "UPDATE users SET age = NULL WHERE id = 2;",
            "UPDATE products SET category = UPPER(category);",
            "UPDATE users SET age = (SELECT AVG(age) FROM users);",
            "UPDATE users SET (name, email) = ('New Name', 'new@example.com') WHERE id = 3;",
            "UPDATE OR IGNORE users SET email = 'duplicate@example.com';",
            "UPDATE users SET score = score + 10 WHERE joined_date > date('now', '-1 month') RETURNING id, name, score AS new_score;",
            "UPDATE products SET stock = 0 WHERE stock < 5 ORDER BY price DESC LIMIT 10;",
            
            # DELETE queries
            "DELETE FROM reviews WHERE rating < 2;",
            "DELETE FROM orders WHERE user_id = 5;",
            "DELETE FROM products WHERE stock = 0;",
            "DELETE FROM users WHERE id IN (SELECT user_id FROM orders WHERE quantity > 10);",
            "DELETE FROM users;", # Delete all rows
            "DELETE FROM orders WHERE order_date < '2023-01-01' ORDER BY order_date LIMIT 10;",
            
            # Complex queries with CASE
            "SELECT name, CASE WHEN age < 18 THEN 'Minor' WHEN age >= 65 THEN 'Senior' ELSE 'Adult' END as age_group FROM users;",
            "SELECT id, name, CASE category WHEN 'Electronics' THEN price * 0.9 WHEN 'Clothing' THEN price * 0.8 ELSE price END as discounted_price FROM products;",
            "UPDATE products SET price = CASE WHEN stock > 100 THEN price * 0.9 WHEN stock > 50 THEN price * 0.95 ELSE price END;",
            
            # Window functions
            "SELECT name, price, AVG(price) OVER (PARTITION BY category) as avg_category_price FROM products;",
            "SELECT name, category, price, RANK() OVER (PARTITION BY category ORDER BY price DESC) as price_rank FROM products;",
            "SELECT id, name, price, LAG(price, 1, 0) OVER (ORDER BY price) as prev_price FROM products;",
            "SELECT id, name, price, LEAD(price, 1, 0) OVER (ORDER BY price) as next_price FROM products;",
            "SELECT id, name, price, FIRST_VALUE(price) OVER (PARTITION BY category ORDER BY price) as min_price FROM products;",
            "SELECT id, name, price, NTH_VALUE(price, 2) OVER (PARTITION BY category ORDER BY price) as second_price FROM products;",
            "SELECT name, price, NTILE(4) OVER (ORDER BY price) as price_quartile FROM products;",
            "SELECT id, category, ROW_NUMBER() OVER (PARTITION BY category ORDER BY price) as row_num FROM products;",
            "SELECT id, category, DENSE_RANK() OVER (PARTITION BY category ORDER BY price) as dense_rank FROM products;",
            "SELECT id, price, PERCENT_RANK() OVER (ORDER BY price) as percent_rank FROM products;",
            "SELECT u.name, v.product_name, v.recommended FROM users u CROSS JOIN (VALUES ('Smartphone', 1), ('Laptop', 0), ('Headphones', 1)) AS v(product_name, recommended) WHERE u.age BETWEEN 20 AND 40 LIMIT 10;",
            
            # WITH clause (CTEs)
            "WITH active_users AS (SELECT user_id FROM orders GROUP BY user_id HAVING COUNT(*) > 5) SELECT u.* FROM users u JOIN active_users au ON u.id = au.user_id;",
            "WITH product_stats AS (SELECT category, AVG(price) as avg_price FROM products GROUP BY category) SELECT p.*, ps.avg_price FROM products p JOIN product_stats ps ON p.category = ps.category WHERE p.price < ps.avg_price;",
            "WITH RECURSIVE category_tree(id, name, level) AS (SELECT 1, 'Electronics', 0 UNION ALL SELECT id+1, category, level+1 FROM products, category_tree WHERE products.id = category_tree.id AND category_tree.level < 2) SELECT * FROM category_tree;",
            "WITH ordered_users AS (SELECT * FROM users ORDER BY age DESC), top_users AS (SELECT * FROM ordered_users LIMIT 5) SELECT * FROM top_users;",
            
            # Transactions
            "BEGIN TRANSACTION; UPDATE products SET stock = stock - 1 WHERE id = 1; INSERT INTO orders (user_id, product_id, quantity) VALUES (1, 1, 1); COMMIT;",
            "BEGIN; UPDATE products SET price = price * 1.1; SAVEPOINT price_update; UPDATE products SET stock = stock + 10; ROLLBACK TO price_update; COMMIT;",
            "BEGIN IMMEDIATE TRANSACTION; UPDATE users SET score = score + 10 WHERE id = 5; COMMIT;",
            "BEGIN EXCLUSIVE TRANSACTION; DELETE FROM orders WHERE order_date < '2023-01-01'; COMMIT;",
            "BEGIN TRANSACTION; CREATE TEMPORARY TABLE temp_users AS SELECT * FROM users WHERE age > 30; INSERT INTO users SELECT * FROM temp_users WHERE id > 100; DROP TABLE temp_users; COMMIT;",
            "BEGIN DEFERRED; UPDATE products SET price = price * 0.9 WHERE category = 'Electronics'; COMMIT;",
            "SAVEPOINT inventory_update; UPDATE products SET stock = stock - 1 WHERE id = 1; ROLLBACK TO SAVEPOINT inventory_update;",
            "SAVEPOINT order_update; RELEASE SAVEPOINT order_update;",
            
            # Indexes and schema alterations
            "CREATE INDEX idx_user_age ON users(age);",
            "CREATE UNIQUE INDEX idx_product_name ON products(name);",
            "CREATE INDEX idx_order_date ON orders(order_date);",
            "CREATE INDEX idx_order_date ON orders(order_date); CREATE INDEX idx_order_date IF NOT EXISTS ON orders(order_date);",
            "DROP INDEX idx_user_age;",
            "CREATE INDEX idx_user_name_age ON users(name, age DESC);",
            "CREATE INDEX idx_reviews_partial ON reviews(rating) WHERE rating > 3;",
            "CREATE UNIQUE INDEX idn ON users (ID COLLATE NOCASE ASC);",
            "ALTER TABLE users ADD COLUMN last_login TEXT;",
            "ALTER TABLE products RENAME TO inventory;",
            "ALTER TABLE products RENAME COLUMN stock TO quantity;",
            "ALTER TABLE reviews DROP COLUMN comment;",
            "CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, event TEXT, timestamp TEXT);",
            "CREATE TEMP TABLE x (id INTEGER PRIMARY KEY) WITHOUT ROWID;",
            "DROP TABLE IF EXISTS logs;",
            "REINDEX idx_products_category;",
            "REINDEX users;",
            
            # UNION and set operations
            "SELECT name FROM users UNION SELECT name FROM products;",
            "SELECT category FROM products EXCEPT SELECT DISTINCT category FROM products WHERE stock = 0;",
            "SELECT id, name FROM users UNION ALL SELECT id, name FROM products;",
            "SELECT category, COUNT(*) FROM products GROUP BY category UNION SELECT 'All Categories', COUNT(*) FROM products;",
            "SELECT category FROM products INTERSECT SELECT category FROM products WHERE price > 50;",
            
            # Date and string functions (deterministic only)
            "SELECT * FROM orders WHERE strftime('%Y', order_date) = '2024';",
            "SELECT UPPER(name), LENGTH(email) FROM users;",
            "SELECT date(order_date, '+1 day') as next_day FROM orders;",
            "SELECT datetime(order_date, 'start of month', '+1 month', '-1 day') as last_day_of_month FROM orders;",
            "SELECT SUBSTR(name, 1, 3) FROM users;",
            "SELECT INSTR(name, 'a') FROM users;",
            "SELECT REPLACE(name, 'e', 'E') FROM users;",
            "SELECT TRIM(name) FROM users;",
            "SELECT LTRIM(RTRIM(name)) FROM users;",
            "SELECT name || ' (' || email || ')' FROM users;",
            
            # NULL handling
            "SELECT * FROM products WHERE category IS NULL;",
            "SELECT COALESCE(age, 0) FROM users;",
            "SELECT NULLIF(category, 'Unknown') FROM products;",
            "SELECT id, IFNULL(age, 'Unknown') FROM users;",
            "SELECT * FROM users WHERE age IS NOT NULL;",
            
            # HAVING (requires GROUP BY)
            "SELECT category, COUNT(*) FROM products GROUP BY category HAVING COUNT(*) > 10;",
            "SELECT user_id, AVG(rating) FROM reviews GROUP BY user_id HAVING MIN(rating) >= 3 AND MAX(rating) <= 5;",
            "SELECT product_id, COUNT(*) FROM reviews GROUP BY product_id HAVING COUNT(*) > (SELECT AVG(cnt) FROM (SELECT COUNT(*) as cnt FROM reviews GROUP BY product_id));",
            
            # Self-joins
            "SELECT a.name as user1, b.name as user2 FROM users a, users b WHERE a.id < b.id AND a.age = b.age;",
            "SELECT a.id, a.name, b.id, b.name FROM users a JOIN users b ON a.id <> b.id AND a.age = b.age;",
            
            # Math functions
            "SELECT name, price, ROUND(price, 1) FROM products;",
            "SELECT name, price, ABS(price - 50) as price_diff FROM products;",
            "SELECT name, price, CEIL(price) as rounded_up FROM products;",
            "SELECT name, price, FLOOR(price) as rounded_down FROM products;",
            "SELECT SIN(0.5), COS(0.5), TAN(0.5), SQRT(100);",
            "SELECT category, price / NULLIF(stock, 0) as price_per_unit FROM products;",
            
            # Additional complex SELECT queries
            "SELECT COUNT(*) FILTER (WHERE age > 30) FROM users;",
            "SELECT * FROM users WHERE age > 30 OR (age IS NULL AND score > 50);",
            
            # Pragmas
            "PRAGMA table_info(users);",
            "PRAGMA index_list(products);",
            "PRAGMA foreign_key_list(orders);",
            "PRAGMA journal_mode = WAL;",
            "PRAGMA synchronous = NORMAL;",
            "PRAGMA cache_size = 10000;",
            
            # Views
            "CREATE VIEW active_products AS SELECT * FROM products WHERE stock > 0;",
            "CREATE TEMPORARY VIEW high_value_orders AS SELECT * FROM orders WHERE quantity * (SELECT price FROM products WHERE id = orders.product_id) > 1000;",
            "DROP VIEW IF EXISTS active_products;",
            "CREATE VIEW product_ratings AS SELECT p.id, p.name, AVG(r.rating) as avg_rating FROM products p LEFT JOIN reviews r ON p.id = r.product_id GROUP BY p.id;",

            # Tables
            "CREATE TEMPORARY TABLE popular_products AS SELECT .id, p.name, COUNT(o.id) AS order_count FROM products p JOIN orders o ON p.id = o.product_id GROUP BY p.id HAVING order_count > 5 ORDER BY order_count DESC;",
            
            # Triggers
            "CREATE TRIGGER update_stock AFTER INSERT ON orders BEGIN UPDATE products SET stock = stock - NEW.quantity WHERE id = NEW.product_id; END;",
            "CREATE TRIGGER check_age BEFORE INSERT ON users BEGIN SELECT CASE WHEN NEW.age < 13 THEN RAISE(ABORT, 'User must be at least 13 years old') END; END;",
            "DROP TRIGGER IF EXISTS update_stock;",
            "CREATE TRIGGER delete_reviews AFTER DELETE ON products BEGIN DELETE FROM reviews WHERE product_id = OLD.id; END;",
            
            # Upsert (INSERT OR ... ON CONFLICT)
            "INSERT INTO users (id, name, email, age) VALUES (1, 'Conflict User', 'conflict@example.com', 50) ON CONFLICT(id) DO UPDATE SET name = excluded.name, age = excluded.age;",
            "INSERT INTO products (id, name, price, category) VALUES (1, 'Conflict Product', 99.99, 'Electronics') ON CONFLICT(id) DO NOTHING;",
            "INSERT INTO users (id, name, email) VALUES (1, 'Test User', 'test@example.com') ON CONFLICT(id) WHERE id < 100 DO UPDATE SET name = excluded.name;",
            
            # Compound queries (multi-statement)
            "SELECT id, name FROM users WHERE age > 30; SELECT id, name FROM products WHERE price < 50;",
            "INSERT INTO logs VALUES (1, 'test', '2024-04-21'); SELECT * FROM logs;",
            
            # Edge cases with expressions
            "SELECT * FROM users WHERE age BETWEEN 20 AND 30;",
            "SELECT * FROM products WHERE category GLOB 'E*s';",
            "SELECT * FROM users WHERE email LIKE '%@example.com';",
            "SELECT * FROM users WHERE email NOT LIKE '%@gmail.com';",
            "SELECT * FROM products WHERE category REGEXP '^E.+s$';",
            "SELECT * FROM products WHERE name MATCH 'product';",
            "SELECT id & 1, id | 1, id << 1, id >> 1 FROM users;",
            "SELECT CAST(price AS INTEGER) FROM products;",
            "SELECT typeof(id), typeof(name), typeof(price) FROM products;",
            
            # Hypothetical functions (may not be in SQLite but testing for coverage)
            "SELECT JSON_EXTRACT('{\\'name\\': \\'value\\'}', '$.name');",
            "SELECT JSON_ARRAY(name, age) FROM users;",
            "SELECT IIF(age > 30, 'Over 30', 'Under 30') FROM users;",
            
            # Various JOIN syntaxes
            "SELECT * FROM users, orders WHERE users.id = orders.user_id;", # Implicit join
            "SELECT * FROM (SELECT * FROM users WHERE age > 30) AS older_users;", # FROM subquery
            
            # Complex nested queries
            "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE product_id IN (SELECT id FROM products WHERE category = 'Electronics'));",
            "SELECT * FROM users WHERE EXISTS (SELECT 1 FROM orders o JOIN products p ON o.product_id = p.id WHERE o.user_id = users.id AND p.category = 'Electronics');",
            
            # Common table expressions with multiple references
            "WITH user_stats AS (SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id) SELECT u.name, us.order_count FROM users u JOIN user_stats us ON u.id = us.user_id WHERE us.order_count > (SELECT AVG(order_count) FROM user_stats);",
            
            # ATTACH and DETACH database (virtualization)
            "ATTACH DATABASE ':memory:' AS mem;",
            "CREATE TABLE mem.temp_table (id INTEGER, value TEXT);",
            "INSERT INTO mem.temp_table VALUES (1, 'test');",
            "SELECT * FROM mem.temp_table;",
            "DETACH DATABASE mem;",
            
            # Virtual tables with FTS
            "CREATE VIRTUAL TABLE IF NOT EXISTS product_search USING fts5(name, category);",
            "INSERT INTO product_search(name, category) SELECT name, category FROM products;",
            "SELECT * FROM product_search WHERE product_search MATCH 'electronics';",
            "DROP TABLE IF EXISTS product_search;",
            
            # RAISE and error handling
            "BEGIN; SELECT RAISE(ABORT, 'Custom error message'); COMMIT;",
            "SELECT CASE WHEN age < 0 THEN RAISE(FAIL, 'Negative age') ELSE age END FROM users;",
            
            # WITH RECURSIVE for hierarchical data
            "WITH RECURSIVE numbered(num) AS (SELECT 1 UNION ALL SELECT num+1 FROM numbered WHERE num < 10) SELECT * FROM numbered;",
            
            # SQLite-specific functions (deterministic only)
            "SELECT changes(), total_changes(), last_insert_rowid();",
            "SELECT zeroblob(10), quote('string''with quotes');",
            
            # Constraints and CHECK expressions
            "CREATE TABLE IF NOT EXISTS temp_table (id INTEGER PRIMARY KEY, value TEXT CHECK(length(value) > 3), age INTEGER CHECK(age >= 18));",
            "DROP TABLE IF EXISTS temp_table;",
            
            # Additional query patterns
            "SELECT * FROM users WHERE (age BETWEEN 20 AND 30) AND (score BETWEEN 80 AND 100);",
            "SELECT * FROM products WHERE price IN (9.99, 19.99, 29.99, 39.99);",
            "SELECT * FROM users WHERE id IN (1, 3, 5, 7) AND age NOT IN (20, 30, 40);",
        ]
        
        return corpus
    