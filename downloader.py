import yt_dlp
import os

def download_song(url, custom_name=None):
    # Ensure songs directory exists
    if not os.path.exists('songs'):
        os.makedirs('songs')

    # Logic to determine file name
    if custom_name:
        # Use custom name, keeping %(ext)s for safety during download
        # The postprocessor will force it to .wav at the end
        out_tmpl = f"songs/{custom_name}.%(ext)s"
    else:
        # Use original video title
        out_tmpl = 'songs/%(title)s.%(ext)s'

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': out_tmpl,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
    }

    print(f"Downloading: {url}...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"\nDownload Complete! Saved to 'songs/' folder.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    link = input("Paste YouTube Link: ")
    name = input("Enter custom file name (or Press Enter for original title): ").strip()
    
    # Pass the name only if the user actually typed something
    download_song(link, name if name else None)