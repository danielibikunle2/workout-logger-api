import os
from functools import wraps

from flask import Flask, request, jsonify
import sqlite3
from datetime import date

app = Flask(__name__)
DB_NAME = "workouts.db"
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    print("WARNING: API_KEY is not set. POST/DELETE endpoints are unprotected.")


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not API_KEY:
            return f(*args, **kwargs)
        provided = request.headers.get("X-API-Key")
        if provided != API_KEY:
            return jsonify({"error": "Missing or invalid API key."}), 401
        return f(*args, **kwargs)
    return decorated


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return jsonify({"message": "Workout Logger API is running."})


@app.route("/workouts", methods=["POST"])
@require_api_key
def log_workout():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    exercise = data.get("exercise")
    if not exercise or not isinstance(exercise, str) or not exercise.strip():
        return jsonify({"error": "Missing or invalid required field: exercise"}), 400

    duration = data.get("duration_minutes")
    if duration is not None:
        # Some clients (e.g. n8n, form submissions) send numbers as strings — try to convert.
        try:
            duration = float(duration)
            if duration.is_integer():
                duration = int(duration)
        except (TypeError, ValueError):
            return jsonify({"error": "duration_minutes must be a positive number."}), 400
        if duration < 0:
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
@require_api_key
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
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)