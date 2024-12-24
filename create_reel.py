import google.generativeai as genai
import requests
import json
from datetime import datetime, timedelta
import os
import re
import logging
from moviepy.editor import *
from gtts import gTTS
import asyncio
from crawl4ai import AsyncWebCrawler

async def scrap(url_):
    async with AsyncWebCrawler(verbose=True,headless=False) as crawler:
        result = await crawler.arun(url=url_)
        return result.markdown
        #print(f"Basic crawl result: {result.markdown[:500]}")  # Print first 500 characters

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


pexels_api_key = "YOUR PEXELS API KEY"  # Replace
genai.configure(api_key='YOUR GEMINI API KEY')  # Replace with your Gemini API key


news_api_key = "YOUR NEWS API KEY"  # Replace with your News API key

# --- Gemini AI Configuration ---
safety_settings = {
    "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
}
generation_config = {
    "temperature": 0.8,  # Slightly reduced temperature for more focused summaries
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 4096, # Reduced token limit
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    safety_settings=safety_settings
)


# --- Functions ---

# ... (Previous functions for news fetching, Jina interaction, JSON parsing, sanitizing filenames remain the same)
def get_tech_news(api_key, days=1):
    url = "https://newsapi.org/v2/top-headlines"
    date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    params = {
        'apiKey': api_key,
        'category': 'technology',
        'language': 'en',
        'from': date,
        'pageSize': 100
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data['articles']:
            processed_articles = [
                {
                    'title': article['title'],
                    'description': article['description'],
                    'url': article['url'],
                    'source': article['source']['name'],
                    'published_at': article['publishedAt']
                }
                for article in data['articles']
            ]

            return {
                'status': 'success',
                'total_results': len(processed_articles),
                'articles': processed_articles
            }
    
        else:
            return {
                'status': 'success',
                'total_results': 0,
                'articles': []
            }

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching news: {str(e)}")
        return {'status': 'error', 'message': str(e)}

    
def get_top(text):
    try:
        prompt = f"From the given list of articles, choose top 5 tech articles that can catch the attention of the readers. {text} give output the index of the top 10 articles as a JSON array."
        response = model.generate_content(prompt)
        return get_json(response.text)
    except Exception as e:
        logging.error(f"Error getting top articles: {str(e)}")
        return []
    
def detail_prompt(title, text):
    prompt = f"""
    You are a journalist writing concise tech news for Instagram. Summarize the article titled "{title}" in 2-3 short paragraphs.
    Here are the details extracted from the link: {text}
    Return in JSON format:
    {{
        "title": "Title of the article",
        "summary": ["para 1", "para 2", "para 3"],
        "image": "Image link",
        "caption": "caption for the instagram post use hashtags too "
    }}
    """
    return prompt

def get_json(text):
    try:
        text = text.split("```")[1].replace("json","")
        return json.loads(text)
    except Exception as e:
        logging.error(f"Error parsing JSON: {str(e)}")
        return None

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def reel_prompt(title, text):
    prompt = f"""
    Create a concise and engaging script for a short Instagram Reels video using the tech article: "{title}".
    Article details: {text}

    scripts will narrated as it is in the video
    keywords will be used to find the stock videos from pexels. 
    Output JSON:
    {{
        "title": "Title of the article (suitable for Reels)",
        "script": ["Scene 1 text", "Scene 2 text", "Scene 3 text"],  
        "keywords": ["keyword1", "keyword2", "keyword3"] // For video search
    }}
    """
    return prompt

def download_pexels_videos(query,base_path, api_key, num_videos=3): # Downloads fewer videos by default
    headers = {"Authorization": api_key}
    params = {"query": query, "orientation": "portrait", "per_page": min(num_videos, 80)}
    url = "https://api.pexels.com/videos/search"

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

    data = response.json()
    videos = data.get("videos", [])

    downloaded_videos = []
    for i, video in enumerate(videos):
        if i >= num_videos:
            break

        video_files = video.get("video_files", [])
        best_quality = sorted(video_files, key=lambda x: x.get("width", 0), reverse=True)
        if best_quality:
            download_url = best_quality[0]["link"]
            try:
                video_response = requests.get(download_url, stream=True)
                video_response.raise_for_status()

                file_extension = os.path.splitext(download_url)[1] or ".mp4"
                file_name =  f"{query}_{video.get('id')}{file_extension}"
                file_name = os.path.join(base_path, file_name)

                with open(file_name, 'wb') as f:
                    for chunk in video_response.iter_content(chunk_size=8192):
                        f.write(chunk)

                print(f"Downloaded: {file_name}")
                downloaded_videos.append(file_name)

            except Exception as e:
                print(f"Error downloading video: {e}")
    return downloaded_videos


def create_reel(content, base_folder, save_reel_path, audio_path):
    clips = []
    width, height = 480, 854 # Portrait aspect ratio for better quality
    subtitle_height_fraction = 0.50 # Position subtitles near the bottom
    subtitle_font_size = int(height * 0.05) # Reduced font size
    subtitle_line_spacing = 2  # Reduced line spacing
    subtitle_color = 'white'
    subtitle_bg_color = 'black'
    subtitle_bg_opacity = 0.6

    downloaded_videos = download_pexels_videos(', '.join(content['keywords']), base_folder, pexels_api_key)
    if not downloaded_videos:
        print("No videos downloaded. Exiting.")
        return

    # Ensure we have enough video clips, loop if necessary
    video_clips = []
    for i in range(len(content['script'])):
        video_path = downloaded_videos[i % len(downloaded_videos)]
        try:
            clip = VideoFileClip(video_path).resize(height=height) # Resize based on height, maintain aspect ratio
            # Crop to desired width if necessary, centering the video
            if clip.w > width:
                margin = (clip.w - width) // 2
                clip = clip.crop(x1=margin, y1=0, x2=clip.w - margin, y2=height)
            elif clip.w < width:
                # Add black bars if the video is narrower
                w_diff = width - clip.w
                x_padding = w_diff // 2
                clip = clip.margin(left=x_padding, right=x_padding, color=(0, 0, 0))
            video_clips.append(clip)
        except Exception as e:
            print(f"Error processing video {video_path}: {e}")
            return

    audio = AudioFileClip(audio_path)
    # Adjust video clip durations to match audio duration
    total_audio_duration = audio.duration
    clip_duration = total_audio_duration / len(content['script'])

    for i, text in enumerate(content['script']):
        clip = video_clips[i]
        clip = clip.subclip(0, min(clip_duration, clip.duration)) # Ensure clip doesn't exceed its length

        # Create text clip with improved formatting
        txt_clip = (TextClip(text,
                             fontsize=subtitle_font_size,
                             color=subtitle_color,
                             font="Arial-Bold",
                             stroke_color='black',
                             stroke_width=4,
                             method='caption',
                             align='center')
                    .set_position(('center', height * (1 - subtitle_height_fraction))) # Position near the bottom, adjust as needed
                    .set_duration(clip_duration))

        final_clip = CompositeVideoClip([clip, txt_clip])
        clips.append(final_clip)

    final_reel = concatenate_videoclips(clips, method="compose", bg_color=(0,0,0)) # Added background color for safety
    final_reel = final_reel.set_audio(audio)
    reel_path = os.path.join(save_reel_path, f"{sanitize_filename(content['title'])}.mp4")
    final_reel.write_videofile(reel_path, codec='libx264', fps=30, preset="ultrafast", threads=8, audio_codec="aac") # Increased FPS for smoother video

    print(f"Reel saved to: {reel_path}")




async def process_news_for_reel(base_path):
    os.makedirs(base_path, exist_ok=True)
    print("-" * 30)
    print("Starting Tech News Reels Creation")
    print("-" * 30)

    news_json = get_tech_news(news_api_key)
    if news_json['status'] == 'error':
        print(f"Error fetching news: {news_json['message']}")
        return

    top_articles_index = get_top(news_json)
    if not top_articles_index:
        print("Error: Could not determine top articles.")
        return

    today = datetime.now().strftime('%Y-%m-%d')
    base_folder = os.path.join(os.getcwd(), today)
    os.makedirs(base_folder, exist_ok=True)

    for i, index in enumerate(top_articles_index):
        try:
            article = news_json['articles'][index]
            title = article['title']
            url = article['url']
            data_url = article['description'] + "Title: " + title

            try:
                data_url = await scrap(url)
                if not data_url:
                    print(f"Skipping article due to Jina fetch failure: {title}")
                    data_url = article['description'] + "Title: " + title
            except Exception as e:
                print(f"Error fetching data from Jina: {str(e)}")
                data_url = article['description'] + "Title: " + title
            prompt = reel_prompt(title, data_url)
            response = model.generate_content(prompt)
            reel_content = get_json(response.text)
            if not reel_content:
                print(f"Skipping article due to JSON parsing failure: {title}")
                continue
            
            print("generating audio....")
            # Generate audio
            tts = gTTS(text=' '.join(reel_content['script']), lang='en', slow=False)
            audio_path = os.path.join(base_path, f"{sanitize_filename(title)}_audio.mp3")
            tts.save(audio_path)

            # Speed up audio 1.25x
            audio = AudioFileClip(audio_path)
            audio_sped_up = audio.fx(vfx.speedx, 1.25)
            audio_sped_up_path = os.path.join(base_path, f"{sanitize_filename(title)}_audio_spedup.mp3")
            audio_sped_up.write_audiofile(audio_sped_up_path)

            # Create Reel
            print(f"Creating Reel for: {title}")
            create_reel(reel_content, base_path,base_folder, audio_sped_up_path)
            print("-" * 30)
        except Exception as e:
            print(f"Error processing article: {str(e)}")


if __name__ == "__main__":
    import shutil
    base_path = "temp"
    asyncio.run(process_news_for_reel(base_path))
    shutil.rmtree(base_path) 