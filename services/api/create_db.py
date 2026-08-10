import psycopg2
from psycopg2 import sql

def create():
    try:
        # Try connecting with user postgres, empty password or 'postgres'
        conn = None
        for pwd in ["", "postgres", "admin", "root"]:
            try:
                conn = psycopg2.connect(dbname="postgres", user="postgres", password=pwd, host="localhost")
                print(f"Connected with password: '{pwd}'")
                break
            except Exception as e:
                pass
        
        if not conn:
            print("Failed to connect to default postgres DB.")
            return

        conn.autocommit = True
        cur = conn.cursor()
        
        # Create user
        try:
            cur.execute("CREATE USER himma WITH PASSWORD 'himmapass';")
            print("Created user himma")
        except psycopg2.errors.DuplicateObject:
            print("User himma already exists")
            cur.execute("ALTER USER himma WITH PASSWORD 'himmapass';")
            print("Updated password for himma")
            
        # Create DB
        try:
            cur.execute("CREATE DATABASE himma_db OWNER himma;")
            print("Created database himma_db")
        except psycopg2.errors.DuplicateDatabase:
            print("Database himma_db already exists")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create()
