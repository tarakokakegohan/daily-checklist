import streamlit as st
from datetime import date
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate

# 🚨 欠席判断の基準点数（3点以上でアウト）
THRESHOLD_SCORE = 3

# 6つのチェック項目と、それぞれの点数（配点）の設定
ITEMS = [
    {"text": "頭が回らない", "points": 2},
    {"text": "身体がだるい・重い", "points": 1},
    {"text": "帰った後洗濯できそうにない", "points": 1},
    {"text": "普段気にならないことでイライラする", "points": 1},
    {"text": "軽めの体調不良", "points": 1},  # 🟢 5項目目に移動
    {"text": "明日来れないレベルの体調不良", "points": 3}
]

# 1. メール送信用の関数
def send_gmail(date_str, score, details_text):
    # Secretsから情報の読み込み
    gmail_user = st.secrets["GMAIL_USER"]
    gmail_pass = st.secrets["GMAIL_PASS"]
    
    # メールの本文を作成
    body = f"📅 日付: {date_str}\n"
    body += f"📊 合計点数: {score} / {THRESHOLD_SCORE} 点\n"
    body += "---------------------------\n"
    body += details_text
    
    # メールオブジェクトの設定
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"【体調記録】{date_str} ({score}点)"
    msg["From"] = f"Streamlit App <{gmail_user}>"
    msg["To"] = gmail_user  # 自分宛てに送信
    msg["Date"] = formatdate(localtime=True)
    
    try:
        # GoogleのSMTPサーバーのIPアドレスを直接指定して接続
        server = smtplib.SMTP_SSL("74.125.142.108", 465)
        server.login(gmail_user, gmail_pass)
        server.send_message(msg)
        server.close()
        return True
    except Exception as e:
        st.error(f"メール送信エラー: {e}")
        return False

# アプリのタイトル
st.title("📅 毎日6項目チェック記録 (Gmail送信版)")

# 2. 入力エリア
st.header("✍️ 今日の記録")
selected_date = st.date_input("記録する日付を選択:", date.today())
date_str = selected_date.strftime("%Y-%m-%d")

# チェックボックスを表示し、点数を計算する
total_score = 0
details_list = []

for i, item in enumerate(ITEMS):
    label = f"{item['text']}  _({item['points']}点)_"
    chk = st.checkbox(label, key=f"item_{i}")
    
    if chk:
        total_score += item["points"]
        details_list.append(f"❗ {item['text']} ({item['points']}点)")

# もし1つもチェックがない場合のテキスト（念のため）
if not details_list:
    details_list.append("特になし（すべて良好）")

# 💡 リアルタイムで合計点数を表示する
st.metric(label="現在の合計点数", value=f"{total_score} / {THRESHOLD_SCORE} 点")

# 基準点数以上になったら警告を表示
if total_score >= THRESHOLD_SCORE:
    st.warning("おとなしく休もう")

st.divider()

# 3. 送信ボタン
if st.button("記録を自分のGmailに送信する", type="primary"):
    final_details = "\n".join(details_list) if details_list else "特になし（すべて良好）"
    
    with st.spinner("メールを送信中..."):
        success = send_gmail(date_str, total_score, final_details)
        
        if success:
            st.success(f"✉️ {date_str} の記録をGmailに送信しました！メールボックスを確認してください。")
            st.info(f"【送信内容】\n\n{final_details}")
