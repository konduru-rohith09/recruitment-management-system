
import sqlite3
from dotenv import load_dotenv

# Load .env BEFORE importing the database engine
load_dotenv(r"D:\yottaflex.ai\.env", override=True)

from sqlalchemy import inspect, text
from src.database import engine

SQLITE_PATH = r"D:\yottaflex.ai\data\recruitment.db"



def main():
    source = sqlite3.connect(SQLITE_PATH)
    source.row_factory = sqlite3.Row

    try:
        inspector = inspect(engine)

        sqlite_tables = {
            row[0]
            for row in source.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        mysql_tables = set(inspector.get_table_names())

        if sqlite_tables != mysql_tables:
            raise RuntimeError(
                f"Table mismatch. SQLite only: "
                f"{sorted(sqlite_tables - mysql_tables)}; "
                f"MySQL only: {sorted(mysql_tables - sqlite_tables)}"
            )

        # Check that every destination table is empty.
        with engine.connect() as conn:
            for table in sorted(mysql_tables):
                count = conn.execute(
                    text(f"SELECT COUNT(*) FROM `{table}`")
                ).scalar_one()
                if count != 0:
                    raise RuntimeError(
                        f"MySQL table '{table}' is not empty "
                        f"({count} rows). No migration performed."
                    )

        # Check column names before transferring data.
        for table in sorted(sqlite_tables):
            sqlite_columns = {
                row[1]
                for row in source.execute(
                    f'PRAGMA table_info("{table}")'
                )
            }
            mysql_columns = {
                col["name"]
                for col in inspector.get_columns(table)
            }
            if sqlite_columns != mysql_columns:
                raise RuntimeError(
                    f"Column mismatch in {table}: "
                    f"SQLite-only={sqlite_columns - mysql_columns}; "
                    f"MySQL-only={mysql_columns - sqlite_columns}"
                )

        # Parent tables must be inserted before their child tables.
        dependencies = {table: set() for table in mysql_tables}
        for table in mysql_tables:
            for fk in inspector.get_foreign_keys(table):
                parent = fk.get("referred_table")
                if parent in mysql_tables and parent != table:
                    dependencies[table].add(parent)

        order = []
        remaining = {t: set(d) for t, d in dependencies.items()}

        while remaining:
            ready = sorted(
                t for t, deps in remaining.items() if not deps
            )
            if not ready:
                raise RuntimeError(
                    "Circular foreign-key dependencies detected: "
                    f"{remaining}. Migration stopped safely."
                )

            for table in ready:
                order.append(table)
                remaining.pop(table)
            for deps in remaining.values():
                deps.difference_update(ready)

        print("Migration order:", " -> ".join(order))

        # Copy all tables inside one transaction.
        counts = {}
        with engine.begin() as conn:
            for table in order:
                columns = [
                    col["name"]
                    for col in inspector.get_columns(table)
                ]
                rows = source.execute(
                    f'SELECT * FROM "{table}"'
                ).fetchall()

                if rows:
                    column_sql = ", ".join(
                        f"`{col}`" for col in columns
                    )
                    placeholders = ", ".join(
                        f":p{i}" for i in range(len(columns))
                    )
                    statement = text(
                        f"INSERT INTO `{table}` ({column_sql}) "
                        f"VALUES ({placeholders})"
                    )

                    batch = [
                        {f"p{i}": row[col] for i, col in enumerate(columns)}
                        for row in rows
                    ]
                    conn.execute(statement, batch)

                actual = conn.execute(
                    text(f"SELECT COUNT(*) FROM `{table}`")
                ).scalar_one()

                if actual != len(rows):
                    raise RuntimeError(
                        f"Count mismatch for {table}: "
                        f"source={len(rows)}, destination={actual}"
                    )

                counts[table] = actual
                print(f"{table}: {actual} rows copied and verified")

        print("\nSUCCESS: Migration committed.")
        print("Total tables:", len(counts))
        print("Total rows:", sum(counts.values()))

    finally:
        source.close()


if __name__ == "__main__":
    main()
