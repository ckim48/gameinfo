import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
import uuid

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For session management, flashing messages
app.config['UPLOAD_FOLDER'] = 'static/uploads/'  # Where images will be stored
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to connect to SQLite database
def get_db_connection():
    conn = sqlite3.connect('games.db')
    conn.row_factory = sqlite3.Row  # For accessing columns by name
    return conn

# Create the games table if it doesn't exist
def create_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            image_filename TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_table()  # Ensure the table is created when the app starts

@app.route('/')
def index():
    conn = get_db_connection()
    games = conn.execute('SELECT * FROM games').fetchall()
    conn.close()

    return render_template('index.html', games=games)

# Route to display individual game details
@app.route('/details/<int:game_id>')
def details(game_id):
    conn = get_db_connection()
    game = conn.execute('SELECT * FROM games WHERE id = ?', (game_id,)).fetchone()
    conn.close()

    if game is None:
        flash("Game not found!")
        return redirect(url_for('index'))

    return render_template('portfolio-details.html', game=game)

@app.route('/add_game')
def add_game():
    return render_template('add_game.html')

@app.route('/submit-game', methods=['POST'])
def submit_game():
    # Get form data
    title = request.form['gameTitle']
    category = request.form['gameCategory']
    description = request.form['gameDescription']
    file = request.files['gameImage']
    source = request.form['gameLink']
    if source == "":
        source = None

    if not title or not category or not description:
        flash('All fields are required!')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        file.save(filepath)
    else:
        flash('Invalid file type! Only images are allowed.')
        return redirect(request.url)

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO games (title, category, description, image_filename, source) VALUES (?, ?, ?, ?,?)',
        (title, category, description, unique_filename, source)
    )
    conn.commit()
    conn.close()

    flash('Game submitted successfully!')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
