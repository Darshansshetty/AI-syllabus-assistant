from fastapi import FastAPI, UploadFile, File
import fitz  # PyMuPDF for PDFs
import docx
from googleapiclient.discovery import build
import tempfile
import os
from io import BytesIO
from dotenv import load_dotenv
load_dotenv()
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # or ["*"] for all origins (not recommended for prod)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

# app.mount("/static", StaticFiles(directory="static"), name="static")
# templates = Jinja2Templates(directory="templates")
# @app.get("/", response_class=HTMLResponse)
# def read_root(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})

# @app.post("/upload_form", response_class=HTMLResponse)
# async def upload_form(request: Request, file: UploadFile = File(...)):
#     if file.filename.endswith(".pdf"):
#         text = await extract_text_from_pdf(file)
#     elif file.filename.endswith(".docx"):
#         text = await extract_text_from_docx(file)
#     else:
#         return templates.TemplateResponse("index.html", {
#             "request": request,
#             "error": "Unsupported file format"
#         })

#     query = " ".join(text.split()[:10])
#     videos = search_youtube_videos(query)
#     return templates.TemplateResponse("result.html", {
#         "request": request,
#         "query": query,
#         "videos": videos
#     })



@app.get("/")  # Define a root endpoint
def read_root():
    return {"message": "Welcome to the AI-powered academic notes retriever!"}

# YouTube API Key (Store in .env for security)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Function to extract text from PDF
async def extract_text_from_pdf(file: UploadFile):
    contents = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        doc = fitz.open(tmp_path)
        text = " ".join([page.get_text() for page in doc])
        doc.close()
    finally:
        os.remove(tmp_path)

    return text
# Function to extract text from Word file
async def extract_text_from_docx(file: UploadFile):
    contents = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    doc = docx.Document(tmp_path)
    text = " ".join([p.text for p in doc.paragraphs])
    os.remove(tmp_path)

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
    try:
        # File type check and text extraction
        if file.filename.endswith(".pdf"):
            text = await extract_text_from_pdf(file)
        elif file.filename.endswith(".docx"):
            text = await extract_text_from_docx(file)
        else:
            return {"error": "Unsupported file format"}

        if not text.strip():
            return {"error": "The uploaded file is empty or unreadable."}

        # Extract first 10 words as YouTube search query
        query = " ".join(text.split()[:10])

        # Attempt to fetch YouTube videos
        try:
            videos = search_youtube_videos(query)
        except Exception as e:
            return {"error": "YouTube search failed", "details": str(e)}

        return {"query": query, "videos": videos}

    except Exception as e:
        return {"error": "File processing failed", "details": str(e)}