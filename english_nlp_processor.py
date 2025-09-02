import gzip
from warcio.archiveiterator import ArchiveIterator
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import langdetect
from collections import Counter
from typing import List, Dict, Tuple
import re
import warnings
import logging
from lxml import etree
import spacy

# Configure warnings and logging
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EnglishWebpageProcessor:
    def __init__(self, warc_file_path: str):
        self.warc_file_path = warc_file_path
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.processed_pages = []
        # Load spaCy model for NER
        self.nlp = spacy.load('en_core_web_sm')
        
    def parse_content(self, content: str) -> Tuple[str, str, str]:
        """
        Parse content trying both XML and HTML parsers.
        Returns: (text_content, title, content_type)
        """
        # Try XML first
        try:
            soup = BeautifulSoup(content, 'lxml-xml')
            if soup.find():  # Check if any XML content was parsed
                return (
                    soup.get_text(separator=' ', strip=True),
                    str(soup.title.string) if soup.title else '',
                    'xml'
                )
        except Exception:
            pass
        
        # Fallback to HTML
        try:
            soup = BeautifulSoup(content, 'lxml')
            # Remove non-content elements
            for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
            
            # Get main content (preferably from article or main tags)
            main_content = soup.find('article') or soup.find('main') or soup.find('body')
            text_content = main_content.get_text(separator=' ', strip=True) if main_content else ''
            
            return (
                text_content,
                str(soup.title.string) if soup.title else '',
                'html'
            )
        except Exception as e:
            logging.warning(f"Parsing failed: {str(e)}")
            return '', '', 'unknown'

    def is_english_content(self, text: str, threshold: float = 0.8) -> Tuple[bool, float]:
        try:
            lang_scores = langdetect.detect_langs(text)
            for lang in lang_scores:
                if lang.lang == 'en':
                    return True, lang.prob
            return False, 0.0
        except:
            return False, 0.0
    
    def clean_text(self, text: str) -> str:
        # Convert to lowercase
        text = text.lower()
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        # Remove special characters and numbers
        text = re.sub(r'[^\w\s]', ' ', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        words = word_tokenize(text)
        words = [w for w in words if w.isalnum() and w not in self.stop_words]
        return [word for word, _ in Counter(words).most_common(top_k)]
    
    def create_summary(self, text: str, max_sentences: int = 3) -> str:
        sentences = sent_tokenize(text)
        return ' '.join(sentences[:max_sentences])
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
      #using spacy
        doc = self.nlp(text)
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            if ent.text not in entities[ent.label_]:  # Avoid duplicates
                entities[ent.label_].append(ent.text)
        return entities
    
    def process_warc_file(self):
        #Process WARC file with improved content handling
        logging.info(f"Processing WARC file: {self.warc_file_path}")
        processed_count = 0
        error_count = 0

        with gzip.open(self.warc_file_path, 'rb') as stream:
            for record in ArchiveIterator(stream):
                if record.rec_type != 'response':
                    continue
                
                try:
                    url = record.rec_headers.get_header('WARC-Target-URI')
                    content = record.content_stream().read().decode('utf-8', errors='ignore')
                    
                    # Parse content
                    text, title, content_type = self.parse_content(content)
                    
                    if not text or len(text.strip()) < 100:  # Skip if too little content
                        continue
                    
                    # Check if content is English
                    is_english, lang_score = self.is_english_content(text)
                    if not is_english or lang_score < 0.8:
                        continue
                    
                    # Clean and process text
                    cleaned_text = self.clean_text(text)
                    keywords = self.extract_keywords(cleaned_text)
                    summary = self.create_summary(cleaned_text)
                    
                    # Extract named entities
                    entities = self.extract_entities(cleaned_text)
                    
                    self.processed_pages.append({
                        'url': url,
                        'title': title or url,
                        'cleaned_text': cleaned_text,
                        'keywords': keywords,
                        'summary': summary,
                        'language_score': lang_score,
                        'content_type': content_type,
                        'named_entities': entities
                    })
                    
                    processed_count += 1
                    if processed_count % 10 == 0:
                        logging.info(f"Processed {processed_count} pages...")
                    
                except Exception as e:
                    error_count += 1
                    logging.error(f"Error processing {url}: {str(e)}")
                    continue
        
        logging.info(f"Processing complete. Successfully processed {processed_count} pages. "
                    f"Errors encountered: {error_count}")

    def calculate_similarities(self) -> List[Tuple[int, int, float]]:
        if not self.processed_pages:
            return []
        
        # Create TF-IDF matrix
        texts = [page['cleaned_text'] for page in self.processed_pages]
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        # Calculate similarities
        similarities = []
        sim_matrix = cosine_similarity(tfidf_matrix)
        
        for i in range(len(self.processed_pages)):
            for j in range(i + 1, len(self.processed_pages)):
                sim_score = sim_matrix[i][j]
                if sim_score > 0.2:  # Only store meaningful similarities
                    similarities.append((i + 1, j + 1, float(sim_score)))
        
        return similarities