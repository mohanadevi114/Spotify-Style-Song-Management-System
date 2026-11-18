from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'spotify_secret_key'

# MySQL Database Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Mohana@1008'  # <-- Inga mee actual MySQL Password
app.config['MYSQL_DB'] = 'spotify_db'

mysql = MySQL(app)

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()
        cursor.close()
        
        if account:
            session['loggedin'] = True
            session['id'] = account['user_id']
            session['username'] = account['username']
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect Username / Password!'
            
    return render_template('login.html', msg=msg)

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        
        if account:
            msg = 'Account already exists!'
        else:
            cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)', (username, email, password))
            mysql.connection.commit()
            cursor.close()
            return redirect(url_for('login'))
            
    return render_template('register.html', msg=msg)

# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Home Page Route
@app.route('/')
@app.route('/home')
def home():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM albums")
    albums = cursor.fetchall()
    
    cursor.execute("""
        SELECT songs.*, albums.artist 
        FROM songs 
        LEFT JOIN albums ON songs.album_id = albums.album_id
    """)
    songs = cursor.fetchall()
    cursor.close()
    
    return render_template('home.html', albums=albums, songs=songs, username=session['username'])

# Search Page Route
@app.route('/search')
def search():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    query = request.args.get('query', '').strip()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if query:
        search_query = "%" + query + "%"
        cursor.execute("""
            SELECT songs.*, albums.artist 
            FROM songs 
            LEFT JOIN albums ON songs.album_id = albums.album_id 
            WHERE songs.song_name LIKE %s OR albums.artist LIKE %s OR albums.genre LIKE %s
        """, (search_query, search_query, search_query))
    else:
        cursor.execute("""
            SELECT songs.*, albums.artist 
            FROM songs 
            LEFT JOIN albums ON songs.album_id = albums.album_id
        """)
        
    songs = cursor.fetchall()
    
    # User-oda playlists retrieve pannanum dropdown menu-kku
    cursor.execute("SELECT * FROM playlists WHERE user_id = %s", (session['id'],))
    playlists = cursor.fetchall()
    cursor.close()
    
    return render_template('search.html', songs=songs, playlists=playlists, query=query, username=session['username'])

# Create Playlist Route
@app.route('/create_playlist', methods=['POST'])
def create_playlist():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    playlist_name = request.form.get('playlist_name')
    if playlist_name:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO playlists (user_id, playlist_name) VALUES (%s, %s)", (session['id'], playlist_name))
        mysql.connection.commit()
        cursor.close()
        
    return redirect(url_for('profile'))

# Add Song to Playlist Route
@app.route('/add_to_playlist', methods=['POST'])
def add_to_playlist():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    song_id = request.form.get('song_id')
    playlist_id = request.form.get('playlist_id')
    
    if song_id and playlist_id:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO playlist_songs (playlist_id, song_id) VALUES (%s, %s)", (playlist_id, song_id))
        mysql.connection.commit()
        cursor.close()
        
    return redirect(url_for('profile'))

# Add to Favourites Route
@app.route('/add_favourite/<int:song_id>', methods=['POST'])
def add_favourite(song_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM favourites WHERE user_id = %s AND song_id = %s", (session['id'], song_id))
    fav = cursor.fetchone()
    
    if not fav:
        cursor.execute("INSERT INTO favourites (user_id, song_id) VALUES (%s, %s)", (session['id'], song_id))
        mysql.connection.commit()
        
    cursor.close()
    return redirect(url_for('profile'))

# Profile Page Route
@app.route('/profile')
def profile():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # 1. Fetch User Info
    cursor.execute("SELECT username, email FROM users WHERE user_id = %s", (session['id'],))
    user_info = cursor.fetchone()
    
    # 2. Fetch User Playlists with Song details
    cursor.execute("SELECT * FROM playlists WHERE user_id = %s", (session['id'],))
    playlists = cursor.fetchall()
    
    for p in playlists:
        cursor.execute("""
            SELECT songs.*, albums.artist 
            FROM playlist_songs 
            JOIN songs ON playlist_songs.song_id = songs.song_id 
            LEFT JOIN albums ON songs.album_id = albums.album_id
            WHERE playlist_songs.playlist_id = %s
        """, (p['playlist_id'],))
        p['songs'] = cursor.fetchall()
        
    # 3. Fetch Favourite Songs
    cursor.execute("""
        SELECT songs.*, albums.artist 
        FROM favourites 
        JOIN songs ON favourites.song_id = songs.song_id 
        LEFT JOIN albums ON songs.album_id = albums.album_id
        WHERE favourites.user_id = %s
    """, (session['id'],))
    fav_songs = cursor.fetchall()
    
    cursor.close()
    
    return render_template('profile.html', user=user_info, playlists=playlists, fav_songs=fav_songs, username=session['username'])

if __name__ == '__main__':
    app.run(debug=True)