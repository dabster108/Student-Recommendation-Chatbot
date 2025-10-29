"""
Student Recommendation POC - FastAPI Backend
============================================
A prototype recommendation system that collects student info and provides 
personalized content recommendations using TF-IDF + Cosine Similarity with 
Groq API for keyword extraction.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import json
import os
from dotenv import load_dotenv

# Machine Learning imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Groq API import
from groq import Groq

# Import recommendation engine
from app.routes import recommendation as rec_engine

# Load environment variables from specific path
ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Initialize FastAPI app
app = FastAPI(
    title="Student Recommendation API",
    description="AI-powered recommendation system for students",
    version="1.0.0"
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR.parent / "static"
DUMMY_DATA_PATH = DATA_DIR / "dummy_data.json"
STUDENT_DATA_PATH = DATA_DIR / "student.json"

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Load dummy data
try:
    with open(DUMMY_DATA_PATH, "r", encoding="utf-8") as f:
        DUMMY_DATA = json.load(f)
except FileNotFoundError:
    raise RuntimeError(f"Dummy data file not found at {DUMMY_DATA_PATH}")

# Initialize Groq client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("Warning: GROQ_API_KEY not found in environment variables")
    groq_client = None
else:
    groq_client = Groq(api_key=GROQ_API_KEY)


# ============================================
# Pydantic Models
# ============================================

class StudentOnboard(BaseModel):
    """Model for student onboarding data"""
    name: str
    username: str
    address: str
    faculty: str
    grade: str
    interests: List[str]
    courses_enrolled: List[str]


class RecommendationQuery(BaseModel):
    """Model for recommendation query"""
    query: str
    # Optional student id to request recommendations from a specific student profile
    student_id: Optional[int] = None


class RecommendationResponse(BaseModel):
    """Model for recommendation response"""
    student: Optional[Dict[str, Any]] = None
    query: str
    extracted_keywords: List[str]
    recommendations: List[Dict[str, Any]]


# ============================================
# Helper Functions
# ============================================

def load_all_students() -> List[Dict[str, Any]]:
    """Load all student profiles from student.json.

    Returns an empty list when the file doesn't exist or cannot be parsed.
    Accepts both legacy single-dict and list formats.
    """
    if not STUDENT_DATA_PATH.exists():
        return []

    try:
        with open(STUDENT_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return [data]
            return []
    except (json.JSONDecodeError, Exception):
        return []


def get_next_student_id() -> int:
    """Determine the next incremental numeric student id."""
    students = load_all_students()
    if not students:
        return 1
    ids = [s.get("id", 0) for s in students if isinstance(s.get("id", None), int)]
    return (max(ids) + 1) if ids else 1


def load_student_data() -> Optional[Dict[str, Any]]:
    """Backward-compatible loader that returns a single student when available.

    If multiple students exist, returns the first one to preserve legacy behavior.
    Use `load_all_students()` or `get_student_by_id()` for multi-student handling.
    """
    students = load_all_students()
    if not students:
        return None
    return students[0]


def save_student_data(student_input: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
    """Save student data.

    - If a dict is provided, append it to the stored list of students.
    - If a list is provided, overwrite the storage with that list.
    """
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if isinstance(student_input, dict):
        students = load_all_students()
        students.append(student_input)
        to_write = students
    elif isinstance(student_input, list):
        to_write = student_input
    else:
        raise ValueError("student_input must be a dict or list of dicts")

    with open(STUDENT_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(to_write, f, indent=2, ensure_ascii=False)


def get_student_by_id(student_id: int) -> Optional[Dict[str, Any]]:
    """Return student dict matching the provided id, or None."""
    students = load_all_students()
    for s in students:
        try:
            if int(s.get("id", -1)) == int(student_id):
                return s
        except Exception:
            continue
    return None


def resolve_student_for_request(student_id: Optional[int]) -> Optional[Dict[str, Any]]:
    """Resolve which student profile to use for a recommendation request.

    Behavior:
    - If student_id is provided: return that student's profile (or None if not found).
    - If no student_id and exactly one student exists: return that student's profile (legacy support).
    - Otherwise return None (anonymous request).
    """
    if student_id is not None:
        return get_student_by_id(student_id)

    students = load_all_students()
    if len(students) == 1:
        return students[0]
    return None


def extract_keywords_with_groq(query: str) -> List[str]:
    """
    Use Groq API to extract important keywords/intent from user query.
    Falls back to simple keyword extraction if API is unavailable.
    """
    if not groq_client:
        print("Groq API not available, using fallback keyword extraction")
        return fallback_keyword_extraction(query)
    
    try:
        system_prompt = """You are an intelligent keyword extraction assistant.

Analyze the user's query and extract keywords for what they WANT.
- Pay attention to words like: "want", "need", "interested in", "looking for"
- IGNORE words after: "don't want", "not interested", "avoid", "except", "but not"
- Add related synonyms and similar topics for positive preferences
- Never include topics the user explicitly rejects

Examples:
Input: "I don't want yoga but I want workout"
Output: workout, fitness, gym, strength training, cardio

Input: "I need physics help but not chemistry"
Output: physics, mechanics, thermodynamics, quantum

Input: "looking for engineering forums not medicine"
Output: engineering, technology, coding, programming, robotics

Return only comma-separated keywords for what the user WANTS."""

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Extract keywords from: {query}"
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=100
        )
        
        keywords_text = chat_completion.choices[0].message.content.strip()
        keywords = [kw.strip().lower() for kw in keywords_text.split(",")]
        
        print(f"Groq extracted keywords: {keywords}")
        return keywords
        
    except Exception as e:
        print(f"Groq API error: {e}, using fallback")
        return fallback_keyword_extraction(query)


def fallback_keyword_extraction(query: str) -> List[str]:
    """Simple fallback keyword extraction using basic NLP techniques"""
    stop_words = {'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 
                  'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 
                  'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
                  'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what',
                  'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am',
                  'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
                  'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the',
                  'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
                  'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
                  'through', 'during', 'before', 'after', 'above', 'below', 'to',
                  'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
                  'again', 'further', 'then', 'once', 'want', 'dont', 'not'}
    
    words = query.lower().split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    return keywords[:5] if keywords else [query.lower()]


def get_top_matches(
    query: str,
    dataset: List[Dict[str, Any]],
    key: str = "description",
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """Content-based recommendation using TF-IDF + Cosine Similarity."""
    if not dataset:
        return []
    
    texts = []
    valid_indices = []
    
    for idx, item in enumerate(dataset):
        text_content = item.get(key, "")
        
        if "title" in item and key != "title":
            text_content = f"{item.get('title', '')} {text_content}"
        
        if "tags" in item:
            tags = item.get("tags", [])
            if isinstance(tags, list):
                text_content = f"{text_content} {' '.join(tags)}"
        
        if text_content and text_content.strip():
            texts.append(text_content.strip())
            valid_indices.append(idx)
    
    if not texts:
        return []
    
    corpus = texts + [query]
    
    vectorizer = TfidfVectorizer(
        stop_words='english',
        max_features=1000,
        ngram_range=(1, 2)
    )
    
    tfidf_matrix = vectorizer.fit_transform(corpus)
    query_vector = tfidf_matrix[-1]
    doc_vectors = tfidf_matrix[:-1]
    similarities = cosine_similarity(query_vector, doc_vectors).flatten()
    top_indices = np.argsort(similarities)[::-1][:top_n]
    
    results = []
    for idx in top_indices:
        original_idx = valid_indices[idx]
        item_copy = dataset[original_idx].copy()
        item_copy["similarity_score"] = float(similarities[idx])
        results.append(item_copy)
    
    return results


def recommend_from_category(
    query: str,
    category: str,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """Get recommendations from a specific category in dummy data."""
    if category not in DUMMY_DATA:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category}' not found in dummy data"
        )
    
    dataset = DUMMY_DATA[category]
    
    if dataset and len(dataset) > 0:
        first_item = dataset[0]
        if "description" in first_item:
            key = "description"
        elif "content" in first_item:
            key = "content"
        elif "question" in first_item:
            key = "question"
        else:
            key = "title"
    else:
        key = "description"
    
    return get_top_matches(query, dataset, key=key, top_n=top_n)


# ============================================
# API Endpoints
# ============================================

@app.get("/")
async def home():
    """Serve the main HTML page"""
    html_path = STATIC_DIR / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    return {
        "message": "Student Recommendation API",
        "version": "1.0.0",
        "status": "running",
        "groq_enabled": groq_client is not None
    }

@app.get("/api")
async def api_info():
    """API health check endpoint"""
    return {
        "message": "Student Recommendation API",
        "version": "1.0.0",
        "status": "running",
        "groq_enabled": groq_client is not None
    }


@app.post("/onboard")
async def onboard_student(student: StudentOnboard):
    """
    Onboard a new student by saving their profile information.
    Automatically generates incremental ID starting from 1.
    """
    student_data = student.dict()
    student_data["id"] = get_next_student_id()
    
    try:
        save_student_data(student_data)
        return {
            "message": "Student onboarded successfully",
            "student": student_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save student data: {str(e)}"
        )


@app.get("/student")
async def get_student():
    """Get current student profile."""
    student_data = load_student_data()
    
    if not student_data:
        raise HTTPException(
            status_code=404,
            detail="No student profile found. Please onboard first using POST /onboard"
        )
    
    return student_data


@app.post("/recommend/forums", response_model=RecommendationResponse)
async def recommend_forums(req: RecommendationQuery):
    """Recommend forums based on user query and student profile."""
    student_data = load_student_data()
    keywords = extract_keywords_with_groq(req.query)
    
    forums_data = DUMMY_DATA.get("forums", [])
    recommendations = rec_engine.recommend_forums(
        query=req.query,
        forums_data=forums_data,
        student_data=student_data,
        top_n=5
    )
    
    return RecommendationResponse(
        student=student_data,
        query=req.query,
        extracted_keywords=keywords,
        recommendations=recommendations
    )


@app.post("/recommend/learning", response_model=RecommendationResponse)
async def recommend_learning(req: RecommendationQuery):
    """Recommend learning content based on user query and student profile."""
    student_data = load_student_data()
    keywords = extract_keywords_with_groq(req.query)
    
    recommendations = rec_engine.recommend_learning_content(
        query=req.query,
        bundles=DUMMY_DATA.get("bundles", []),
        courses=DUMMY_DATA.get("learning_courses", []),
        learning_sets=DUMMY_DATA.get("learning_sets", []),
        practice_sets=DUMMY_DATA.get("practice_sets", []),
        student_data=student_data,
        top_n=10
    )
    
    return RecommendationResponse(
        student=student_data,
        query=req.query,
        extracted_keywords=keywords,
        recommendations=recommendations
    )


@app.post("/recommend/wellness", response_model=RecommendationResponse)
async def recommend_wellness(req: RecommendationQuery):
    """Recommend wellness content based on user query and student profile."""
    student_data = load_student_data()
    keywords = extract_keywords_with_groq(req.query)
    
    recommendations = rec_engine.recommend_wellness(
        query=req.query,
        challenges=DUMMY_DATA.get("wellness_challenges", []),
        content=DUMMY_DATA.get("wellness_content", []),
        activities=DUMMY_DATA.get("wellness_activities", []),
        student_data=student_data,
        top_n=5
    )
    
    return RecommendationResponse(
        student=student_data,
        query=req.query,
        extracted_keywords=keywords,
        recommendations=recommendations
    )


@app.post("/recommend/opportunities", response_model=RecommendationResponse)
async def recommend_opportunities(req: RecommendationQuery):
    """Recommend opportunities based on user query and student profile."""
    student_data = load_student_data()
    keywords = extract_keywords_with_groq(req.query)
    
    opportunities_data = DUMMY_DATA.get("opportunities", [])
    recommendations = rec_engine.recommend_opportunities(
        query=req.query,
        opportunities_data=opportunities_data,
        student_data=student_data,
        top_n=5
    )
    
    return RecommendationResponse(
        student=student_data,
        query=req.query,
        extracted_keywords=keywords,
        recommendations=recommendations
    )


@app.post("/recommend/events", response_model=RecommendationResponse)
async def recommend_events(req: RecommendationQuery):
    """Recommend events based on user query and student profile."""
    student_data = load_student_data()
    keywords = extract_keywords_with_groq(req.query)
    
    events_data = DUMMY_DATA.get("events", [])
    recommendations = rec_engine.recommend_events(
        query=req.query,
        events_data=events_data,
        student_data=student_data,
        top_n=5
    )
    
    return RecommendationResponse(
        student=student_data,
        query=req.query,
        extracted_keywords=keywords,
        recommendations=recommendations
    )


@app.post("/recommend/scholarships", response_model=RecommendationResponse)
async def recommend_scholarships(req: RecommendationQuery):
    """Recommend scholarships based on user query and student profile."""
    student_data = load_student_data()
    keywords = extract_keywords_with_groq(req.query)
    
    scholarships_data = DUMMY_DATA.get("scholarships", [])
    recommendations = rec_engine.recommend_scholarships(
        query=req.query,
        scholarships_data=scholarships_data,
        student_data=student_data,
        top_n=5
    )
    
    return RecommendationResponse(
        student=student_data,
        query=req.query,
        extracted_keywords=keywords,
        recommendations=recommendations
    )


@app.post("/recommend/confessions", response_model=RecommendationResponse)
async def recommend_confessions(req: RecommendationQuery):
    """
    Recommend confessions based on user query and student profile.
    """
    student_data = load_student_data()
    keywords = extract_keywords_with_groq(req.query)
    
    confessions_data = DUMMY_DATA.get("confessions", [])
    recommendations = rec_engine.recommend_confessions(
        query=req.query,
        confessions_data=confessions_data,
        student_data=student_data,
        top_n=5
    )
    
    return RecommendationResponse(
        student=student_data,
        query=req.query,
        extracted_keywords=keywords,
        recommendations=recommendations
    )


@app.post("/recommend/flashcards", response_model=RecommendationResponse)
async def recommend_flashcards(req: RecommendationQuery):
    """
    Recommend flashcards based on user query and student profile.
    Considers enrolled courses and study interests.
    """
    student_data = load_student_data()
    keywords = extract_keywords_with_groq(req.query)
    
    flashcards_data = DUMMY_DATA.get("flashcards", [])
    recommendations = rec_engine.recommend_flashcards(
        query=req.query,
        flashcards_data=flashcards_data,
        student_data=student_data,
        top_n=5
    )
    
    return RecommendationResponse(
        student=student_data,
        query=req.query,
        extracted_keywords=keywords,
        recommendations=recommendations
    )


@app.post("/recommend/qna", response_model=RecommendationResponse)
async def recommend_qna(req: RecommendationQuery):
    """
    Recommend Q&A content based on user query and student profile.
    Considers enrolled courses and academic interests.
    """
    student_data = load_student_data()
    keywords = extract_keywords_with_groq(req.query)
    
    qna_data = DUMMY_DATA.get("qna", [])
    recommendations = rec_engine.recommend_qna(
        query=req.query,
        qna_data=qna_data,
        student_data=student_data,
        top_n=5
    )
    
    return RecommendationResponse(
        student=student_data,
        query=req.query,
        extracted_keywords=keywords,
        recommendations=recommendations
    )


@app.post("/recommend/truefalse", response_model=RecommendationResponse)
async def recommend_truefalse(req: RecommendationQuery):
    """
    Recommend True/False question sets based on user query and student profile.
    Considers enrolled courses and subjects of interest.
    """
    student_data = load_student_data()
    keywords = extract_keywords_with_groq(req.query)
    
    truefalse_data = DUMMY_DATA.get("true_false", [])
    recommendations = rec_engine.recommend_truefalse(
        query=req.query,
        truefalse_data=truefalse_data,
        student_data=student_data,
        top_n=5
    )
    
    return RecommendationResponse(
        student=student_data,
        query=req.query,
        extracted_keywords=keywords,
        recommendations=recommendations
    )


@app.post("/recommend/mcq", response_model=RecommendationResponse)
async def recommend_mcq(req: RecommendationQuery):
    """
    Recommend MCQ sets based on user query and student profile.
    Considers enrolled courses and subjects of interest.
    """
    student_data = load_student_data()
    keywords = extract_keywords_with_groq(req.query)
    
    mcq_data = DUMMY_DATA.get("mcq", [])
    recommendations = rec_engine.recommend_mcq(
        query=req.query,
        mcq_data=mcq_data,
        student_data=student_data,
        top_n=5
    )
    
    return RecommendationResponse(
        student=student_data,
        query=req.query,
        extracted_keywords=keywords,
        recommendations=recommendations
    )


# ============================================
# Legacy GET endpoints (for backward compatibility)
# ============================================

@app.get("/forums")
async def get_forums():
    """Get all forums"""
    return DUMMY_DATA["forums"]


@app.get("/learning")
async def get_learning_content():
    """Get all learning content"""
    return {
        "bundles": DUMMY_DATA["bundles"],
        "learning_courses": DUMMY_DATA["learning_courses"],
        "learning_sets": DUMMY_DATA["learning_sets"],
        "practice_sets": DUMMY_DATA["practice_sets"]
    }


@app.get("/wellness")
async def get_wellness():
    """Get all wellness content"""
    return {
        "wellness_challenges": DUMMY_DATA["wellness_challenges"],
        "wellness_content": DUMMY_DATA["wellness_content"],
        "wellness_activities": DUMMY_DATA["wellness_activities"]
    }


@app.get("/opportunities")
async def get_opportunities():
    """Get all opportunities"""
    return DUMMY_DATA["opportunities"]


@app.get("/events")
async def get_events():
    """Get all events"""
    return DUMMY_DATA["events"]


@app.get("/scholarships")
async def get_scholarships():
    """Get all scholarships"""
    return DUMMY_DATA["scholarships"]


@app.get("/confessions")
async def get_confessions():
    """Get all confessions"""
    return DUMMY_DATA["confessions"]


@app.get("/flashcards")
async def get_flashcards():
    """Get all flashcards"""
    return DUMMY_DATA["flashcards"]


@app.get("/qna")
async def get_qna():
    """Get all Q&A"""
    return DUMMY_DATA["qna"]


@app.get("/truefalse")
async def get_truefalse():
    """Get all True/False questions"""
    return DUMMY_DATA["true_false"]


@app.get("/mcq")
async def get_mcq():
    """Get all MCQ sets"""
    return DUMMY_DATA["mcq"]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)