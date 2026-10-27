
import sqlite3
from dotenv import load_dotenv
from sqlalchemy import text
from src.database import engine

load_dotenv(r"D:\yottaflex.ai\.env", override=True)

source = sqlite3.connect(r"D:\yottaflex.ai\data\recruitment.db")
conn = engine.connect()

tables = source.execute("""
    SELECT name FROM sqlite_master
    WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
    ORDER BY name
""").fetchall()

errors = []
total = 0

try:
    for (table,) in tables:
        sqlite_count = source.execute(
            f'SELECT COUNT(*) FROM "{table}"'
        ).fetchone()[0]

        mysql_count = conn.execute(
            text(f"SELECT COUNT(*) FROM `{table}`")
        ).scalar_one()

        total += mysql_count
        status = "MATCH" if sqlite_count == mysql_count else "MISMATCH"

        print(
            f"{table}: SQLite={sqlite_count}, "
            f"MySQL={mysql_count} -> {status}"
        )

        if sqlite_count != mysql_count:
            errors.append(table)

    print("\nTotal MySQL rows:", total)
    print(
        "Overall result:",
        "PASS" if not errors and len(tables) == 21
        else "CHECK REQUIRED"
    )
finally:
    conn.close()
    source.close()
