# db_init.py
from my_helpers import get_connection


def init_tables():
    """Creates all tables specified by the schema.sql file"""
    conn = get_connection()
    with open("schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_tables()
    print("DB initialisiert")