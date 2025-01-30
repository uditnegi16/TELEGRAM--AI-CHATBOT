# Telegram Bot with File Handling, AI, and Web Search

This is a Python Telegram bot that integrates multiple features, including:
- Handling document files (PDF, DOCX)
- Image file processing with Gemini API
- Web search and summarization using Google Custom Search and OpenAI API

## Features
1. **Image Analysis**: Upload an image (JPG, PNG) and the bot will send it to Gemini for content analysis.
2. **Document Processing**: Upload a PDF or DOCX file, and the bot will extract the text content and send it back. It also saves metadata to MongoDB.
3. **Web Search**: Users can query the bot to perform a web search. The bot will summarize the top search results and provide the links.

## Setup

1. Install the necessary dependencies:
    ```bash
    pip install python-telegram-bot pymongo google-api-python-client openai pillow pdfplumber python-docx
    ```

2. Set up your environment variables:
    - `bot_token`: Your Telegram bot token.
    - `gemini_api_key`: Your Gemini API key.
    - `mongo_uri`: MongoDB connection string.

3. Run the bot:
    ```bash
    python bot3.py
    ```

## Usage

- Send `/start` to begin.
- Upload a PDF, DOCX, or image file for processing.
- Use `/websearch <query>` to perform a web search.
# TELEGRAM--AI-CHATBOT
