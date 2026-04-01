import sqlite3
from pathlib import Path


def resolve_db_path() -> Path:
    base = Path(__file__).resolve().parent
    candidates = [
        base / "instance" / "assetguard.db",
        base / "assetguard.db",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("Could not find assetguard.db in project root or instance/.")


def print_query(cursor, title: str, sql: str) -> None:
    print(f"\n=== {title} ===")
    cursor.execute(sql)
    rows = cursor.fetchall()
    if not rows:
        print("(empty)")
        return
    for row in rows:
        print(row)


def main() -> None:
    db_path = resolve_db_path()
    print(f"Using database: {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()

        print_query(
            cursor,
            "tables",
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
        )

        print_query(
            cursor,
            "locations",
            "SELECT id, name FROM locations ORDER BY id",
        )

        print_query(
            cursor,
            "assets",
            "SELECT id, name, location_id FROM assets ORDER BY id",
        )

        print_query(
            cursor,
            "load_capacities",
            "SELECT id, asset_id, name, metric, max_load, details FROM load_capacities ORDER BY asset_id, id",
        )

        print_query(
            cursor,
            "assets_with_locations",
            """
            SELECT a.id, a.name, l.name AS location_name
            FROM assets a
            JOIN locations l ON l.id = a.location_id
            ORDER BY a.id
            """,
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
