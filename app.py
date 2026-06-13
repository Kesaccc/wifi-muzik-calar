from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from mutagen.mp3 import MP3
import pygame
import os
import json
import hashlib
import time
from functools import wraps

app = Flask(__name__)
app.secret_key = 'okul-projesi-gizli-anahtar-degistir-123'

pygame.mixer.init()

BASE_DIR = os.path.dirname(__file__)
MUSIC_DIR = os.path.join(BASE_DIR, 'static', 'music')
USERS_FILE = os.path.join(BASE_DIR, 'users.json')

current_file = None
is_playing = False

# Brute-force kilidi icin
MAX_ATTEMPTS = 5          # kac yanlis denemeden sonra
LOCK_SECONDS = 60         # kac saniye kilitlensin
failed_attempts = 0
lock_until = 0            # bu zamana kadar kilitli (unix time)


# ---------- Kullanici yonetimi ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(USERS_FILE):
        # Ilk acilista varsayilan kullanici: admin / 1234
        default = {'admin': hash_password('1234')}
        with open(USERS_FILE, 'w') as f:
            json.dump(default, f)
        return default
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)


# ---------- Giris kontrolu ----------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


@app.route('/login', methods=['GET', 'POST'])
def login():
    global failed_attempts, lock_until

    # Kilitli mi kontrol et
    now = time.time()
    if now < lock_until:
        kalan = int(lock_until - now)
        return render_template('login.html',
                               error='Cok fazla yanlis deneme! ' + str(kalan) + ' saniye bekleyin.')

    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        users = load_users()
        if username in users and users[username] == hash_password(password):
            session['logged_in'] = True
            session['username'] = username
            failed_attempts = 0
            return redirect(url_for('index'))
        else:
            failed_attempts += 1
            if failed_attempts >= MAX_ATTEMPTS:
                lock_until = time.time() + LOCK_SECONDS
                failed_attempts = 0
                return render_template('login.html',
                                       error='Cok fazla yanlis deneme! ' + str(LOCK_SECONDS) + ' saniye kilitlendi.')
            kalan = MAX_ATTEMPTS - failed_attempts
            return render_template('login.html',
                                   error='Kullanici adi veya sifre yanlis. (' + str(kalan) + ' deneme hakkiniz kaldi)')

    return render_template('login.html', error=None)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old = request.form.get('old_password', '')
        new = request.form.get('new_password', '')
        users = load_users()
        username = session['username']
        if users.get(username) != hash_password(old):
            return render_template('change_password.html', error='Eski sifre yanlis', success=None)
        if len(new) < 4:
            return render_template('change_password.html', error='Yeni sifre en az 4 karakter olmali', success=None)
        users[username] = hash_password(new)
        save_users(users)
        return render_template('change_password.html', error=None, success='Sifre basariyla degistirildi')
    return render_template('change_password.html', error=None, success=None)


# ---------- Muzik ----------
def get_music_files():
    files = []
    if os.path.exists(MUSIC_DIR):
        for f in sorted(os.listdir(MUSIC_DIR)):
            if f.lower().endswith('.mp3'):
                files.append(f)
    return files

@app.route('/')
@login_required
def index():
    songs = get_music_files()
    return render_template('index.html', songs=songs, username=session.get('username'))

@app.route('/api/songs')
@login_required
def api_songs():
    return jsonify(get_music_files())

@app.route('/api/play', methods=['POST'])
@login_required
def play():
    global current_file, is_playing
    data = request.json
    filename = data.get('filename')
    start_seconds = float(data.get('start_seconds', 0))
    filepath = os.path.join(MUSIC_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'Dosya bulunamadi'}), 404
    pygame.mixer.music.load(filepath)
    pygame.mixer.music.play(start=start_seconds)
    current_file = filename
    is_playing = True
    return jsonify({'status': 'playing', 'file': filename, 'start': start_seconds})

@app.route('/api/pause', methods=['POST'])
@login_required
def pause():
    global is_playing
    pygame.mixer.music.pause()
    is_playing = False
    return jsonify({'status': 'paused'})

@app.route('/api/resume', methods=['POST'])
@login_required
def resume():
    global is_playing
    pygame.mixer.music.unpause()
    is_playing = True
    return jsonify({'status': 'playing'})

@app.route('/api/stop', methods=['POST'])
@login_required
def stop():
    global current_file, is_playing
    pygame.mixer.music.stop()
    current_file = None
    is_playing = False
    return jsonify({'status': 'stopped'})

@app.route('/api/status')
@login_required
def status():
    playing = pygame.mixer.music.get_busy()
    return jsonify({
        'is_playing': playing,
        'current_file': current_file,
    })

@app.route('/api/duration', methods=['POST'])
@login_required
def duration():
    data = request.json
    filename = data.get('filename')
    filepath = os.path.join(MUSIC_DIR, filename)
    try:
        audio = MP3(filepath)
        return jsonify({'duration': audio.info.length})
    except:
        return jsonify({'duration': 0})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
