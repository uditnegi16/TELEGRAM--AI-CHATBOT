import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, ConversationHandler, filters
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
from datetime import datetime
import google.generativeai as generativeai
from datetime import timezone


# Environment variables (important!)
mongo_uri = "mongodb+srv://uditnegi521:udit521@cluster0.jryv5.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Correct way to access environment variable
bot_token = "7570968898:AAGfINcRcn1EOOL6jB1czBnfZLwBHTkFGuY" # Correct way to access environment variable
gemini_api_key = "AIzaSyAj_Wuj-r1QdKBUpvYRq9EYvFEpkbJmRVo"

# MongoDB Connection
client = MongoClient(mongo_uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(f"MongoDB connection error: {e}")
    exit()

db = client['Telegram'] # Database name corrected to 'Telegram'
users_collection = db['USERS'] # Collection name corrected to 'USERS'
chat_collection = db['CHAT']  # Define chat collection
image_collection = db['images']

# Gemini API Configuration
generativeai.configure(api_key=gemini_api_key)

# Telegram Bot Handlers (Combined)
async def start(update: Update, context: CallbackContext) -> None:
    contact_button = KeyboardButton("Share Contact", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True)
    await update.message.reply_text("Hi! Please share your contact by clicking the button below.", reply_markup=reply_markup)
    return "contact"  # Correct: Return the string label "contact"

async def handle_contact(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    # ... (rest of your handle_contact code) ...
    reply_keyboard = [['Yes', 'No']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    await update.message.reply_text("Thank you! Do you want to chat with me?", reply_markup=markup)

    context.user_data['waiting_for_chat_choice'] = True
    return "chat_choice"  # Correct: Return the string label "chat_choice"

async def chat_option_handler(update: Update, context: CallbackContext):
    user_choice = update.message.text.lower()
    if user_choice == 'yes':
        context.user_data['chatting'] = True
        await update.message.reply_text("Great! Let's chat.")
        return ConversationHandler.END  # Correct: Use ConversationHandler.END here
    elif user_choice == 'no':
        await update.message.reply_text("Okay, maybe later!")
        return ConversationHandler.END  # Correct: Use ConversationHandler.END here
    else:
        await update.message.reply_text("Please choose 'Yes' or 'No'.")
        return "chat_choice"  # Correct: Return the string label "chat_choice"


async def gemini_chat(update: Update, context: CallbackContext):
    if context.user_data.get('chatting'):
        user_message = update.message.text

        try:
            generativeai.configure(api_key=gemini_api_key)  # Configure the API key inside the function
            model = generativeai.GenerativeModel('gemini-pro')  # Specify the model
            
            # Correct method call
            response = model.generate_content(user_message)

            # Extract the response text
            if response and hasattr(response, "text"):
                bot_response = response.text
            else:
                bot_response = "No response from Gemini API"

            if bot_response:
                await update.message.reply_text(bot_response)

                chat_history = {
                    "user_id": update.message.chat_id,
                    "user_message": user_message,
                    "bot_response": bot_response,
                    "timestamp": datetime.now(timezone.utc) 
                }
                chat_collection.insert_one(chat_history)
            else:
                await update.message.reply_text("Gemini API returned an empty response.")

        except Exception as e:
            print(f"Gemini API error: {e}")
            await update.message.reply_text(f"There was an error processing your request. Please try again later. Error: {e}")
    else:
        await update.message.reply_text("Please register first using /start command.")

import io
from PIL import Image
from pdfplumber import open as open_pdf
from docx import Document
from telegram.ext import CallbackContext
from datetime import datetime
import google.generativeai as generativeai

# Assuming you already have this configured
generativeai.configure(api_key=gemini_api_key)


import math

# Function to send long text in smaller chunks
async def send_long_text(update, text, chunk_size=4096):
    """Helper function to split long text into chunks and send multiple messages."""
    # Split the text into smaller chunks
    num_chunks = math.ceil(len(text) / chunk_size)
    
    for i in range(num_chunks):
        chunk = text[i*chunk_size:(i+1)*chunk_size]
        await update.message.reply_text(chunk)
        
# Handle PDF Documents
async def handle_pdf(update: Update, context: CallbackContext):
    user = update.message.from_user
    file_id = update.message.document.file_id
    file = await context.bot.get_file(file_id)

    # Download the PDF file into memory
    file_buffer = io.BytesIO()
    await file.download_to_memory(out=file_buffer)
    file_buffer.seek(0)

    try:
        # Extract text from the PDF
        with open_pdf(file_buffer) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()  # Extract text from each page

        if text:
            await send_long_text(update, text)  # Send long text in chunks

            # Save extracted text to MongoDB
            file_metadata = {
                "user_id": update.message.chat_id,
                "filename": update.message.document.file_name,
                "description": text,
                "timestamp": datetime.now(),
            }
            chat_collection.insert_one(file_metadata)
        else:
            await update.message.reply_text("No text extracted from the PDF.")

    except Exception as e:
        print(f"Error processing PDF: {e}")
        await update.message.reply_text(f"Error processing PDF: {str(e)}")

    return ConversationHandler.END  # End the conversation

# Handle DOCX Documents
async def handle_docx(update: Update, context: CallbackContext):
    user = update.message.from_user
    file_id = update.message.document.file_id
    file = await context.bot.get_file(file_id)

    # Download the DOCX file into memory
    file_buffer = io.BytesIO()
    await file.download_to_memory(out=file_buffer)
    file_buffer.seek(0)

    try:
        # Extract text from the DOCX
        doc = Document(file_buffer)
        text = "\n".join([para.text for para in doc.paragraphs])

        if text:
            await send_long_text(update, text)  # Send long text in chunks

            # Save extracted text to MongoDB
            file_metadata = {
                "user_id": update.message.chat_id,
                "filename": update.message.document.file_name,
                "description": text,
                "timestamp": datetime.now(),
            }
            chat_collection.insert_one(file_metadata)
        else:
            await update.message.reply_text("No text extracted from the DOCX.")

    except Exception as e:
        print(f"Error processing DOCX: {e}")
        await update.message.reply_text(f"Error processing DOCX: {str(e)}")

    return ConversationHandler.END  # End the conversation

# Handle Images (JPG, PNG, etc.)
async def handle_image(update: Update, context: CallbackContext):
    """Function to handle image file, send to Gemini, and send back the analysis."""
    user = update.message.from_user
    file_id = update.message.photo[-1].file_id  # Get highest resolution photo
    file = await context.bot.get_file(file_id)

    # Download the image file into memory
    file_buffer = io.BytesIO()
    await file.download_to_memory(out=file_buffer)
    file_buffer.seek(0)

    try:
        # Use PIL to open the image
        img = Image.open(file_buffer)

        # Send the image to Gemini for analysis (example with a placeholder function)
        response = generativeai.GenerativeModel('gemini-1.5-flash').generate_content([img, "Analyze the content of this image."])

        # Retrieve the analysis text from the response (adjust based on actual response structure)
        description = response.text if hasattr(response, "text") else "No response from Gemini."

        # Send the description in chunks if it's too long for Telegram
        await send_long_text(update, description)

        # Save file metadata to MongoDB (you can modify this part based on your MongoDB setup)
        file_metadata = {
            "user_id": update.message.chat_id,
            "filename": file.file_unique_id + ".jpg",  # Or the relevant extension
            "description": description,
            "timestamp": datetime.now(),
        }
        image_collection.insert_one(file_metadata)

    except Exception as e:
        await update.message.reply_text(f"Error processing image: {str(e)}")
# Main handler function for documents (PDF, DOCX, and Images)
async def handle_document(update: Update, context: CallbackContext):
    file = update.message.document
    file_name = file.file_name

    # Check for file extensions and route to respective handlers
    if file_name.lower().endswith('.pdf'):
        await handle_pdf(update, context)
    elif file_name.lower().endswith('.docx'):
        await handle_docx(update, context)
    elif file_name.lower().endswith(('jpg', 'jpeg', 'png')):
        await handle_image(update, context)
    else:
        await update.message.reply_text("Unsupported file format. Please upload a PDF, DOCX, or an image.")

    return ConversationHandler.END  # End the conversation
def main():
    if not bot_token:
        print("TELEGRAM_BOT_TOKEN environment variable not set.")
        return

    application = Application.builder().token(bot_token).build()

    conv_handler = ConversationHandler(  # Correct indentation
        entry_points=[CommandHandler("start", start)],
        states={
            "contact": [MessageHandler(filters.CONTACT, handle_contact)],
            "chat_choice": [MessageHandler(filters.TEXT, chat_option_handler)],
        },
        fallbacks=[MessageHandler(filters.TEXT, chat_option_handler)],
    )

    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gemini_chat))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.Document, handle_document))  # ✅ Correct
    application.run_polling()


if __name__ == '__main__':
    main()

