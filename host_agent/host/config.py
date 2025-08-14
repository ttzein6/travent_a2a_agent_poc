"""
Configuration settings for the AI-Powered Candidate Matching RAG Agent.

These settings are used by the various RAG tools.
Vertex AI initialization is performed in the package's __init__.py
"""

import os

from dotenv import load_dotenv

# Load environment variables (this is redundant if __init__.py is imported first,
# but included for safety when importing config directly)
load_dotenv()

# Vertex AI settings
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION")

# RAG settings
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 150  # Increased for better context capture
DEFAULT_TOP_K = 8  # Increased to return more candidate matches
DEFAULT_DISTANCE_THRESHOLD = 0.55  # Adjusted for better candidate matching
DEFAULT_EMBEDDING_MODEL = "publishers/google/models/text-embedding-005"
DEFAULT_EMBEDDING_REQUESTS_PER_MIN = 1000

# LLM settings for candidate scoring
CANDIDATE_SCORING_MODEL = "gemini-2.5-flash-preview-05-20"  # Model used for candidate scoring

# Match quality thresholds - used by the LLM for consistent scoring
EXCELLENT_MATCH_THRESHOLD = 0.85  # Score needed for "Excellent Match"
STRONG_MATCH_THRESHOLD = 0.75     # Score needed for "Strong Match"
GOOD_MATCH_THRESHOLD = 0.65       # Score needed for "Good Match"
MODERATE_MATCH_THRESHOLD = 0.55    # Score needed for "Moderate Match"
POTENTIAL_MATCH_THRESHOLD = 0.45   # Score needed for "Potential Match"
WEAK_MATCH_THRESHOLD = 0.30        # Score needed for "Weak Match"
