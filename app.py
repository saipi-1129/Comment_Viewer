import os
import pymysql
import pymysql.cursors
from flask import Flask, render_template, request, session, redirect, url_for, flash

app = Flask(__name__)

# --- アプリケーション設定 (重要！) ---
# 1. セッションを暗号化するための秘密鍵。必ず複雑な文字列に変更してください。
# この行がないと「Internal Server Error」になります。
app.config['SECRET_KEY'] = 'your-very-secret-and-complex-key-change-me'

# 2. ログインパスワードを設定
APP_PASSWORD = 'password' # ← ここに好きなパスワードを設定してください

# --- データベース接続情報 --
DB_HOST = 
DB_DATABASE = 
DB_USER = 
DB_PASSWORD =
DB_PORT = 3306

def get_db_connection():
    """データベース接続を取得します"""
    try:
        conn = pymysql.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_DATABASE,
            port=DB_PORT, cursorclass=pymysql.cursors.DictCursor, charset='utf8mb4'
        )
        return conn
    except pymysql.Error as e:
        print(f"データベース接続に失敗しました: {e}")
        return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    """ログインページの表示と認証処理"""
    if request.method == 'POST':
        if request.form.get('password') == APP_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('パスワードが違います', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """ログアウト処理"""
    session.pop('logged_in', None)
    flash('ログアウトしました', 'info')
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    """メインのコメントビューアページ"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    if not conn:
        flash("データベースに接続できませんでした。", "danger")
        return render_template('index.html', comments=[], users=[], search_params={})
    
    comments, users = [], []
    search_params = {}
    
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT name FROM comments WHERE name IS NOT NULL AND name != '' ORDER BY name")
            users = [row['name'] for row in cursor.fetchall()]

            search_params = {
                'start_date': request.form.get('start_date', ''),
                'end_date': request.form.get('end_date', ''),
                'user_name': request.form.get('user_name', ''),
                'keyword': request.form.get('keyword', '')
            }

            sql_query = "SELECT `time`, `name`, `comment` FROM comments WHERE 1=1"
            params = []

            if search_params['start_date']:
                sql_query += " AND `time` >= %s"; params.append(search_params['start_date'])
            if search_params['end_date']:
                sql_query += " AND `time` <= %s"; params.append(f"{search_params['end_date']} 23:59:59")
            if search_params['user_name']:
                sql_query += " AND `name` = %s"; params.append(search_params['user_name'])
            if search_params['keyword']:
                sql_query += " AND `comment` LIKE %s"; params.append(f"%{search_params['keyword']}%")

            sql_query += " ORDER BY `time` DESC LIMIT 100"
            cursor.execute(sql_query, tuple(params))
            comments = cursor.fetchall()

    return render_template('index.html',
                           comments=comments, users=users, search_params=search_params)

# systemdで起動する場合は、以下のブロックは不要です
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)
