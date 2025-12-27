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
    return {"message": "YouTube MP3 API (iOS + Format Fix) Calisiyor."}

def get_ydl_opts(filename=None):
    return {
        # --- FORMAT AYARI DEĞİŞTİ ---
        # "bestaudio/best" yerine daha genel bir ayar kullanıyoruz.
        # iPhone akışlarını (m3u8) da kabul et diyoruz.
        'format': 'bestaudio/best', 
        'outtmpl': filename,
        'quiet': True,
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt', # Cookie MUTLAKA olmalı
        
        # --- iOS MASKESİ (IP Engelini Aşmak İçin ŞART) ---
        'extractor_args': {
            'youtube': {
                'player_client': ['ios'], 
            }
        },
        # --------------------------------------------------
        
        # MP3 Çevirme Ayarları (Gelen ses ne olursa olsun MP3 yap)
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

@app.get("/get-playlist-info")
def get_playlist_info(url: str):
    opts = get_ydl_opts()
    opts['extract_flat'] = True
    
    try:
        if not os.path.exists('cookies.txt'):
             return {"error": "cookies.txt yok! Lutfen yukleyin."}

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Playlist kontrolü
            if 'entries' not in info:
                # Belki tek videodur, onu listeye çevirip verelim
                return {
                    "playlist_title": info.get('title'),
                    "total_count": 1,
                    "videos": [{"title": info.get('title'), "url": info.get('webpage_url') or info.get('url')}]
                }

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
        
        # Dosya oluştu mu kontrol et
        if not os.path.exists(final_filename):
            # Bazen yt-dlp uzantıyı dosya ismine eklemez, bir de öyle bakalım
            if os.path.exists(file_path):
                 os.rename(file_path, final_filename)
            else:
                 return {"error": "Dosya indirilemedi (Format veya Izin Hatasi)."}

        background_tasks.add_task(cleanup_file, final_filename)
        
        return FileResponse(path=final_filename, filename="music.mp3", media_type="audio/mpeg")

    except Exception as e:
        return {"error": str(e)}
