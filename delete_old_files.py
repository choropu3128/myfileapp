import os, sqlite3
from datetime import datetime

DB = "files.db"
conn = sqlite3.connect(DB)
expired = conn.execute("SELECT id, path FROM files WHERE expires_at < ?", (datetime.now().isoformat(),)).fetchall()

for file_id, path in expired:
    if os.path.exists(path):
        os.remove(path)
    qr_path = f"qrcodes/{file_id}.png"
    if os.path.exists(qr_path):
        os.remove(qr_path)
    print(f"削除: {file_id}")
    conn.execute("DELETE FROM files WHERE id = ?", (file_id,))

conn.commit()
conn.close()
