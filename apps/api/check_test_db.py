from sqlalchemy import create_engine, text

e = create_engine("sqlite:///test.db")
with e.connect() as conn:
    r = conn.execute(text("SELECT id, connection_metadata FROM social_connections WHERE id = 'test-linkedin-conn-sync'"))
    rows = list(r)
    print(f"Found {len(rows)} rows")
    for row in rows:
        print(f"  id={row[0]}, metadata={row[1]}")
