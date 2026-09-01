import streamlit as st
import sqlite3
from datetime import date
import pandas as pd

# 1. データベースの初期設定（scoreカラムを追加）
DB_FILE = "daily_checklist.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checklist (
            date TEXT PRIMARY KEY,
            item1 INTEGER,
            item2 INTEGER,
            item3 INTEGER,
            item4 INTEGER,
            item5 INTEGER,
            score INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# アプリのタイトル
st.title("📅 毎日5項目チェック記録")

# 5つのチェック項目と、それぞれの点数（配点）の設定
ITEMS = [
    {"text": "頭が回らない", "points": 2},
    {"text": "身体がだるい・重い", "points": 1},
    {"text": "帰った後洗濯できそうにない", "points": 1},
    {"text": "普段気にならないことでイライラする", "points": 1},
    {"text": "明日来れないレベルの体調不良", "points": 3}
]

# 2. 入力エリア
st.header("✍️ 今日の記録")
selected_date = st.date_input("記録する日付を選択:", date.today())
date_str = selected_date.strftime("%Y-%m-%d")

# 既存のデータがあれば読み込む
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
try:
    cursor.execute("SELECT item1, item2, item3, item4, item5 FROM checklist WHERE date = ?", (date_str,))
    existing_row = cursor.fetchone()
except sqlite3.OperationalError:
    # 古いデータベース構造のままの場合エラーになるため、一度テーブルを作り直す
    cursor.execute("DROP TABLE IF EXISTS checklist")
    conn.commit()
    conn.close()
    st.warning("⚠️ データベースの形が変わったため、一度データをリセットしました。画面を再読み込みしてください。")
    st.stop()
conn.close()

# 初期値の設定
defaults = [False] * 5
if existing_row:
    defaults = [bool(val) for val in existing_row]

# 5つのチェックボックスを表示し、点数を計算する
total_score = 0
checks = []

for i, item in enumerate(ITEMS):
    # ラベルに点数を分かりやすく表示 (例: 朝7時までに起きた [2点])
    label = f"{item['text']}  _({item['points']}点)_"
    chk = st.checkbox(label, value=defaults[i], key=f"item_{i}")
    
    if chk:
        total_score += item["points"]
        checks.append(1)
    else:
        checks.append(0)

# 💡 リアルタイムで合計点数を表示する
st.metric(label="現在の合計点数", value=f"{total_score} / 10 点")

if total_score >= 3:
    st.warning("おとなしく休もう")

# 保存ボタン
if st.button("記録を保存する", type="primary"):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO checklist (date, item1, item2, item3, item4, item5, score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            item1=excluded.item1,
            item2=excluded.item2,
            item3=excluded.item3,
            item4=excluded.item4,
            item5=excluded.item5,
            score=excluded.score
    ''', (date_str, *checks, total_score))
    conn.commit()
    conn.close()
    st.success(f"{date_str} の記録（{total_score}点）を保存しました！")
    st.rerun()

st.divider()

# 3. 履歴の表示エリア
st.header("📊 過去の記録一覧")

conn = sqlite3.connect(DB_FILE)
# 最新の日付が一番上に来るように並び替え
df = pd.read_sql_query("SELECT * FROM checklist ORDER BY date DESC", conn)
conn.close()

if not df.empty:
    # 1日ずつループして箇条書きを作成
    for _, row in df.iterrows():
        # 日付と合計点数を太字の見出しにする
        st.markdown(f"#### 📅 {row['date']}  _({row['score']}点)_")
        
        # 5つの項目を縦の箇条書きで表示
        # 1なら⭕、0なら❌
        st.write(f"- {'⭕' if row['item1'] else '❌'} {ITEMS[0]['text']}")
        st.write(f"- {'⭕' if row['item2'] else '❌'} {ITEMS[1]['text']}")
        st.write(f"- {'⭕' if row['item3'] else '❌'} {ITEMS[2]['text']}")
        st.write(f"- {'⭕' if row['item4'] else '❌'} {ITEMS[3]['text']}")
        st.write(f"- {'⭕' if row['item5'] else '❌'} {ITEMS[4]['text']}")
        
        # 日付ごとの区切り線
        st.divider()
else:
    st.info("まだ記録がありません。上のボタンから最初の記録を追加してください。")

