import os
import re
import time
import sqlite3
import hashlib
import secrets
from pathlib import Path
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError

PH = PasswordHasher()
DUMMY = PH.hash(secrets.token_urlsafe(32))
IDLE = 1800

def connect():
    path = Path(os.environ.get('DATASCOPE_AUTH_DB', Path(__file__).resolve().parent / 'private' / 'users.sqlite3'))
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    conn = sqlite3.connect(path, timeout=10)
    conn.execute('PRAGMA busy_timeout=10000')
    conn.executescript('''CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, password TEXT NOT NULL, theme TEXT NOT NULL DEFAULT 'Light');
    CREATE TABLE IF NOT EXISTS attempts(bucket TEXT PRIMARY KEY, count INTEGER NOT NULL, until REAL NOT NULL);''')
    try: path.chmod(0o600)
    except OSError: pass
    return conn

def create_user(username, password, reset=False):
    username = username.strip().lower()
    if not re.fullmatch(r'[a-z0-9_.-]{3,64}', username): raise ValueError('Identifiant : 3–64 caractères, lettres minuscules, chiffres, _ . -')
    if len(password) < 12 or len(password) > 256: raise ValueError('Mot de passe : 12–256 caractères.')
    with connect() as con:
        if reset:
            if not con.execute('SELECT 1 FROM users WHERE username=?',(username,)).fetchone(): raise ValueError('Compte introuvable.')
            con.execute('UPDATE users SET password=? WHERE username=?',(PH.hash(password),username))
            con.execute('DELETE FROM attempts WHERE bucket=?',(hashlib.sha256(username.encode()).hexdigest(),))
        else: con.execute('INSERT INTO users(username,password) VALUES (?,?)',(username, PH.hash(password)))

def authenticate(username, password):
    username = username.strip().lower()[:64]
    bucket = hashlib.sha256(username.encode()).hexdigest(); now = time.time()
    with connect() as con:
        con.execute('BEGIN IMMEDIATE')
        con.execute('DELETE FROM attempts WHERE until < ?', (now,))
        attempt = con.execute('SELECT count,until FROM attempts WHERE bucket=?',(bucket,)).fetchone()
        if attempt and attempt[0] >= 5: return None
        # Réserver la tentative avant le calcul du hash pour limiter les connexions concurrentes.
        con.execute('INSERT INTO attempts VALUES (?,1,?) ON CONFLICT(bucket) DO UPDATE SET count=count+1',(bucket,now+900))
        row = con.execute('SELECT password,theme FROM users WHERE username=?',(username,)).fetchone()
    valid = False
    try:
        if len(password) <= 256: valid = PH.verify(row[0] if row else DUMMY, password)
    except (VerificationError, InvalidHashError): pass
    if row and valid:
        with connect() as con:
            con.execute('DELETE FROM attempts WHERE bucket=?',(bucket,))
            if PH.check_needs_rehash(row[0]): con.execute('UPDATE users SET password=? WHERE username=?',(PH.hash(password),username))
        return {'username':username,'theme':row[1]}
    return None

def set_theme(username, theme):
    if theme not in ['Light','Dark']: raise ValueError('Thème invalide.')
    with connect() as con: con.execute('UPDATE users SET theme=? WHERE username=?',(theme,username))

def clear_session(st):
    for key in list(st.session_state): del st.session_state[key]

def login_gate(st):
    now = time.time()
    if st.session_state.get('auth_user') and now - st.session_state.get('auth_last_seen', 0) < IDLE:
        st.session_state.auth_last_seen = now
        return st.session_state.auth_user
    if st.session_state.get('auth_user'): clear_session(st)
    st.markdown('## 🔐 Bienvenue dans DataScope Studio')
    st.caption('Connectez-vous pour accéder à votre espace analytique.')
    with st.form('login_form', clear_on_submit=True):
        username = st.text_input('Identifiant', max_chars=64)
        password = st.text_input('Mot de passe', type='password', max_chars=256)
        submit = st.form_submit_button('Se connecter', type='primary')
    if submit:
        user = authenticate(username, password)
        if user:
            clear_session(st)
            st.session_state.auth_user = user['username']
            st.session_state.auth_last_seen = now
            st.session_state.display_theme = user['theme']
            st.rerun()
        st.error('Connexion refusée. Vérifiez vos identifiants ou réessayez après 15 minutes si trop de tentatives ont été effectuées.')
    st.info('Pas de compte par défaut. L’administrateur doit créer votre compte depuis le terminal.')
    st.stop()
