from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from mutagen.mp3 import MP3
import pygame
import os
import json
import hashlib
import time
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)

# Rastgele uretilmis gizli anahtar (oturum cerezlerini imzalar)
app.secret_key = '835a21343675be695fae9c99c7afeb831700f657cab2aa63525e223696797022'

# Oturum hareketsizlik suresi: 15 dakika
INACTIVITY_MINUTES = 15
app.permanent_session_lifetime = timedelta(minutes=INACTIVITY_MINUTES)

pygame.mixer.init()

BASE_DIR = os.path.dirname(__file__)
MUSIC_DIR = os.path.join(BASE_DIR, 'static', 'music')
USERS_FILE = os.path.join(BASE_DIR, 'users.json')
LOG_FILE = os.path.join(BASE_DIR, 'login.log')

current_file = None
is_playing = False

# Brute-force kilidi (IP bazli)
MAX_ATTEMPTS = 5          # kac yanlis denemeden sonra
LOCK_SECONDS = 60         # kac saniye kilitlensin
# IP bazli takip: { "ip": {"attempts": 0, "lock_until": 0} }
attempt_tracker = {}


# ---------- Yardimci ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_client_ip():
    return request.remote_addr or 'bilinmeyen'

def write_log(username, ip, result):
    # Sifre ASLA log'a yazilmaz - sadece kim/ne zaman/nereden/sonuc
    line = '{} | IP: {} | Kullanici: {} | Sonuc: {}\n'.format(
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ip, username, result)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line)
    except:
        pass


# ---------- Kullanici yonetimi ----------
def load_users():
    if not os.path.exists(USERS_FILE):
        # Ilk acilista varsayilan kullanici
        default = {'IBMTAL': hash_password('Alanya2025!')}
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


# Her istekte hareketsizlik suresini kontrol et
@app.before_request
def check_inactivity():
    if session.get('logged_in'):
        now = time.time()
        last = session.get('last_activity', now)
        if now - last > INACTIVITY_MINUTES * 60:
            session.clear()
            return redirect(url_for('login'))
        session['last_activity'] = now
        session.permanent = True


@app.route('/login', methods=['GET', 'POST'])
def login():
    ip = get_client_ip()
    now = time.time()

    # Bu IP kilitli mi?
    info = attempt_tracker.get(ip, {'attempts': 0, 'lock_until': 0})
    if now < info['lock_until']:
        kalan = int(info['lock_until'] - now)
        return render_template('login.html',
                               error='Cok fazla yanlis deneme! ' + str(kalan) + ' saniye bekleyin.')

    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        users = load_users()

        if username in users and users[username] == hash_password(password):
            session['logged_in'] = True
            session['username'] = username
            session['last_activity'] = time.time()
            session.permanent = True
            attempt_tracker[ip] = {'attempts': 0, 'lock_until': 0}
            write_log(username, ip, 'BASARILI giris')
            return redirect(url_for('index'))
        else:
            info['attempts'] += 1
            write_log(username, ip, 'BASARISIZ deneme')
            if info['attempts'] >= MAX_ATTEMPTS:
                info['lock_until'] = time.time() + LOCK_SECONDS
                info['attempts'] = 0
                attempt_tracker[ip] = info
                write_log(username, ip, 'IP KILITLENDI')
                return render_template('login.html',
                                       error='Cok fazla yanlis deneme! ' + str(LOCK_SECONDS) + ' saniye kilitlendi.')
            attempt_tracker[ip] = info
            kalan = MAX_ATTEMPTS - info['attempts']
            return render_template('login.html',
                                   error='Kullanici adi veya sifre yanlis. (' + str(kalan) + ' deneme hakkiniz kaldi)')

    return render_template('login.html', error=None)


@app.route('/logout')
def logout():
    if session.get('username'):
        write_log(session.get('username'), get_client_ip(), 'CIKIS yapildi')
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
        write_log(username, get_client_ip(), 'SIFRE degistirildi')
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
    # Port 5000 yerine 8080 kullaniliyor
    app.run(host='0.0.0.0', port=8080, debug=False)
