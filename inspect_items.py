
import sqlite3

def inspect_db():
    conn = sqlite3.connect('aeropost.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Buscar IDs especificos
    items = cursor.execute("SELECT id, internal_id, status, location FROM items WHERE internal_id IN ('AP-20260115-Q066', 'AP-20260115-WMD0')").fetchall()
    
    print("-" * 60)
    print(f"{'ID':<5} | {'Internal ID':<15} | {'Status':<20} | {'Location'}")
    print("-" * 60)
    
    for item in items:
        # Truncate strings for display
        status = str(item['status'])[:20]
        location = str(item['location']) if item['location'] else "NULL"
        print(f"{item['id']:<5} | {item['internal_id']:<15} | {status:<20} | {location}")

if __name__ == "__main__":
    inspect_db()
