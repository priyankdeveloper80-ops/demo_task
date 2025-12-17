import os
import whisper
import yt_dlp
import tempfile

def extract_transcript(video_source):
    if video_source.startswith('http'):
        return extract_from_youtube(video_source)
    else:
        return extract_from_file(video_source)

def extract_from_youtube(url):
    try:
        print(f"Processing YouTube URL: {url}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Configure yt-dlp options based on your working example
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': f'{temp_dir}/%(title)s.%(ext)s',
                # Use specific client to bypass "Precondition check failed"
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web']
                    }
                },
                'verbose': False,  # Set to True for debugging
                'quiet': True,     # Reduce output noise
            }
            
            print(f"Attempting download to: {temp_dir}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to get video details
                info = ydl.extract_info(url, download=False)
                video_title = info.get('title', 'Unknown')
                video_duration = info.get('duration', 0)
                
                print(f"Video title: {video_title}")
                print(f"Video duration: {video_duration} seconds")
                
                # Download the video
                ydl.download([url])
            
            # Find the downloaded file
            downloaded_files = [f for f in os.listdir(temp_dir) if f.endswith(('.mp4', '.webm', '.mkv'))]
            if not downloaded_files:
                raise ValueError("No video file was downloaded")
            
            downloaded_file = os.path.join(temp_dir, downloaded_files[0])
            print(f"Downloaded file: {downloaded_file}")
            
            # Extract transcript from downloaded file
            transcript = extract_from_file(downloaded_file)
            print("Transcript extraction completed")
            
            # Add video title to transcript result
            transcript['title'] = video_title
            
            return transcript
                
    except Exception as e:
        print(f"YouTube extraction error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Run 'pip install --upgrade yt-dlp'")
        print("2. Check if the video is available in your region")
        print("3. Try a different YouTube URL")
        raise Exception(f"YouTube extraction failed: {str(e)}")

def extract_from_file(file_path):
    try:
        print(f"Loading Whisper model...")
        model = whisper.load_model("base")
        
        print(f"Transcribing audio from: {file_path}")
        result = model.transcribe(file_path)
        
        transcript_text = result["text"]
        segments = []
        
        for segment in result.get("segments", []):
            segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"]
            })
        
        print(f"Transcription completed. Text length: {len(transcript_text)} characters")
        
        return {
            "text": transcript_text,
            "segments": segments,
            "title": None  # Will be set by extract_from_youtube if available
        }
    except Exception as e:
        print(f"Transcription error: {str(e)}")
        raise Exception(f"Transcription failed: {str(e)}")
