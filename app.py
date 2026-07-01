from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import os
from datetime import datetime
app=Flask(__name__)
app.secret_key='recharge_secret_key'
def get_db_connection():
    conn = mysql.connector.connect(
        host=os.environ.get('MYSQL_HOST', 'mysql-service'),
        port=int(os.environ.get('MYSQL_PORT', 3306)),
        database=os.environ.get('MYSQL_DATABASE', 'recharge_db'),
        user=os.environ.get('MYSQL_USER', 'recharge_user'),
        password=os.environ.get('MYSQL_PASSWORD', 'rehargepass')
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
            password VARCHAR(50) NOT NULL,
            phone VARCHAR(15) NOT NULL,
            balance DECIMAL(10,2) DEFAULT 0.00,
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
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        conn=get_db_connection()
        cursor=conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        user=cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            session['user_id']=user['id']
            session['username']=user['username']
            session['phone']=user['phone']
            flash('login successful!','success')
            return redirect(url_for('dashboard'))

        else:
            flash('invalid username or password!', 'error')

    return render_template('login.html')
    return render_template('register.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        phone = request.form['phone']
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password, phone, balance) VALUES (%s, %s, %s, %s)',
                          (username, password, phone, 1000.00))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Registration successful! You get Rs. 1000 welcome bonus!', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Username already exists!', 'error')
    return render_template('register.html')
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn=get_db_connection()
    cursor=conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
    user=cursor.fetchone()
    cursor.execute('SELECT * FROM transactions WHERE user_id = %s ORDER BY created_at DESC LIMIT 5', (session['user_id'],))
    transactions=cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('dashboard.html', user=user, transactions=transactions)
@app.route('/recharge', methods=['GET', 'POST'])
def recharge():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method=='POST':
        phone=request.form['phone']
        amount=float(request.form['amount'])
        operator= request.form['operator']
        conn=get_db_connection()
        cursor=conn.cursor(dictionary=True)
        cursor.execute('SELECT balance FROM users WHERE id = %s', (session['user_id'],))
        user=cursor.fetchone()
        if user['balance']>=amount:
            cursor.execute('UPDATE users SET balance=balance - %s WHERE id=%s', (amount, session['user_id']))
            cursor.execute('INSERT INTO transactions (user_id, phone, amount, operator) VALUES (%s, %s, %s, %s)', (session['user_id'], phone, amount, operator))
            conn.commit()
            flash(f'recharge of Rs {amount} for {phone} successful!', 'success')
        else:
            flash('Insufficient Balance!', 'error')
        cursor.close()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('recharge.html')
@app.route('/transactions')
def transactions():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn=get_db_connection()
    cursor=conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM transactions WHERE user_id=%s ORDER BY created_at DESC', (session['user_id'],))
    transactions=cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('transactions.html', transactions=transactions)
@app.route('/logout')
def logout():
    session.clear()
    flash('logged out successfully!', 'success')
    return redirect(url_for('login'))
if __name__=='__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)


























































