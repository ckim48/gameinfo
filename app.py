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
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            image_filename TEXT NOT NULL,
            email TEXT NOT NULL,
            verified INTEGER DEFAULT 0  -- New column for verification status
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            review TEXT NOT NULL,
            FOREIGN KEY (game_id) REFERENCES games (id)
        )
    ''')
    conn.commit()
    conn.close()


create_table()

@app.route('/')
def index():
    conn = get_db_connection()
    games = conn.execute('SELECT * FROM games WHERE verified = 1').fetchall()
    conn.close()

    return render_template('index.html', games=games)


# Route to display individual game details
@app.route('/details/<int:game_id>', methods=['GET', 'POST'])
def details(game_id):
    conn = get_db_connection()

    if request.method == 'POST':
        name = request.form['name']
        review = request.form['review']

        if name and review:
            conn.execute('INSERT INTO reviews (game_id, name, review) VALUES (?, ?, ?)',
                         (game_id, name, review))
            conn.commit()
            flash('Review submitted successfully!')

    game = conn.execute('SELECT * FROM games WHERE id = ?', (game_id,)).fetchone()
    reviews = conn.execute('SELECT * FROM reviews WHERE game_id = ?', (game_id,)).fetchall()
    conn.close()

    if game is None:
        flash("Game not found!")
        return redirect(url_for('index'))

    return render_template('portfolio-details.html', game=game, reviews=reviews)


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
    email = request.form['email']

    # Set default source if empty
    if source == "":
        source = None

    if not title or not category or not description:
        flash('All fields are required!', 'danger')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))

        # Insert game into database with verified set to 0
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO games (title, category, description, image_filename, email, verified)
            VALUES (?, ?, ?, ?, ?, 0)
        ''', (title, category, description, unique_filename, email))
        conn.commit()
        conn.close()

        flash(
            'Thank you for submitting your game. Your game will be reviewed, and you will receive an email with updates soon.',
            'success')
    else:
        flash('Invalid file type. Please upload a valid image file.', 'danger')

    return redirect(url_for('add_game'))


if __name__ == '__main__':
    app.run(debug=True)
