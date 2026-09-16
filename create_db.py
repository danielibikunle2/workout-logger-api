import sqlite3

conn = sqlite3.connect("workouts.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS Workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise TEXT NOT NULL,
    duration_minutes INTEGER,
    date TEXT NOT NULL,
    notes TEXT
);
""")

conn.commit()
conn.close()

print("Database and Workouts table created successfully.")