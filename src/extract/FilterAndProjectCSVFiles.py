import argparse
import csv
import sqlite3
import re
from pathlib import Path
 
def get_table_name(file_path):
    # strip of pattern at end of file indicating date and time stamp,
    # e.g._11-12-2023-225308
    p = re.compile('[a-zA-Z]([\w_]*[a-zA-Z])?')
    m = p.match(file_path.stem)
    return file_path.stem[:m.end()]

def exists_table(tablename: str, connection: sqlite3.Connection):
    cursor = connection.cursor() 
    # get the count of tables with the name  
    cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name=? ", (tablename, ))
    # if the count is 1, then table exists 
    return cursor.fetchone()[0] == 1

def insert_data(table_name:str, header:list, connection: sqlite3.Connection):
    # insert all records after the header
    connection.execute(f"INSERT INTO {table_name} ({','.join(header)}) SELECT {','.join(header)} FROM temp_table LIMIT -1 OFFSET 2")

def create_sql_table(file_path: Path, header:list, connection: sqlite3.Connection):
    table_name = get_table_name(file_path)
    
    if exists_table(table_name, connection):
        # insert data into existing table
        insert_data(table_name, header, connection)
    else:
        # create new table
        connection.execute(f"CREATE TABLE {table_name} AS SELECT DISTINCT * FROM temp_table")
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

    create_sql_table(file_path, header, connection)
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
