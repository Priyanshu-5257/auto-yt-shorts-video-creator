# Auto-YouTube-Short-Creation

This project automates the process of creating engaging YouTube Shorts from the latest tech news articles. The workflow includes fetching articles, summarizing them, creating video scripts, generating voiceovers, and finally, producing short video reels with relevant stock footage.

## Prerequisites

To use this project, you will need the following API keys:

1. **Pexels API Key**: To fetch stock videos for YouTube Shorts.
   - Obtain your Pexels API key from [Pexels API](https://www.pexels.com/api/).
   
2. **Gemini API Key (Google Generative AI)**: To generate summaries and scripts from the articles.
   - Obtain your Gemini API key from [Google Gemini](https://cloud.google.com/genai).

3. **News API Key**: To fetch the latest tech news articles.
   - Obtain your News API key from [News API](https://newsapi.org/).

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/auto-yt-short-creation.git
cd auto-yt-short-creation
```

### 2. Install Dependencies

Create a virtual environment and install the required packages.

```bash
python -m venv venv
source venv/bin/activate  # On Windows use 'venv\Scripts\activate'
pip install -r requirements.txt
```

### 3. Set Up API Keys

In the project folder, create a `.env` file and add your API keys:

```ini
PEXELS_API_KEY=your_pexels_api_key
GEMINI_API_KEY=your_gemini_api_key
NEWS_API_KEY=your_news_api_key
```


### 4. Download Pexels Videos

Make sure you have internet access as the project will need to download stock videos from Pexels.

## Running the Script

Once everything is set up, you can run the script to create YouTube Shorts:

```bash
python create_reels.py
```

The script will:
1. Fetch the latest tech news articles using News API.
2. Generate short summaries and scripts for YouTube Shorts using Gemini AI.
3. Fetch relevant stock videos from Pexels.
4. Generate an audio file using Google Text-to-Speech (gTTS).
5. Compile the video clips, add subtitles, and synchronize with the generated audio.
6. Save the final video reel to the specified directory.

## Output

The final video reels will be saved in the specified directory under `temp/{date}/{article_title}.mp4`. The `temp` directory is cleaned up after the process is completed.

## Notes

- Ensure you have the necessary API keys before running the script.
- The project may download multiple videos from Pexels depending on the articles selected.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

---

For any questions or issues, feel free to open an issue on the repository or contact the maintainers.