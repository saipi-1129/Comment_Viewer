import os
import pymysql
import pymysql.cursors # この行を追加！
from flask import Flask, render_template, request

# --- Flaskアプリケーションの初期化 ---
app = Flask(__name__)

# --- データベース接続情報 ---
# 接続に成功した情報なので、このままでOK
DB_HOST = 
DB_DATABASE = 
DB_USER = 
DB_PASSWORD = 
DB_PORT = 3306

def get_db_connection():
    """データベース接続を取得します（PyMySQL版）"""
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE,
            port=DB_PORT,
            # 結果を辞書形式で扱うための設定
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4' # ← この行を追加！

        )
        return conn
    except pymysql.Error as e:
        print(f"データベース接続に失敗しました: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    """コメント一覧表示と検索処理"""
    conn = get_db_connection()
    if not conn:
        return "データベースに接続できませんでした。", 500
    
    # withを使うと、自動でcursor.close()とconn.close()をしてくれるので安全です
    with conn:
        with conn.cursor() as cursor:
            # --- 絞り込み用のユーザー一覧を取得 ---
            cursor.execute("SELECT DISTINCT name FROM comments ORDER BY name")
            # DictCursorのおかげで row['name'] のようにアクセスできます
            users = [row['name'] for row in cursor.fetchall()]

            # --- 検索条件の処理 ---
            search_params = {
                'start_date': request.form.get('start_date', ''),
                'end_date': request.form.get('end_date', ''),
                'user_name': request.form.get('user_name', '')
            }

            # --- SQLクエリの組み立て ---
            sql_query = "SELECT `time`, `name`, `comment` FROM comments WHERE 1=1"
            params = []

            if search_params['start_date']:
                sql_query += " AND `time` >= %s"
                params.append(search_params['start_date'])

            if search_params['end_date']:
                sql_query += " AND `time` <= %s"
                params.append(f"{search_params['end_date']} 23:59:59")

            if search_params['user_name']:
                sql_query += " AND `name` = %s"
                params.append(search_params['user_name'])

            sql_query += " ORDER BY `time` DESC" # ←★このように変更


            cursor.execute(sql_query, tuple(params))
            comments = cursor.fetchall()

            print("------------------------------------")
            print(f"取得したコメント数: {len(comments)} 件")
            if comments: # もしデータが1件でもあれば
                print("最初のコメントのデータ内容:")
                # 取得したデータの最初の1行を表示します
                print(comments[0])
                # timeカラムのデータ型を表示します
                print(f"timeのデータ型: {type(comments[0]['time'])}")
            print("------------------------------------")
            

    return render_template('index.html',
                           comments=comments,
                           users=users,
                           search_params=search_params)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
