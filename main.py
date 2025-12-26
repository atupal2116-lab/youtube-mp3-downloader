import os
import yt_dlp
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
import uuid

app = FastAPI()
TEMP_DIR = "/tmp"

def cleanup_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@app.get("/")
def home():
    return {"message": "YouTube MP3 API (iOS Mode) Calisiyor."}

def get_ydl_opts(filename=None):
    return {
        'format': 'bestaudio/best',
        'outtmpl': filename,
        'quiet': True,
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt',
        # --- KRİTİK DEĞİŞİKLİK: iOS MASKESİ ---
        # YouTube şu an Android ve Web istemcilerini veri merkezlerinden engelliyor.
        # iOS (iPhone) istemcisi hala çalışıyor.
        'extractor_args': {
            'youtube': {
                'player_client': ['ios'], 
            }
        },
        # ------------------------------------------
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

@app.get("/get-playlist-info")
def get_playlist_info(url: str):
    # Playlist için de iOS taklidi
    opts = get_ydl_opts()
    opts['extract_flat'] = True
    
    try:
        if not os.path.exists('cookies.txt'):
             return {"error": "cookies.txt yok! GitHub'a yukle."}

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'entries' not in info:
                return {"error": "Playlist bulunamadi."}

            video_list = []
            for entry in info['entries']:
                if entry:
                    video_list.append({
                        "title": entry.get('title'),
                        "url": entry.get('url'),
                        "id": entry.get('id')
                    })
            
            return {
                "playlist_title": info.get('title'), 
                "total_count": len(video_list), 
                "videos": video_list
            }
            
    except Exception as e:
        return {"error": str(e)}

@app.get("/download-mp3")
def download_mp3(url: str, background_tasks: BackgroundTasks):
    file_id = str(uuid.uuid4())
    file_path = os.path.join(TEMP_DIR, file_id)
    
    opts = get_ydl_opts(file_path)

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
            
        final_filename = f"{file_path}.mp3"
        
        if not os.path.exists(final_filename):
            return {"error": "Dosya indirilemedi. (iOS modu da engellendi)"}

        background_tasks.add_task(cleanup_file, final_filename)
        
        return FileResponse(path=final_filename, filename="music.mp3", media_type="audio/mpeg")

    except Exception as e:
        return {"error": str(e)}
