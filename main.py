import os
import yt_dlp
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
import uuid

app = FastAPI()

# Geçici dosyalar için güvenli klasör
TEMP_DIR = "/tmp"

def cleanup_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@app.get("/")
def home():
    return {"message": "YouTube MP3 Downloader (Render) Calisiyor."}

@app.get("/get-playlist-info")
def get_playlist_info(url: str):
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'nocheckcertificate': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'entries' not in info:
                return {"title": info.get('title'), "videos": [{"title": info.get('title'), "url": info.get('original_url')}]}

            video_list = []
            for entry in info['entries']:
                if entry:
                    video_list.append({
                        "title": entry.get('title'),
                        "url": entry.get('url'),
                    })
            
            return {"playlist_title": info.get('title'), "count": len(video_list), "videos": video_list}
            
    except Exception as e:
        return {"error": str(e)}

@app.get("/download-mp3")
def download_mp3(url: str, background_tasks: BackgroundTasks):
    file_id = str(uuid.uuid4())
    # Dosya yolunu /tmp içine ayarlıyoruz
    file_path = os.path.join(TEMP_DIR, file_id)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': file_path, # Geçici isim
        'quiet': True,
        'nocheckcertificate': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        final_filename = f"{file_path}.mp3"
        
        if not os.path.exists(final_filename):
            return {"error": "Dosya indirilemedi."}

        background_tasks.add_task(cleanup_file, final_filename)
        return FileResponse(path=final_filename, filename="music.mp3", media_type="audio/mpeg")

    except Exception as e:
        return {"error": str(e)}