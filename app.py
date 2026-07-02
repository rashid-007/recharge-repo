from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import os
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from email_validator import validate_email, EmailNotValidError

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'recharge_secret_key')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

bcrypt = Bcrypt(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

def get_db_connection():
    conn = mysql.connector.connect(
        host=os.environ.get('MYSQL_HOST', 'mysql-service'),
        port=int(os.environ.get('MYSQL_PORT', 3306)),
        database=os.environ.get('MYSQL_DATABASE', 'recharge_db'),
        user=os.environ.get('MYSQL_USER', 'recharge_user'),
        password=os.environ.get('MYSQL_PASSWORD', 'rechargepass')
    )
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SET FOREIGN_KEY_CHECKS=0')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            phone VARCHAR(15) NOT NULL,
            balance DECIMAL(10,2) DEFAULT 0.00,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            phone VARCHAR(15) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            operator VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'Success',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('SET FOREIGN_KEY_CHECKS=1')

    conn.commit()
    cursor.close()
    conn.close()

def validate_phone(phone):
    phone = phone.strip()
    if not phone.isdigit():
        return False
    if len(phone) < 10 or len(phone) > 15:
        return False
    return True

def validate_password(password):
    if len(password) < 8:
        return False, 'Password must be at least 8 characters'
    if not any(c.isupper() for c in password):
        return False, 'Password must contain at least one uppercase letter'
    if not any(c.isdigit() for c in password):
        return False, 'Password must contain at least one number'
    return True, ''

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please fill in all fields!', 'error')
            return render_template('login.html')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s AND is_active = TRUE',
                      (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['phone'] = user['phone']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()

        if not username or not email or not password or not phone:
            flash('Please fill in all fields!', 'error')
            return render_template('register.html')

        if len(username) < 3 or len(username) > 50:
            flash('Username must be between 3 and 50 characters!', 'error')
            return render_template('register.html')

        try:
            validate_email(email)
        except EmailNotValidError:
            flash('Invalid email address!', 'error')
            return render_template('register.html')

        is_valid, msg = validate_password(password)
        if not is_valid:
            flash(msg, 'error')
            return render_template('register.html')

        if not validate_phone(phone):
            flash('Invalid phone number!', 'error')
            return render_template('register.html')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, email, password, phone, balance) VALUES (%s, %s, %s, %s, %s)',
                          (username, email, hashed_password, phone, 1000.00))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Registration successful! You get Rs. 1000 welcome bonus!', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Username or email already exists!', 'error')

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
    user = cursor.fetchone()

    cursor.execute('SELECT * FROM transactions WHERE user_id = %s ORDER BY created_at DESC LIMIT 5',
                  (session['user_id'],))
    transactions = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('dashboard.html', user=user, transactions=transactions)

@app.route('/recharge', methods=['GET', 'POST'])
def recharge():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        amount = request.form.get('amount', '')
        operator = request.form.get('operator', '').strip()

        if not phone or not amount or not operator:
            flash('Please fill in all fields!', 'error')
            return render_template('recharge.html')

        if not validate_phone(phone):
            flash('Invalid phone number!', 'error')
            return render_template('recharge.html')

        try:
            amount = float(amount)
            if amount <= 0:
                flash('Amount must be greater than 0!', 'error')
                return render_template('recharge.html')
        except ValueError:
            flash('Invalid amount!', 'error')
            return render_template('recharge.html')

        valid_operators = ['Jazz', 'Telenor', 'Zong', 'Ufone', 'SCO']
        if operator not in valid_operators:
            flash('Invalid operator!', 'error')
            return render_template('recharge.html')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT balance FROM users WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()

        if user['balance'] >= amount:
            cursor.execute('UPDATE users SET balance = balance - %s WHERE id = %s',
                          (amount, session['user_id']))
            cursor.execute('INSERT INTO transactions (user_id, phone, amount, operator) VALUES (%s, %s, %s, %s)',
                          (session['user_id'], phone, amount, operator))
            conn.commit()
            flash(f'Recharge of Rs. {amount} for {phone} successful!', 'success')
        else:
            flash('Insufficient balance!', 'error')

        cursor.close()
        conn.close()
        return redirect(url_for('dashboard'))

    return render_template('recharge.html')

@app.route('/transactions')
def transactions():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM transactions WHERE user_id = %s ORDER BY created_at DESC',
                  (session['user_id'],))
    transactions = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('transactions.html', transactions=transactions)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)


































