from flask import Flask, request, jsonify
import sqlite3
from datetime import date

app = Flask(__name__)
DB_NAME = "workouts.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn


@app.route("/")
def home():
    return jsonify({"message": "Workout Logger API is running."})


@app.route("/workouts", methods=["POST"])
def log_workout():
    data = request.get_json()

    if not data or "exercise" not in data:
        return jsonify({"error": "Missing required field: exercise"}), 400

    exercise = data["exercise"]
    duration = data.get("duration_minutes")
    notes = data.get("notes", "")
    workout_date = data.get("date", str(date.today()))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Workouts (exercise, duration_minutes, date, notes) VALUES (?, ?, ?, ?)",
        (exercise, duration, workout_date, notes),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({"message": "Workout logged.", "id": new_id}), 201


@app.route("/workouts", methods=["GET"])
def get_workouts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Workouts ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()

    workouts = [dict(row) for row in rows]
    return jsonify(workouts)


@app.route("/workouts/summary", methods=["GET"])
def workout_summary():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT exercise, COUNT(*) as times_done, SUM(duration_minutes) as total_minutes
        FROM Workouts
        GROUP BY exercise
        ORDER BY times_done DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    summary = [dict(row) for row in rows]
    return jsonify(summary)


if __name__ == "__main__":
    app.run(debug=True, port=5000)