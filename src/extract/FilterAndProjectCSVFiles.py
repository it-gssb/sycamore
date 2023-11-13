import argparse
import csv
import sqlite3
from pathlib import Path


def create_sql_table(file_path: Path, connection: sqlite3.Connection):
    table_name = file_path.stem
    connection.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT DISTINCT * FROM temp_table")
    connection.commit()


def import_csv_to_sqlite(file_path: Path, connection: sqlite3.Connection):
    with open(file_path, "r") as f:
        reader = csv.reader(f)
        header = [txt.replace(' ', '') for txt in next(reader)]

        # Create temporary table with the proper columns based on the header
        connection.execute(f"CREATE TEMPORARY TABLE temp_table ({','.join(header)})")

        connection.execute(f"INSERT INTO temp_table ({','.join(header)}) VALUES ({','.join(['?' for _ in header])})", header)
        for row in reader:
            connection.execute(f"INSERT INTO temp_table ({','.join(header)}) VALUES ({','.join(['?' for _ in header])})", row)

    create_sql_table(file_path, connection)
    connection.execute("DROP TABLE temp_table;")


def main(args: argparse.Namespace):
    conn = sqlite3.connect(":memory:")

    for file in args.files:
        file_path = Path(file)
        import_csv_to_sqlite(file_path, conn)

    if args.query is None:
        while True:
            query = input("Enter your SQL query: ")
            try:
                result = conn.execute(query).fetchall()
                print(result)
                save_results = input("Do you want to save the results? (y/n): ").lower()
                if save_results == 'y':
                    args.query = query
                    break
            except Exception as e:
                print(f"Error: {e}")
    else:
        result = conn.execute(args.query).fetchall()

    if args.out:
        with open(args.out, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(result)

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter CSV files and save the results")
    parser.add_argument("files", nargs="+", help="Paths to CSV files")
    parser.add_argument("--query", help="SQL query to run on the imported data")
    parser.add_argument("--out", help="Path to save the results as a new CSV file")
    args = parser.parse_args()

    main(args)
