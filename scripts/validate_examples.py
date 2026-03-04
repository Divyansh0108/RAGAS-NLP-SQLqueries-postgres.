"""
Validate NL-SQL example queries against the live dvdrental database.
Run with: uv run python scripts/validate_examples.py
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from src.db.config import db_config

QUERIES = {
    # ── SIMPLE ──────────────────────────────────────────────────────────────
    "s01": "SELECT first_name, last_name FROM actor ORDER BY last_name LIMIT 10",
    "s02": "SELECT COUNT(*) AS total_films FROM film",
    "s03": "SELECT title, rental_rate FROM film ORDER BY rental_rate DESC LIMIT 5",
    "s04": "SELECT title, length FROM film ORDER BY length DESC LIMIT 10",
    "s05": "SELECT ROUND(AVG(rental_rate)::numeric, 2) AS avg_rental_rate FROM film",
    "s06": "SELECT rating, COUNT(*) AS cnt FROM film GROUP BY rating ORDER BY cnt DESC",
    "s07": "SELECT first_name, last_name, email FROM customer WHERE activebool = TRUE ORDER BY last_name LIMIT 5",
    "s08": "SELECT title, replacement_cost FROM film WHERE replacement_cost > 25 ORDER BY replacement_cost DESC LIMIT 5",
    "s09": "SELECT title, description FROM film WHERE rating = 'PG-13' ORDER BY title LIMIT 5",
    "s10": "SELECT name FROM category ORDER BY name",
    "s11": "SELECT title FROM film WHERE rental_duration <= 3 ORDER BY title LIMIT 10",
    "s12": "SELECT first_name, last_name FROM staff WHERE active = TRUE",
    "s13": "SELECT COUNT(*) AS total_customers FROM customer WHERE activebool = TRUE",
    "s14": "SELECT title, release_year FROM film WHERE release_year = 2006 ORDER BY title LIMIT 10",
    "s15": "SELECT DISTINCT rating FROM film ORDER BY rating",
    # ── MEDIUM ──────────────────────────────────────────────────────────────
    "m01": """
        SELECT a.first_name, a.last_name, COUNT(fa.film_id) AS film_count
        FROM actor a
        JOIN film_actor fa ON a.actor_id = fa.actor_id
        GROUP BY a.actor_id, a.first_name, a.last_name
        ORDER BY film_count DESC LIMIT 10
    """,
    "m02": """
        SELECT f.title, COUNT(r.rental_id) AS rental_count
        FROM film f
        JOIN inventory i ON f.film_id = i.film_id
        JOIN rental r ON i.inventory_id = r.inventory_id
        GROUP BY f.film_id, f.title
        ORDER BY rental_count DESC LIMIT 10
    """,
    "m03": """
        SELECT c.first_name, c.last_name, SUM(p.amount) AS total_spent
        FROM customer c
        JOIN payment p ON c.customer_id = p.customer_id
        GROUP BY c.customer_id, c.first_name, c.last_name
        HAVING SUM(p.amount) > 150
        ORDER BY total_spent DESC LIMIT 10
    """,
    "m04": """
        SELECT f.title, cat.name AS category
        FROM film f
        JOIN film_category fc ON f.film_id = fc.film_id
        JOIN category cat ON fc.category_id = cat.category_id
        WHERE cat.name = 'Action'
        ORDER BY f.title LIMIT 10
    """,
    "m05": """
        SELECT s.store_id, SUM(p.amount) AS total_revenue
        FROM store s
        JOIN staff st ON s.store_id = st.store_id
        JOIN payment p ON st.staff_id = p.staff_id
        GROUP BY s.store_id
    """,
    "m06": """
        SELECT f.title, f.rental_rate, l.name AS language
        FROM film f
        JOIN language l ON f.language_id = l.language_id
        ORDER BY f.rental_rate DESC LIMIT 10
    """,
    "m07": """
        SELECT c.first_name, c.last_name, COUNT(r.rental_id) AS rental_count
        FROM customer c
        JOIN rental r ON c.customer_id = r.customer_id
        GROUP BY c.customer_id, c.first_name, c.last_name
        ORDER BY rental_count DESC LIMIT 10
    """,
    "m08": """
        SELECT cat.name, COUNT(fc.film_id) AS film_count
        FROM category cat
        JOIN film_category fc ON cat.category_id = fc.category_id
        GROUP BY cat.name
        ORDER BY film_count DESC
    """,
    "m09": """
        SELECT f.title, f.length
        FROM film f
        JOIN film_category fc ON f.film_id = fc.film_id
        JOIN category c ON fc.category_id = c.category_id
        WHERE f.length > 120 AND c.name = 'Drama'
        ORDER BY f.length DESC LIMIT 10
    """,
    "m10": """
        SELECT cu.first_name, cu.last_name, co.country
        FROM customer cu
        JOIN address a ON cu.address_id = a.address_id
        JOIN city ci ON a.city_id = ci.city_id
        JOIN country co ON ci.country_id = co.country_id
        WHERE co.country = 'United States'
        ORDER BY cu.last_name LIMIT 10
    """,
    "m11": """
        SELECT f.rating, ROUND(AVG(p.amount)::numeric, 2) AS avg_payment
        FROM film f
        JOIN inventory i ON f.film_id = i.film_id
        JOIN rental r ON i.inventory_id = r.inventory_id
        JOIN payment p ON r.rental_id = p.rental_id
        GROUP BY f.rating
        ORDER BY avg_payment DESC
    """,
    "m12": """
        SELECT f.title, COUNT(i.inventory_id) AS copies_in_stock
        FROM film f
        JOIN inventory i ON f.film_id = i.film_id
        GROUP BY f.film_id, f.title
        ORDER BY copies_in_stock DESC LIMIT 10
    """,
    "m13": """
        SELECT DATE_TRUNC('month', payment_date) AS month,
               SUM(amount) AS monthly_revenue
        FROM payment
        GROUP BY month
        ORDER BY month
    """,
    "m14": """
        SELECT f.title, f.rental_rate
        FROM film f
        JOIN film_category fc ON f.film_id = fc.film_id
        JOIN category c ON fc.category_id = c.category_id
        WHERE c.name = 'Comedy' AND f.rental_rate < 3.00
        ORDER BY f.rental_rate, f.title LIMIT 10
    """,
    "m15": """
        SELECT cu.first_name, cu.last_name, COUNT(r.rental_id) AS rentals,
               SUM(p.amount) AS total_paid
        FROM customer cu
        JOIN rental r ON cu.customer_id = r.customer_id
        JOIN payment p ON r.rental_id = p.rental_id
        GROUP BY cu.customer_id, cu.first_name, cu.last_name
        ORDER BY total_paid DESC LIMIT 10
    """,
    # ── HARD ────────────────────────────────────────────────────────────────
    "h01": """
        SELECT f.title
        FROM film f
        WHERE f.film_id NOT IN (
            SELECT DISTINCT i.film_id
            FROM inventory i
            JOIN rental r ON i.inventory_id = r.inventory_id
        )
        ORDER BY f.title LIMIT 10
    """,
    "h02": """
        WITH customer_spend AS (
            SELECT customer_id, SUM(amount) AS total_spent
            FROM payment
            GROUP BY customer_id
        )
        SELECT c.first_name, c.last_name, cs.total_spent
        FROM customer c
        JOIN customer_spend cs ON c.customer_id = cs.customer_id
        WHERE cs.total_spent > (SELECT AVG(total_spent) FROM customer_spend)
        ORDER BY cs.total_spent DESC LIMIT 10
    """,
    "h03": """
        SELECT a.first_name, a.last_name,
               cat.name AS category,
               COUNT(fa.film_id) AS films_in_category
        FROM actor a
        JOIN film_actor fa ON a.actor_id = fa.actor_id
        JOIN film_category fc ON fa.film_id = fc.film_id
        JOIN category cat ON fc.category_id = cat.category_id
        GROUP BY a.actor_id, a.first_name, a.last_name, cat.category_id, cat.name
        ORDER BY films_in_category DESC LIMIT 10
    """,
    "h04": """
        SELECT cu.first_name, cu.last_name
        FROM customer cu
        WHERE cu.customer_id NOT IN (
            SELECT DISTINCT r.customer_id
            FROM rental r
            JOIN inventory i ON r.inventory_id = i.inventory_id
            JOIN film_category fc ON i.film_id = fc.film_id
            JOIN category c ON fc.category_id = c.category_id
            WHERE c.name = 'Action'
        )
        ORDER BY cu.last_name LIMIT 10
    """,
    "h05": """
        SELECT EXTRACT(YEAR FROM payment_date) AS year,
               EXTRACT(MONTH FROM payment_date) AS month,
               SUM(amount) AS revenue,
               RANK() OVER (
                   PARTITION BY EXTRACT(YEAR FROM payment_date)
                   ORDER BY SUM(amount) DESC
               ) AS rank_in_year
        FROM payment
        GROUP BY year, month
        ORDER BY year, rank_in_year LIMIT 24
    """,
    "h06": """
        WITH ranked AS (
            SELECT c.first_name, c.last_name,
                   COUNT(r.rental_id) AS rental_count,
                   RANK() OVER (ORDER BY COUNT(r.rental_id) DESC) AS rnk
            FROM customer c
            JOIN rental r ON c.customer_id = r.customer_id
            GROUP BY c.customer_id, c.first_name, c.last_name
        )
        SELECT first_name, last_name, rental_count, rnk
        FROM ranked WHERE rnk <= 5
    """,
    "h07": """
        SELECT f.title,
               COUNT(r.rental_id) AS times_rented,
               ROUND(SUM(p.amount)::numeric, 2) AS total_revenue,
               ROUND(AVG(p.amount)::numeric, 2) AS avg_payment
        FROM film f
        JOIN inventory i ON f.film_id = i.film_id
        JOIN rental r ON i.inventory_id = r.inventory_id
        JOIN payment p ON r.rental_id = p.rental_id
        GROUP BY f.film_id, f.title
        ORDER BY total_revenue DESC LIMIT 10
    """,
    "h08": """
        SELECT co.country, COUNT(DISTINCT cu.customer_id) AS customers,
               ROUND(SUM(p.amount)::numeric, 2) AS total_revenue
        FROM country co
        JOIN city ci ON co.country_id = ci.country_id
        JOIN address a ON ci.city_id = a.city_id
        JOIN customer cu ON a.address_id = cu.address_id
        JOIN payment p ON cu.customer_id = p.customer_id
        GROUP BY co.country_id, co.country
        ORDER BY total_revenue DESC LIMIT 10
    """,
    "h09": """
        SELECT f.title,
               f.rental_rate,
               AVG(f.rental_rate) OVER (
                   PARTITION BY fc.category_id
               ) AS avg_rate_in_category,
               f.rental_rate - AVG(f.rental_rate) OVER (
                   PARTITION BY fc.category_id
               ) AS diff_from_category_avg
        FROM film f
        JOIN film_category fc ON f.film_id = fc.film_id
        ORDER BY diff_from_category_avg DESC LIMIT 10
    """,
    "h10": """
        WITH monthly AS (
            SELECT DATE_TRUNC('month', payment_date) AS month,
                   SUM(amount) AS revenue
            FROM payment GROUP BY month
        )
        SELECT month, revenue,
               LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue,
               ROUND(
                   (revenue - LAG(revenue) OVER (ORDER BY month))
                   / NULLIF(LAG(revenue) OVER (ORDER BY month), 0) * 100,
               2) AS pct_change
        FROM monthly ORDER BY month
    """,
}


def main():
    conn = psycopg2.connect(db_config.connection_string)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    passed, failed = [], []

    for qid, sql in QUERIES.items():
        try:
            cur.execute(sql)
            rows = cur.fetchall()
            passed.append(qid)
            print(f"  OK  {qid}  ({len(rows)} rows)")
        except Exception as e:
            failed.append((qid, str(e)))
            print(f" FAIL {qid}  {e}")
            conn.rollback()

    cur.close()
    conn.close()
    print(f"\nPassed: {len(passed)}/{len(QUERIES)}  |  Failed: {len(failed)}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
