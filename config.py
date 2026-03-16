"""
Configuration settings for Ghostbuster
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

# Confidence Score Thresholds
CONFIDENCE_THRESHOLD_HIGH = int(os.getenv('CONFIDENCE_THRESHOLD_HIGH', 75))
CONFIDENCE_THRESHOLD_LOW = int(os.getenv('CONFIDENCE_THRESHOLD_LOW', 40))

# Red Flag Weights (used in scoring algorithm)
RED_FLAG_WEIGHTS = {
    'posting_age_days': 2,  # Older postings are more suspicious
    'generic_description': 3,  # Very generic = likely fake
    'no_salary': 1,  # Missing salary info
    'vague_requirements': 2,  # Unclear requirements
    'company_size_mismatch': 4,  # Job doesn't match company stage
    'multiple_similar_postings': 3,  # Same job posted many times
    'no_company_presence': 5,  # Can't find company info
    'unrealistic_requirements': 2,  # Too many requirements
}

# User Agent for web scraping (pretends to be a browser)
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'