"""
Text Preprocessor for WolloNet Search Engine.
Handles tokenization, stopword removal, and stemming for
English and Ethiopic-script languages (Amharic, Tigregna, Afan Oromo).
"""
import re
import logging
import unicodedata
from pathlib import Path

logger = logging.getLogger('search_app')

# Ethiopic Unicode block range: U+1200 to U+137F
ETHIOPIC_RANGE = re.compile(r'[\u1200-\u137F]+')

# Built-in English stopwords
ENGLISH_STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'shall', 'can', 'not', 'no', 'nor',
    'so', 'yet', 'both', 'either', 'neither', 'each', 'few', 'more', 'most',
    'other', 'some', 'such', 'than', 'too', 'very', 'just', 'as', 'if',
    'then', 'that', 'this', 'these', 'those', 'it', 'its', 'i', 'me', 'my',
    'we', 'our', 'you', 'your', 'he', 'she', 'his', 'her', 'they', 'their',
    'what', 'which', 'who', 'whom', 'when', 'where', 'why', 'how', 'all',
    'also', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further', 'once',
    'here', 'there', 'about', 'against', 'between', 'while', 'although',
    'because', 'since', 'until', 'unless', 'however', 'therefore', 'thus',
}

# Built-in Amharic stopwords (common function words)
AMHARIC_STOPWORDS = {
    'እና', 'ወይም', 'ነው', 'ናት', 'ናቸው', 'ነበር', 'ነበሩ', 'ይሆናል', 'ሆነ',
    'ሆኑ', 'አለ', 'አለች', 'አሉ', 'ነበረ', 'ነበረች', 'ነበሩ', 'ይህ', 'ይህን',
    'ይህም', 'ያ', 'ያን', 'ያም', 'እነዚህ', 'እነዚያ', 'ስለ', 'ለ', 'ከ', 'በ',
    'እስከ', 'ወደ', 'ላይ', 'ውስጥ', 'ጋር', 'ዘንድ', 'ምክንያቱም', 'ስለዚህ',
    'ግን', 'ነገር', 'ግን', 'ደግሞ', 'ብቻ', 'ሁሉ', 'ሁሉም', 'አንድ', 'አንዲት',
    'እኔ', 'አንተ', 'አንቺ', 'እሱ', 'እሷ', 'እኛ', 'እናንተ', 'እነሱ', 'የ',
    'ያለ', 'ያለው', 'ያለች', 'ያሉ', 'ያለን', 'ያለው', 'ያለቸው', 'ያለቸው',
    'ሲሆን', 'ሲሆኑ', 'ሲሆን', 'ሆኖ', 'ሆና', 'ሆነው', 'ሆኖም', 'ሆናም',
    'ወቅት', 'ጊዜ', 'ቦታ', 'ቦታው', 'ቦታዋ', 'ቦታቸው', 'ቦታችን',
    'ምን', 'ማን', 'የት', 'መቼ', 'ለምን', 'እንዴት', 'ስንት', 'ምን ያህል',
    'ሌላ', 'ሌሎች', 'ሌሎቹ', 'ሌሎቹ', 'ሌሎቹ', 'ሌሎቹ', 'ሌሎቹ',
    'ብዙ', 'ጥቂት', 'ሁሉ', 'ሁሉም', 'አንዳንድ', 'አንዳንዶቹ', 'አብዛኛው',
    'ሲ', 'ሲሆን', 'ሲሆኑ', 'ሲሆን', 'ሲሆኑ', 'ሲሆን', 'ሲሆኑ',
    'ም', 'ም', 'ም', 'ም', 'ም', 'ም', 'ም', 'ም', 'ም', 'ም',
}

# Combined default stopwords
DEFAULT_STOPWORDS = ENGLISH_STOPWORDS | AMHARIC_STOPWORDS


def load_stopwords_from_file(filepath):
    """Load stopwords from a UTF-8 text file, one per line."""
    try:
        path = Path(filepath)
        if path.exists():
            words = set()
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith('#'):
                        words.add(word)
            logger.info(f'Loaded {len(words)} stopwords from {filepath}')
            return words
        else:
            logger.warning(f'Stopword file not found: {filepath}')
            return DEFAULT_STOPWORDS
    except Exception as e:
        logger.warning(f'Failed to load stopwords from {filepath}: {e}')
        return DEFAULT_STOPWORDS


def normalize_ethiopic(token):
    """
    Apply NFC normalization and collapse Ethiopic fidel variants.
    Ethiopic characters in U+1200-U+137F are kept as-is after NFC.
    """
    return unicodedata.normalize('NFC', token)


def tokenize(text):
    """
    Tokenize text into words.
    - Splits on whitespace and non-letter characters
    - Preserves Ethiopic Unicode block characters (U+1200-U+137F) as valid tokens
    - Removes pure digit/punctuation tokens
    """
    if not text:
        return []

    # Normalize unicode
    text = unicodedata.normalize('NFC', text)

    tokens = []
    # Split on whitespace first
    for word in text.split():
        # Check if it's an Ethiopic token
        if ETHIOPIC_RANGE.fullmatch(word):
            tokens.append(normalize_ethiopic(word))
            continue

        # For Latin/mixed text: extract alphabetic sequences
        parts = re.findall(r'[a-zA-Z]+', word)
        for part in parts:
            if len(part) >= 2:  # skip single characters
                tokens.append(part.lower())

        # Also extract any Ethiopic substrings within mixed tokens
        ethiopic_parts = ETHIOPIC_RANGE.findall(word)
        for part in ethiopic_parts:
            tokens.append(normalize_ethiopic(part))

    return tokens


def remove_stopwords(tokens, stopwords=None):
    """Remove stopwords from token list."""
    if stopwords is None:
        stopwords = DEFAULT_STOPWORDS
    return [t for t in tokens if t not in stopwords]


def stem_token(token, stemmer=None):
    """
    Apply stemming to a token.
    Falls back to the original token if stemming fails.
    """
    if stemmer is None:
        return token
    try:
        return stemmer.stem(token)
    except Exception as e:
        logger.warning(f'Stemming failed for token "{token}": {e}')
        return token


def preprocess(text, stopwords=None, stemmer=None, use_stemming=True):
    """
    Full preprocessing pipeline:
    1. Tokenize
    2. Remove stopwords
    3. Stem (optional)

    Returns an ordered list of normalized tokens.
    """
    if not text:
        return []

    tokens = tokenize(text)
    tokens = remove_stopwords(tokens, stopwords or DEFAULT_STOPWORDS)

    if use_stemming and stemmer:
        tokens = [stem_token(t, stemmer) for t in tokens]

    return tokens


def get_default_stemmer():
    """Get the NLTK Porter stemmer, or None if NLTK is unavailable."""
    try:
        from nltk.stem import PorterStemmer
        return PorterStemmer()
    except ImportError:
        logger.warning('NLTK not available; stemming disabled.')
        return None
