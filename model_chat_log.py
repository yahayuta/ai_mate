from google.cloud import bigquery

# save chat log
def save_log(role, msg):
    client = bigquery.Client()
    query_job = client.query(f'INSERT INTO app.chat_log(user_id,message,role,created) values(\'mate\',\'\'\'{msg}\'\'\',\'{role}\',CURRENT_DATETIME(\'Asia/Tokyo\'))')
    print(query_job)
    
# load chat logs
def get_logs():
    client = bigquery.Client()
    query_job = client.query("SELECT * FROM app.chat_log WHERE user_id = 'mate' order by created")
    rows = query_job.result()
    print(rows.total_rows)
    logs = []
    for row in rows:
        log = {"role": row["role"], "content": row["message"]}
        logs.append(log)
    return logs

# delete chat logs
def delete_logs():
    client = bigquery.Client()
    query_job = client.query("DELETE FROM app.chat_log WHERE user_id = 'mate'")
    print(query_job)
