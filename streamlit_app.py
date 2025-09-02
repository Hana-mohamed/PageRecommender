import streamlit as st
import pandas as pd
import plotly.express as px
from simple_db_manager import SimpleWebpageDBManager
import sqlite3
import json
import os
from typing import List, Dict, Tuple
import requests
from bs4 import BeautifulSoup
import html2text
import re
from urllib.parse import urljoin
from warcio.archiveiterator import ArchiveIterator
import gzip
import logging


# Page configuration
st.set_page_config(
    page_title="Page Recommender",
    page_icon="🔍",
    layout="wide"
)

# Session state for the database manager
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = None

# Initialize database manager
@st.cache_resource
def get_db_manager():
    """Initialize database manager with path"""
    try:
        # Get absolute path to the database
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, 'webpage_analysis.db')
        
        st.sidebar.write(f"Database path: {db_path}")
        
        if not os.path.exists(db_path):
            st.sidebar.error("Database file not found!")
            return None
            
        db_manager = SimpleWebpageDBManager(db_path)
        
        # Verify database is properly initialized
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='webpages') as has_webpages,
                    (SELECT COUNT(*) FROM webpages) as webpage_count
            """)
            has_tables, row_count = cursor.fetchone()
            
            if has_tables == 0:
                st.sidebar.error("Database schema not initialized!")
                return None
                
            st.sidebar.success(f"Database connected. Found {row_count} webpages.")
            return db_manager
            
    except Exception as e:
        st.sidebar.error(f"Database initialization failed: {str(e)}")
        return None

# Custom CSS
st.markdown("""
<style>
    /* Webpage Mirror Styling */
    .webpage-mirror {
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 0;
        margin: 20px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        overflow: hidden;
    }
    
    .webpage-header {
        background: #f8f9fa;
        padding: 15px 20px;
        border-bottom: 1px solid #eee;
    }
    
    .webpage-meta {
        color: #666;
        font-size: 14px;
        margin-top: 5px;
    }
    
    .source-link {
        color: #1976d2;
        text-decoration: none;
        font-weight: 500;
    }
    
    .source-link:hover {
        text-decoration: underline;
    }
    
    .webpage-content {
        padding: 20px;
        max-height: 800px;
        overflow-y: auto;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Content Styling */
    .webpage-content {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        line-height: 1.6;
        font-size: 16px;
        color: #333;
    }
    
    .webpage-content p {
        margin: 1em 0;
    }
    
    .webpage-content img {
        max-width: 100%;
        height: auto;
        margin: 1em 0;
        border-radius: 4px;
    }
    
    .webpage-content a {
        color: #1976d2;
        text-decoration: none;
        transition: color 0.2s ease;
    }
    
    .webpage-content a:hover {
        color: #1565c0;
        text-decoration: underline;
    }
    
    .webpage-content h1, .webpage-content h2, .webpage-content h3 {
        margin: 1.5em 0 0.5em;
        color: #1a1a1a;
    }
    
    .webpage-content ul, .webpage-content ol {
        margin: 1em 0;
        padding-left: 2em;
    }
    
    .webpage-content blockquote {
        margin: 1em 0;
        padding-left: 1em;
        border-left: 4px solid #e0e0e0;
        color: #666;
    }
    
    .webpage-content code {
        background: #f5f5f5;
        padding: 0.2em 0.4em;
        border-radius: 3px;
        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
    }
    
    .webpage-content h1, 
    .webpage-content h2, 
    .webpage-content h3, 
    .webpage-content h4 {
        margin: 1em 0 0.5em 0;
        line-height: 1.3;
    }
    
    .webpage-content p {
        margin: 0.8em 0;
        line-height: 1.6;
    }
    
    .webpage-content ul, 
    .webpage-content ol {
        margin: 1em 0;
        padding-left: 2em;
    }
    
    /* Responsive layout */
    @media (max-width: 768px) {
        .webpage-content {
            padding: 15px;
        }
    }
    
    .result-card:hover {
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    .result-card.main-result {
        border-left: 5px solid #1976d2;
    }
    
    .result-card.related-content {
        border-left: 5px solid #2e8b57;
    }
    
    /* Tags and Badges */
    .keyword-tag {
        background-color: #e3f2fd;
        color: #1976d2;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        margin: 0.3rem;
        display: inline-block;
        font-size: 0.9rem;
        transition: all 0.2s ease;
    }
    
    .keyword-tag:hover {
        background-color: #1976d2;
        color: white;
    }
    
    .similarity-badge {
        background-color: #2e8b57;
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        display: inline-block;
        font-weight: bold;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    
    /* Content Layout */
    .content-preview {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    .relationship-info {
        display: flex;
        justify-content: space-between;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #eee;
    }
    
    /* Advanced Search Section */
    .search-options {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    /* Loading States */
    .loading-spinner {
        text-align: center;
        padding: 2rem;
        color: #1976d2;
    }
    .similar-page {
        padding: 1rem;
        border-left: 3px solid #2e8b57;
        margin: 1rem 0;
        background-color: #ffffff;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .stMarkdown a {
        color: #1976d2;
        text-decoration: none;
    }
    .stMarkdown a:hover {
        text-decoration: underline;
    }
    .right-column {
        border-left: 1px solid #eee;
        padding-left: 2rem;
        height: 100vh;
        overflow-y: auto;
    }
    .result-card {
        background-color: #ffffff;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #eee;
    }
    .result-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Webpage content container */
    .webpage-content {
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        line-height: 1.6;
    }
    
    .webpage-content img {
        max-width: 100%;
        height: auto;
        margin: 10px 0;
    }
    
    .webpage-content a {
        color: #1976d2;
        text-decoration: none;
    }
    
    .webpage-content a:hover {
        text-decoration: underline;
    }
    
    /* Error message styling */
    .error-message {
        padding: 20px;
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

def fetch_from_warc(url: str, warc_path: str = 'english.warc.gz') -> Tuple[str, str, str]:
    """Fetch content from local WARC file with optimized processing"""
    try:
        # Use a context manager for proper resource handling
        with gzip.open(warc_path, 'rb') as stream:
            for record in ArchiveIterator(stream):
                if record.rec_type == 'response':
                    record_url = record.rec_headers.get_header('WARC-Target-URI')
                    if record_url == url:
                        # Read and decode content with error handling
                        content = record.content_stream().read()
                        content = content.decode('utf-8', errors='ignore')
                        
                        # Parse with BeautifulSoup using lxml for speed
                        soup = BeautifulSoup(content, 'lxml')
                        
                        # Get title
                        title = soup.title.string if soup.title else url
                        
                        # Clean content
                        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
                            tag.decompose()
                        
                        # Convert to readable format
                        h = html2text.HTML2Text()
                        h.ignore_links = False
                        h.ignore_images = False
                        h.body_width = 0
                        text_content = h.handle(str(soup))
                        
                        return title, text_content, 'warc'
        return None, None, None
    except Exception as e:
        logging.error(f"Error reading WARC file: {e}")
        return None, None, None

def fetch_webpage_content(url: str) -> Tuple[str, str]:
    """Fetch webpage content from local WARC file for faster access.
    Only falls back to live URL if content is not found in WARC."""
    
    # First try to get content from WARC file
    title, content, source = fetch_from_warc(url)
    if title and content:
        return title, f"""
{content}

*Retrieved from local WARC archive*
"""
    
    # Only if WARC fetch fails, try live webpage
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0 
    
    def create_error_message(status_code: int, url: str) -> str:
        messages = {
            404: "This page no longer exists (404 Not Found).",
            403: "Access to this page is forbidden (403 Forbidden).",
            412: "Website requires specific conditions (412 Precondition Failed).",
            500: "The website's server encountered an error (500 Internal Server Error).",
            503: "The website is temporarily unavailable (503 Service Unavailable).",
            504: "The website took too long to respond (504 Gateway Timeout)."
        }
        return f"""
### ⚠️ This content is no longer accessible

**URL:** {url}
**Status:** {messages.get(status_code, f"Error {status_code}")}

This might be because:
- The page has been removed
- The website is no longer active
- Access is restricted
- The server is experiencing issues

You can try:
- Checking if the website is still active
- Accessing the page directly in your browser
- Using a web archive service like the [Wayback Machine](https://web.archive.org/web/{url})
"""
    
    try:
        # Try multiple times with different user agents if needed
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        
        last_error = None
        for agent in user_agents:
            try:
                headers['User-Agent'] = agent
                response = requests.get(
                    url, 
                    headers=headers,
                    timeout=30,
                    verify=False,
                    allow_redirects=True
                )
                
                # Check for common error codes
                if response.status_code in [404, 403, 412, 500, 503, 504]:
                    return url, create_error_message(response.status_code, url)
                
                response.raise_for_status()
                break
            except requests.RequestException as e:
                last_error = e
                continue
        else:
            # If all attempts failed
            if last_error:
                raise last_error
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Get title
        title = soup.title.string if soup.title else url
        
        # Remove unwanted elements but preserve main content structure
        for element in soup.find_all(['script', 'iframe', 'noscript', 'style']):
            element.decompose()
            
        # Try to get main content
        main_content = None
        content_selectors = [
            'article', 'main', '#main', '#content', '.content', 
            '.article', '.post', '.entry-content', '[role="main"]'
        ]
        
        # Try each selector
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content and len(str(main_content)) > 100:  # Ensure we have substantial content
                break
        
        # Fallback to body if no main content found
        if not main_content:
            main_content = soup.find('body')
            if main_content:
                # Remove unwanted elements from body
                for tag in main_content.find_all(['header', 'footer', 'nav', 'script', 'style', 'iframe']):
                    tag.decompose()
        
        if main_content:
            # Convert content to readable text format
            content = h.handle(str(main_content))
            return title, content
        
        # If no content found, try to get the whole body text
        body_text = soup.get_text()
        if body_text.strip():
            return title, h.handle(body_text)
            
        return title, "No content found"
        
        if main_content:
            # Process links and images
            for tag in main_content.find_all(['a', 'img', 'link']):
                # Handle links
                if tag.name == 'a' and tag.get('href'):
                    tag['href'] = urljoin(url, tag['href'])
                    tag['target'] = '_blank'
                    tag['rel'] = 'noopener noreferrer'
                
                # Handle images
                elif tag.name == 'img':
                    if tag.get('src'):
                        tag['src'] = urljoin(url, tag['src'])
                    if tag.get('srcset'):
                        srcset = tag['srcset'].split(',')
                        new_srcset = []
                        for src in srcset:
                            parts = src.strip().split()
                            if len(parts) == 2:
                                new_srcset.append(f"{urljoin(url, parts[0])} {parts[1]}")
                        tag['srcset'] = ', '.join(new_srcset)
            
            # Preserve classes for styling but remove potentially problematic attributes
            for tag in main_content.find_all(True):
                # Keep only safe attributes
                allowed_attrs = {'class', 'id', 'src', 'href', 'alt', 'title', 'target', 'rel'}
                for attr in list(tag.attrs.keys()):
                    if attr not in allowed_attrs:
                        del tag[attr]
            
            content = str(main_content)
            return title, content
        
        return title, "No main content found"
        
    except (requests.Timeout, requests.TooManyRedirects, requests.RequestException, Exception) as e:
        # Try fetching from WARC file as fallback
        title, content, source = fetch_from_warc(url)
        if title and content:
            return title, f"""
### 📚 Archive Content

This content was retrieved from our local WARC archive.

---

{content}
"""
        
        # If WARC fetch also failed, show error
        status_code = e.response.status_code if hasattr(e, 'response') and e.response is not None else 0
        return url, f"""
### ⚠️ Content Not Available

**URL:** {url}
**Error:** {str(e)}

Live webpage access failed, and content was not found in local WARC archive.

You can try:
- Checking if the URL is correct
- Accessing the page directly in your browser
- Checking if the content exists in a different WARC file
"""

def verify_database():
    """Verify database exists and is accessible"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, 'webpage_analysis.db')
    
    if not os.path.exists(db_path):
        st.error(f"""
        Database file not found at: {db_path}
        
        Please ensure:
        1. You have run the NLP processor (main.py) first
        2. The database was created successfully
        3. The file has proper permissions
        
        Steps to populate database:
        1. Open terminal
        2. Run: python main.py
        3. Wait for processing to complete
        4. Restart this Streamlit app
        
        Current directory: {current_dir}
        """)
        return False, "Database file not found"
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            # Check tables
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND (name='webpages' OR name='webpage_similarities')
            """)
            tables = cursor.fetchall()
            if len(tables) < 2:
                st.error("Required database tables are missing!")
                return False, "Missing tables"
                
            # Check if tables have data
            cursor.execute('SELECT COUNT(*) FROM webpages')
            webpage_count = cursor.fetchone()[0]
            if webpage_count == 0:
                st.warning("""
                Database is empty! No webpage data found.
                
                To populate the database:
                1. Ensure your WARC file contains webpage data
                2. Run the NLP processor: python main.py
                3. Check the terminal for processing status
                4. Restart this Streamlit app after processing completes
                """)
                return False, "Empty database"
                
            return True, f"Database OK - Found {webpage_count} webpages"
    except sqlite3.Error as e:
        st.error(f"Database error: {str(e)}")
        return False, f"Database error: {str(e)}"

def show_database_stats():
    """Show database statistics in the sidebar"""
    with st.sidebar:
        st.subheader("Database Statistics")
        try:
            with sqlite3.connect(st.session_state.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Get webpage count
                cursor.execute('SELECT COUNT(*) FROM webpages')
                webpage_count = cursor.fetchone()[0]
                
                # Get similarity count
                cursor.execute('SELECT COUNT(*) FROM webpage_similarities')
                similarity_count = cursor.fetchone()[0]
                
                # Get content types
                cursor.execute('''
                    SELECT content_type, COUNT(*) 
                    FROM webpages 
                    GROUP BY content_type
                ''')
                content_types = cursor.fetchall()
                
                # Display stats
                st.metric("Total Webpages", f"{webpage_count:,}")
                st.metric("Similarity Links", f"{similarity_count:,}")
                
                if content_types:
                    st.write("**Content Types:**")
                    for ctype, count in content_types:
                        st.write(f"- {ctype}: {count:,}")
                        
        except Exception as e:
            st.error(f"Error loading stats: {str(e)}")

def show_search_results(results: List[tuple]):
    """Display search results with live webpage content"""
    if not results:
        return
    
    # Show the most relevant result at the top
    webpage_id, url, title, content_type = results[0]
    
    st.header("Most Relevant Result")
    with st.container():
        with st.spinner("Fetching webpage content..."):
            try:
                live_title, live_content = fetch_webpage_content(url)
                st.subheader(live_title)
                st.write(f"**URL:** {url}")
                st.write(f"**Type:** {content_type}")
                
                # Display the content in a clean format
                with st.expander("View Full Content", expanded=True):
                    st.markdown(live_content)
            except Exception as e:
                st.error(f"Error fetching content: {str(e)}")
    
    # Show similar pages
    st.subheader("Similar Pages")
    similar_pages = st.session_state.db_manager.get_similar_webpages(webpage_id, limit=5)
    if similar_pages:
        for similar in similar_pages:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    with st.spinner("Fetching similar page content..."):
                        try:
                            sim_title, sim_content = fetch_webpage_content(similar['url'])
                            st.markdown(f"#### {sim_title}")
                            with st.expander("View Content"):
                                st.markdown(sim_content)
                        except Exception as e:
                            st.error(f"Error fetching similar page: {str(e)}")
                with col2:
                    st.markdown(f"<div class='similarity-score'>Similarity: {similar['similarity']:.2f}</div>", 
                              unsafe_allow_html=True)
                st.divider()
    else:
        st.info("No similar pages found")
    
    # Show other search results
    if len(results) > 1:
        st.header("Other Results")
        for webpage_id, url, title, content_type in results[1:]:
            with st.expander(f"📄 {title or url}"):
                with st.spinner("Fetching content..."):
                    try:
                        other_title, other_content = fetch_webpage_content(url)
                        st.write(f"**URL:** {url}")
                        st.markdown(other_content)
                    except Exception as e:
                        st.error(f"Error fetching content: {str(e)}")

def show_search_and_browse():
    """Main search and browse interface"""
    if not verify_database():
        return

    # Create a two-column layout
    col1, col2 = st.columns([3, 2])
    
    # Search bar with auto-search
    search_query = st.text_input(
        "🔍 Search by URL, title, or content:",
        placeholder="Enter search term...",
        key="search_input"
    )
    
    # Add filters
    with st.expander("Advanced Search Options"):
        col1_filter, col2_filter = st.columns(2)
        with col1_filter:
            min_similarity = st.slider(
                "Minimum Similarity Score",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.1
            )
        with col2_filter:
            content_type_filter = st.multiselect(
                "Content Type",
                options=["html", "xml", "unknown"],
                default=["html", "xml"]
            )
    
    if search_query:
        try:
            with sqlite3.connect(st.session_state.db_manager.db_path) as conn:
                cursor = conn.cursor()
                query = '''
                    SELECT id, url, title, content_type
                    FROM webpages
                    WHERE url LIKE ? 
                       OR title LIKE ?
                    ORDER BY 
                        CASE 
                            WHEN title LIKE ? THEN 1
                            ELSE 2
                        END
                    LIMIT 15
                '''
                search_pattern = f'%{search_query}%'
                cursor.execute(query, (search_pattern,) * 3)
                results = cursor.fetchall()
                
                if results:
                    # Main result in left column
                    with col1:
                        show_main_result(results[0])
                    
                    # Other results in right column
                    with col2:
                        st.markdown("### Other Results")
                        st.markdown("""<div style='height: 10px'></div>""", unsafe_allow_html=True)
                        show_other_results(results[1:])
                else:
                    st.info("No matching pages found")
                    
        except Exception as e:
            st.error(f"Search failed: {str(e)}")

def show_main_result(result):
    """Display main search result with similar pages in a continuous feed"""
    webpage_id, url, title, content_type = result
    
    with st.container():
        st.markdown("""
        <div class="result-card main-result">
            <div class="result-header">🎯 Most Relevant Result</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.spinner("Loading content..."):
            try:
                live_title, live_content = fetch_webpage_content(url)
                
                # Create a webpage mirror container
                with st.container():
                    # Webpage header with title and link
                    st.markdown(f"""
                    <div class="webpage-header">
                        <h1 style="margin-bottom: 5px;">{live_title}</h1>
                        <div class="webpage-meta">
                            <a href="{url}" target="_blank" class="source-link">🔗 View Original Website</a>
                            <span class="content-type">{content_type}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display the content
                    st.markdown(live_content)
                
            except Exception as e:
                st.error(f"Error displaying content: {str(e)}")
    
    # Get and display similar pages in a continuous feed
    similar_pages = st.session_state.db_manager.get_similar_webpages(
        webpage_id, 
        limit=10,  # Increased limit for more content
        threshold=0.3  # Lower threshold for more results
    )
    
    if similar_pages:
        st.markdown("### 🔄 Related Content Feed")
        
        # Create continuous feed of related content
        for i, similar in enumerate(similar_pages):
            with st.container():
                st.markdown(f"""
                <div class="result-card related-content">
                    <div class="similarity-badge">
                        {similar['similarity']:.2f} Match Score
                    </div>
                """, unsafe_allow_html=True)
                
                try:
                    sim_title, sim_content = fetch_webpage_content(similar['url'])
                    
                    # Create an expandable card with preview
                    with st.expander(f"📄 {sim_title}", expanded=False):
                        st.markdown(f"""
                        <div class="webpage-meta">
                            <a href="{similar['url']}" target="_blank" class="source-link">🔗 View Original</a>
                            <span class="similarity-score">Similarity: {similar['similarity']:.2f}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        
                        st.markdown(sim_content)
                        
                except Exception as e:
                    st.error(f"Error loading related content: {str(e)}")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
        # Add load more button
        if len(similar_pages) >= 10:  # Show only if there might be more results
            if st.button("Load More Related Content"):
                # Implement pagination logic here
                pass
                
    else:
        st.info("No related content found. Try adjusting the similarity threshold in Advanced Search Options")

def show_other_results(results):
    """Display other search results in right column"""
    for webpage_id, url, title, content_type in results:
        with st.container():
            with st.expander(f"📄 {title or url}", expanded=False):
                with st.spinner("Fetching content..."):
                    try:
                        other_title, other_content = fetch_webpage_content(url)
                        st.write(f"**URL:** {url}")
                        st.markdown(other_content[:500] + "..." if len(other_content) > 500 else other_content)
                        if len(other_content) > 500:
                            st.markdown("[Show full content...]")
                    except Exception as e:
                        st.error(f"Error fetching content: {str(e)}")
            st.divider()

def show_analysis():
    """Show analysis visualizations"""
    st.subheader("📈 Content Analysis")
    
    try:
        with sqlite3.connect(st.session_state.db_manager.db_path) as conn:
            cursor = conn.cursor()
            
            # Content distribution
            cursor.execute('''
                SELECT content_type, COUNT(*) as count
                FROM webpages
                GROUP BY content_type
            ''')
            content_types = cursor.fetchall()
            
            if content_types:
                df = pd.DataFrame(content_types, columns=['Content Type', 'Count'])
                fig = px.pie(df, values='Count', names='Content Type', 
                            title='Content Distribution')
                st.plotly_chart(fig)
            
            # Similarity distribution
            cursor.execute('SELECT similarity_score FROM webpage_similarities')
            similarities = [row[0] for row in cursor.fetchall()]
            
            if similarities:
                fig = px.histogram(similarities, 
                                 title='Similarity Distribution',
                                 labels={'value': 'Similarity Score', 
                                        'count': 'Count'})
                st.plotly_chart(fig)
            
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")

def show_info():
    """Show information and database status"""
    st.subheader("ℹ️ About This Tool")
    st.write("""
    This tool analyzes webpage content from WARC files and shows relationships between pages.
    
    **Features:**
    - Full-text search of processed webpages
    - Content similarity analysis
    - Visualization of content types
    - Similarity relationship analysis
    """)
    
    st.subheader("🔧 Database Debug Information")
    if st.button("Check Database Status"):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, 'webpage_analysis.db')
        
        debug_info = {
            "Working Directory": current_dir,
            "Database Path": db_path,
            "File Exists": os.path.exists(db_path),
            "File Size": f"{os.path.getsize(db_path) / 1024:.2f} KB" if os.path.exists(db_path) else "N/A"
        }
        
        for key, value in debug_info.items():
            st.write(f"**{key}:** {value}")
        
        if os.path.exists(db_path):
            try:
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    # Check schema
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    st.write("\n**Database Tables:**")
                    for table in tables:
                        st.write(f"- `{table[0]}`")
                        cursor.execute(f"PRAGMA table_info({table[0]})")
                        columns = cursor.fetchall()
                        st.write("  Columns:")
                        for col in columns:
                            st.write(f"    - {col[1]} ({col[2]})")
                        cursor.execute(f"SELECT * FROM {table[0]} LIMIT 1")
                        row = cursor.fetchone()
                        if row:
                            st.write(f"  Sample row: {row}")
            except Exception as e:
                st.error(f"Debug check failed: {str(e)}")

def main():
    st.markdown('<h1 class="main-title">Webpage Analysis Explorer</h1>', 
                unsafe_allow_html=True)
    
    # Initialize and store database manager in session state
    st.session_state.db_manager = get_db_manager()
    if st.session_state.db_manager is None:
        st.error("""
        Database connection failed!
        
        Please check:
        1. The database file exists
        2. You have run the NLP processor first
        3. The processing completed successfully
        """)
        
        if st.button("Show Setup Instructions"):
            st.info("""
            **Setup Instructions:**
            
            1. Open terminal in your project directory
            2. Run the NLP processor:
               ```
               python main.py
               ```
            3. Wait for processing to complete
            4. Restart this Streamlit app
            
            If problems persist, check the terminal output for errors.
            """)
        st.stop()
    
    # Verify database has data
    is_valid, status = verify_database()
    if not is_valid:
        st.error(f"Database verification failed: {status}")
        st.stop()
    
    show_database_stats()
    
    tabs = st.tabs(["🔍 Search & Browse", "📊 Analysis", "ℹ️ Info"])
    
    with tabs[0]:
        show_search_and_browse()
    with tabs[1]:
        show_analysis()
    with tabs[2]:
        show_info()

if __name__ == "__main__":
    main()
