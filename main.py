from fastapi import FastAPI, UploadFile, File
import fitz  # PyMuPDF for PDFs
import docx
from googleapiclient.discovery import build
import tempfile
import os

app = FastAPI()

@app.get("/")  # Define a root endpoint
def read_root():
    return {"message": "Welcome to the AI-powered academic notes retriever!"}

# YouTube API Key (Store in .env for security)
YOUTUBE_API_KEY = "AIzaSyA216qPfndLfTWJWvXEJNyy4pe1npG-QPE"

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.file.read())  # Save the uploaded file to disk
        tmp_path = tmp.name  # Store the file path
    
    # Open the PDF using PyMuPDF
    try:
        doc = fitz.open(tmp_path)  # Open file from disk
        text = " ".join([page.get_text() for page in doc])
        doc.close()  # Close the file after reading
    finally:
        os.remove(tmp_path)  # Now it's safe to delete

    return text
# Function to extract text from Word file
def extract_text_from_docx(docx_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(docx_file.file.read())  # Save file to temp storage
        tmp_path = tmp.name

    doc = docx.Document(tmp_path)
    text = " ".join([p.text for p in doc.paragraphs])

    os.remove(tmp_path)  # Clean up temp file
    return text

# Function to search YouTube videos
def search_youtube_videos(query):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(q=query, part="snippet", maxResults=5)
    response = request.execute()

    videos = []
    for item in response["items"]:
        video_id = item.get("id", {}).get("videoId", "")
        if video_id:  # Ensure it's a video, not a channel/playlist
            videos.append({
                "title": item["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={video_id}"
            })
    
    return videos

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(file)
    elif file.filename.endswith(".docx"):
        text = extract_text_from_docx(file)
    else:
        return {"error": "Unsupported file format"}

    # Extract first 10 words as topic query
    query = " ".join(text.split()[:10])
    
    # Fetch YouTube videos
    videos = search_youtube_videos(query)
    
    return {"query": query, "videos": videos}
