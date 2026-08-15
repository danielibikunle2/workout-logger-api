from flask import Flask, request, jsonify
import sqlite3
from datetime import date

app = Flask(__name__)
DB_NAME = "workouts.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  
    return conn


@app.route("/")
def home():
    return jsonify({"message": "Workout Logger API is running."})


@app.route("/workouts", methods=["POST"])
def log_workout():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    exercise = data.get("exercise")
    if not exercise or not isinstance(exercise, str) or not exercise.strip():
        return jsonify({"error": "Missing or invalid required field: exercise"}), 400

    duration = data.get("duration_minutes")
    if duration is not None:
        if not isinstance(duration, (int, float)) or duration < 0:
            return jsonify({"error": "duration_minutes must be a positive number."}), 400

    notes = data.get("notes", "")
    workout_date = data.get("date", str(date.today()))

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Workouts (exercise, duration_minutes, date, notes) VALUES (?, ?, ?, ?)",
            (exercise.strip(), duration, workout_date, notes),
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500

    return jsonify({"message": "Workout logged.", "id": new_id}), 201


@app.route("/workouts", methods=["GET"])
def get_workouts():
    exercise_filter = request.args.get("exercise")

    conn = get_connection()
    cursor = conn.cursor()
    if exercise_filter:
        cursor.execute(
            "SELECT * FROM Workouts WHERE exercise = ? ORDER BY date DESC",
            (exercise_filter,),
        )
    else:
        cursor.execute("SELECT * FROM Workouts ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()

    workouts = [dict(row) for row in rows]
    return jsonify(workouts)


@app.route("/workouts/<int:workout_id>", methods=["DELETE"])
def delete_workout(workout_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Workouts WHERE id = ?", (workout_id,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify({"error": f"No workout found with id {workout_id}."}), 404

    cursor.execute("DELETE FROM Workouts WHERE id = ?", (workout_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Workout {workout_id} deleted."})


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "That endpoint doesn't exist."}), 404


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