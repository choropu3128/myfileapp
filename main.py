from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from uuid import uuid4
from datetime import datetime, timedelta
import os, shutil, qrcode, sqlite3

app = FastAPI()

UPLOAD_DIR = "uploads"
QRCODE_DIR = "qrcodes"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(QRCODE_DIR, exist_ok=True)

DB = "files.db"
conn = sqlite3.connect(DB)
conn.execute("""
CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    filename TEXT,
    path TEXT,
    expires_at TEXT
)
""")
conn.commit()

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    file_id = str(uuid4())
    filename = file.filename
    filepath = os.path.join(UPLOAD_DIR, f"{file_id}_{filename}")
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    expires_at = datetime.now() + timedelta(days=1)
    conn.execute("INSERT INTO files VALUES (?, ?, ?, ?)",
                 (file_id, filename, filepath, expires_at.isoformat()))
    conn.commit()

    download_url = f"https://yourdomain.com/download/{file_id}"
    qr = qrcode.make(download_url)
    qr_path = os.path.join(QRCODE_DIR, f"{file_id}.png")
    qr.save(qr_path)

    return HTMLResponse(f"""
        <h2>アップロード成功！</h2>
        <p>ダウンロードURL: <a href="{download_url}">{download_url}</a></p>
        <img src="/qr/{file_id}" alt="QRコード" />
    """)

@app.get("/download/{file_id}")
def download(file_id: str):
    result = conn.execute("SELECT path, filename, expires_at FROM files WHERE id = ?", (file_id,)).fetchone()
    if not result:
        return HTMLResponse("ファイルが見つかりません", status_code=404)
    path, filename, expires_at = result
    if datetime.fromisoformat(expires_at) < datetime.now():
        return HTMLResponse("ファイルの有効期限が切れています", status_code=410)
    return FileResponse(path, filename=filename)

@app.get("/qr/{file_id}")
def get_qr(file_id: str):
    qr_path = os.path.join(QRCODE_DIR, f"{file_id}.png")
    if os.path.exists(qr_path):
        return FileResponse(qr_path, media_type="image/png")
    return HTMLResponse("QRコードが見つかりません", status_code=404)
