"""
Recommendation Engine
=====================
Smart content-based recommendation system that considers:
1. User's query text
2. Student interests
3. Student courses enrolled
4. TF-IDF + Cosine Similarity matching
5. Semantic understanding via Groq API
"""

from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ENV_PATH = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Import Groq
try:
    from groq import Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except ImportError:
    groq_client = None
    print("Groq library not available")


def enhance_query_with_student_context(
    query: str,
    student_data: Optional[Dict[str, Any]]
) -> str:
    """
    Enhance the user query with student profile context.
    
    Combines:
    - Original query
    - Student interests
    - Student courses enrolled
    
    This helps recommendations be more personalized.
    """
    enhanced_query = query
    
    if student_data:
        if "interests" in student_data and student_data["interests"]:
            interests = " ".join(student_data["interests"])
            enhanced_query = f"{enhanced_query} {interests}"
        
        if "courses_enrolled" in student_data and student_data["courses_enrolled"]:
            courses = " ".join(student_data["courses_enrolled"])
            enhanced_query = f"{enhanced_query} {courses}"
    
    return enhanced_query


def semantic_relevance_check(
    query: str,
    item_text: str,
    threshold: float = 0.30
) -> tuple[bool, float]:
    """
    Use Groq API to check if an item is semantically relevant to the query.
    This helps filter out false positives from TF-IDF matching.
    """
    if not groq_client:
        return True, 0.5
    
    try:
        system_prompt = """You are a strict relevance checker for educational content recommendations.

Your job: Determine if the content directly matches what the user wants to learn.

Scoring rules (0-100):
- 0-20:  Completely different subject (physics vs programming, business vs medicine)
- 20-40: Different field but vaguely related (programming vs machine learning)
- 40-60: Related but not the main topic (calculus when asking for physics)
- 60-80: Good match - directly relevant to the query
- 80-100: Perfect match - exactly what user wants

BE STRICT:
- If user wants "physics", only physics content scores high (mechanics, thermodynamics, quantum)
- Programming content scores LOW for physics queries (below 30)
- Machine learning scores LOW for physics queries (below 20)
- Only give high scores (60+) if the content is DIRECTLY about the queried topic

Return ONLY a number from 0 to 100."""

        prompt = f"""User wants to learn: "{query}"

Content title and description: "{item_text}"

Relevance score (0-100):"""

        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,  # Lower temperature for more consistent scoring
            max_tokens=10
        )
        
        score_text = response.choices[0].message.content.strip()
        import re
        numbers = re.findall(r'\d+', score_text)
        if numbers:
            score = float(numbers[0]) / 100.0
        else:
            score = 0.5
        
        is_relevant = score >= threshold
        return is_relevant, score
        
    except Exception as e:
        print(f"Semantic check error: {e}")
        return True, 0.5


def get_recommendations(
    query: str,
    dataset: List[Dict[str, Any]],
    student_data: Optional[Dict[str, Any]] = None,
    content_key: str = "description",
    top_n: int = 10,
    min_similarity: float = 0.0,
    use_semantic_check: bool = True
) -> List[Dict[str, Any]]:
    """Get personalized recommendations using TF-IDF + Cosine Similarity + Semantic Check."""
    if not dataset:
        return []
    
    enhanced_query = enhance_query_with_student_context(query, student_data)
    
    texts = []
    valid_indices = []
    item_full_texts = {}
    
    for idx, item in enumerate(dataset):
        text_parts = []
        
        if content_key in item:
            text_parts.append(str(item[content_key]))
        
        if "title" in item and content_key != "title":
            text_parts.append(str(item["title"]))
        
        if "tags" in item and isinstance(item["tags"], list):
            text_parts.extend(item["tags"])
        
        if "category" in item:
            text_parts.append(str(item["category"]))
        
        full_text = " ".join(text_parts).strip()
        
        if full_text:
            texts.append(full_text)
            valid_indices.append(idx)
            item_full_texts[idx] = full_text
    
    if not texts:
        return []
    
    corpus = texts + [enhanced_query]
    
    vectorizer = TfidfVectorizer(
        stop_words='english',
        max_features=1000,
        ngram_range=(1, 2),
        min_df=1
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except Exception as e:
        print(f"TF-IDF error: {e}")
        return []
    
    query_vector = tfidf_matrix[-1]
    doc_vectors = tfidf_matrix[:-1]
    similarities = cosine_similarity(query_vector, doc_vectors).flatten()
    
    # Filter by minimum similarity threshold
    valid_results = []
    for idx, similarity in enumerate(similarities):
        if similarity > min_similarity:
            original_idx = valid_indices[idx]
            item_copy = dataset[original_idx].copy()
            
            # Add TF-IDF similarity score
            item_copy["tfidf_score"] = float(similarity)
            
            # Semantic relevance check using Groq
            if use_semantic_check and groq_client:
                item_text = item_full_texts[original_idx]
                is_relevant, semantic_score = semantic_relevance_check(query, item_text, threshold=0.30)
                
                if is_relevant:
                    # Combine TF-IDF and semantic scores
                    # 40% TF-IDF + 60% semantic for final score (prioritize semantic understanding)
                    combined_score = (0.4 * similarity) + (0.6 * semantic_score)
                    item_copy["similarity_score"] = float(combined_score)
                    item_copy["semantic_score"] = float(semantic_score)
                    valid_results.append((combined_score, item_copy))
                else:
                    # Skip items that fail semantic check
                    print(f" Filtered out: {item_copy.get('title', 'unknown')} (semantic: {semantic_score:.2f}, tfidf: {similarity:.2f})")
            else:
                # No semantic check, use TF-IDF score only
                item_copy["similarity_score"] = float(similarity)
                valid_results.append((similarity, item_copy))
    
    # Sort by similarity (descending)
    valid_results.sort(key=lambda x: x[0], reverse=True)
    
    # Return top N results
    return [item for _, item in valid_results[:top_n]]


def recommend_forums(
    query: str,
    forums_data: List[Dict[str, Any]],
    student_data: Optional[Dict[str, Any]] = None,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Recommend forums based on query and student profile.
    """
    return get_recommendations(
        query=query,
        dataset=forums_data,
        student_data=student_data,
        content_key="description",
        top_n=top_n,
        min_similarity=0.0
    )


def recommend_learning_content(
    query: str,
    bundles: List[Dict[str, Any]],
    courses: List[Dict[str, Any]],
    learning_sets: List[Dict[str, Any]],
    practice_sets: List[Dict[str, Any]],
    student_data: Optional[Dict[str, Any]] = None,
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Recommend learning content from bundles, courses, learning sets, and practice sets.
    """
    # Combine all learning content
    all_learning = []
    
    for bundle in bundles:
        item = bundle.copy()
        item["content_type"] = "bundle"
        all_learning.append(item)
    
    for course in courses:
        item = course.copy()
        item["content_type"] = "course"
        all_learning.append(item)
    
    for learning_set in learning_sets:
        item = learning_set.copy()
        item["content_type"] = "learning_set"
        all_learning.append(item)
    
    for practice_set in practice_sets:
        item = practice_set.copy()
        item["content_type"] = "practice_set"
        all_learning.append(item)
    
    return get_recommendations(
        query=query,
        dataset=all_learning,
        student_data=student_data,
        content_key="description",
        top_n=top_n,
        min_similarity=0.0
    )


def recommend_wellness(
    query: str,
    challenges: List[Dict[str, Any]],
    content: List[Dict[str, Any]],
    activities: List[Dict[str, Any]],
    student_data: Optional[Dict[str, Any]] = None,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Recommend wellness content from challenges, content, and activities.
    """
    # Combine all wellness content
    all_wellness = []
    
    for challenge in challenges:
        item = challenge.copy()
        item["content_type"] = "challenge"
        all_wellness.append(item)
    
    for wellness_item in content:
        item = wellness_item.copy()
        item["content_type"] = "wellness_content"
        all_wellness.append(item)
    
    for activity in activities:
        item = activity.copy()
        item["content_type"] = "activity"
        all_wellness.append(item)
    
    return get_recommendations(
        query=query,
        dataset=all_wellness,
        student_data=student_data,
        content_key="description",
        top_n=top_n,
        min_similarity=0.0
    )


def recommend_opportunities(
    query: str,
    opportunities_data: List[Dict[str, Any]],
    student_data: Optional[Dict[str, Any]] = None,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Recommend opportunities based on query and student profile.
    """
    return get_recommendations(
        query=query,
        dataset=opportunities_data,
        student_data=student_data,
        content_key="description",
        top_n=top_n,
        min_similarity=0.0
    )


def recommend_events(
    query: str,
    events_data: List[Dict[str, Any]],
    student_data: Optional[Dict[str, Any]] = None,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Recommend events based on query and student profile.
    """
    return get_recommendations(
        query=query,
        dataset=events_data,
        student_data=student_data,
        content_key="description",
        top_n=top_n,
        min_similarity=0.0
    )


def recommend_scholarships(
    query: str,
    scholarships_data: List[Dict[str, Any]],
    student_data: Optional[Dict[str, Any]] = None,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Recommend scholarships based on query and student profile.
    """
    return get_recommendations(
        query=query,
        dataset=scholarships_data,
        student_data=student_data,
        content_key="description",
        top_n=top_n,
        min_similarity=0.0
    )


def recommend_confessions(
    query: str,
    confessions_data: List[Dict[str, Any]],
    student_data: Optional[Dict[str, Any]] = None,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Recommend confessions based on query and student profile.
    """
    return get_recommendations(
        query=query,
        dataset=confessions_data,
        student_data=student_data,
        content_key="content",
        top_n=top_n,
        min_similarity=0.0
    )


def recommend_flashcards(
    query: str,
    flashcards_data: List[Dict[str, Any]],
    student_data: Optional[Dict[str, Any]] = None,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Recommend flashcard sets based on query and student profile.
    """
    return get_recommendations(
        query=query,
        dataset=flashcards_data,
        student_data=student_data,
        content_key="description",
        top_n=top_n,
        min_similarity=0.0
    )


def recommend_qna(
    query: str,
    qna_data: List[Dict[str, Any]],
    student_data: Optional[Dict[str, Any]] = None,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Recommend Q&A content based on query and student profile.
    """
    return get_recommendations(
        query=query,
        dataset=qna_data,
        student_data=student_data,
        content_key="question",
        top_n=top_n,
        min_similarity=0.0
    )


def recommend_truefalse(
    query: str,
    truefalse_data: List[Dict[str, Any]],
    student_data: Optional[Dict[str, Any]] = None,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Recommend True/False question sets based on query and student profile.
    """
    return get_recommendations(
        query=query,
        dataset=truefalse_data,
        student_data=student_data,
        content_key="description",
        top_n=top_n,
        min_similarity=0.0
    )


def recommend_mcq(
    query: str,
    mcq_data: List[Dict[str, Any]],
    student_data: Optional[Dict[str, Any]] = None,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Recommend MCQ sets based on query and student profile.
    """
    return get_recommendations(
        query=query,
        dataset=mcq_data,
        student_data=student_data,
        content_key="description",
        top_n=top_n,
        min_similarity=0.0
    )
