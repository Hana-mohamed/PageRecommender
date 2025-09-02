# Webpage NLP Processor with Database Integration

A comprehensive Natural Language Processing module for analyzing webpage content from WARC (Web ARChive) files. This tool extracts, cleans, and analyzes webpage content to understand meaning and calculate similarities between webpages, storing results in a SQLite database for easy exploration via a Streamlit web interface. Optimized for fast content retrieval from local WARC archives.

## Features

### **Optimized WARC Processing**
- Direct WARC file access for faster content retrieval
- Smart caching of archived content
- Efficient HTML parsing with lxml
- English language content filtering and processing
- Intelligent content type detection

### **Content Cleaning & Preprocessing**
- HTML parsing and text extraction
- URL and email removal
- Special character cleaning
- Stopword removal (including web-specific stopwords)
- Text normalization and lemmatization

### **NLP Analysis**
- **Keyword Extraction**: Frequency-based keyword identification
- **Named Entity Recognition**: Person, organization, and location detection
- **Text Statistics**: Word count, sentence count, lexical diversity, etc.
- **Part-of-Speech Tagging**: Grammatical analysis of text

### **Similarity & Clustering**
- **TF-IDF Vectorization**: Convert text to numerical features
- **Cosine Similarity**: Calculate similarity between webpages
- **Topic Modeling**: LDA-based topic discovery
- **K-Means Clustering**: Group similar webpages together

### **Visualization & Reporting**
- Comprehensive analysis reports
- SQLite database storage
- Streamlit web interface for exploration
- Interactive visualizations with Plotly
- Statistical summaries and exports

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Required packages:**
   - `warcio`: WARC file processing (optimized archive reading)
   - `beautifulsoup4`: HTML parsing
   - `lxml`: Fast HTML parsing engine
   - `nltk`: Natural language processing
   - `scikit-learn`: Machine learning algorithms
   - `numpy` & `pandas`: Data manipulation
   - `matplotlib` & `seaborn`: Visualization
   - `streamlit`: Web interface
   - `plotly`: Interactive visualizations
   - `html2text`: Clean text conversion

## Quick Start

### Basic Usage

```python
from nlp_processor import WebpageNLPProcessor

# Initialize processor with your WARC file
processor = WebpageNLPProcessor('english.warc.gz')

# Extract webpage content
webpages = processor.extract_webpage_content()

# Process and analyze content
processed_data = processor.process_all_webpages()

# Calculate similarities
processor.create_tfidf_matrix()
processor.calculate_similarity_matrix()

# Find similar webpages
similar_pairs = processor.find_most_similar_pairs(5)
```

### Run Complete Analysis

```bash
# Run the main processor with database integration
python main.py

```

### Launch Streamlit Web Interface

```bash
# Start the web interface
streamlit run streamlit_app.py
```

## Performance Optimizations

### WARC File Access
The application prioritizes local WARC file access for content retrieval:
1. First attempts to fetch content from local WARC files
2. Falls back to live web access only if content is not found in WARC
3. Uses optimized HTML parsing with lxml for faster processing
4. Implements error handling and logging for better debugging

### Content Processing
- Efficient HTML parsing using lxml parser
- Smart content cleaning with BeautifulSoup
- Optimized text conversion with html2text
- Proper resource handling with context managers

## Detailed Usage Examples

### 1. Basic Content Analysis

```python
processor = WebpageNLPProcessor('english.warc.gz')
webpages = processor.extract_webpage_content()
processed_data = processor.process_all_webpages()

# View statistics for each webpage
for item in processed_data:
    print(f"URL: {item['url']}")
    print(f"Word count: {item['statistics']['word_count']}")
    print(f"Keywords: {item['keywords'][:5]}")
    print("---")
```

### 2. Similarity Analysis

```python
# Create TF-IDF matrix and calculate similarities
processor.create_tfidf_matrix()
processor.calculate_similarity_matrix()

# Find most similar webpage pairs
similar_pairs = processor.find_most_similar_pairs(10)
for i, j, similarity in similar_pairs:
    print(f"Similarity: {similarity:.3f}")
    print(f"  {processed_data[i]['url']}")
    print(f"  {processed_data[j]['url']}")
```

### 3. Topic Modeling

```python
# Discover topics in the content
topics, topic_weights = processor.perform_topic_modeling(5)

for topic in topics:
    print(f"Topic {topic['topic_id']}:")
    print(f"  Top words: {', '.join(topic['top_words'][:8])}")
```

### 4. Webpage Clustering

```python
# Cluster webpages by content similarity
clusters = processor.cluster_webpages(5)

# View cluster distribution
for i, cluster_id in enumerate(clusters):
    print(f"Webpage {i}: Cluster {cluster_id}")
```

## Output Files & Database

The processor generates several outputs:

- **`webpage_analysis.db`**: SQLite database with all analysis results
- **`webpage_similarity_heatmap.png`**: Visual similarity matrix
- **Console output**: Real-time analysis progress and results
- **Streamlit web interface**: Interactive exploration of results

## Configuration Options

### TF-IDF Parameters
```python
# Customize TF-IDF vectorization
processor.vectorizer = TfidfVectorizer(
    max_features=10000,      # Maximum features
    min_df=3,               # Minimum document frequency
    max_df=0.7,             # Maximum document frequency
    ngram_range=(1, 3)      # Unigrams, bigrams, trigrams
)
```

### Clustering Parameters
```python
# Adjust number of clusters
clusters = processor.cluster_webpages(n_clusters=10)
```

### Topic Modeling Parameters
```python
# Customize topic modeling
topics, weights = processor.perform_topic_modeling(n_topics=10)
```

## Advanced Features

### Custom Text Cleaning
```python
# Override default cleaning
def custom_cleaner(text):
    # Your custom cleaning logic
    return cleaned_text

processor.clean_text = custom_cleaner
```

### Extended Stopwords
```python
# Add domain-specific stopwords
processor.web_stopwords.update(['custom', 'domain', 'words'])
```

## Performance Considerations

- **Large WARC files**: Process in batches for memory efficiency
- **TF-IDF matrix**: Adjust `max_features` based on available memory
- **Clustering**: Use appropriate number of clusters for your dataset size

## Troubleshooting

### Common Issues

1. **NLTK data not found:**
   ```python
   import nltk
   nltk.download('punkt')
   nltk.download('stopwords')
   nltk.download('wordnet')
   ```

2. **Memory issues with large files:**
   - Reduce `max_features` in TF-IDF
   - Process webpages in smaller batches

3. **HTML parsing errors:**
   - Ensure `lxml` parser is installed
   - Check for malformed HTML in WARC records

### Error Handling

The processor includes comprehensive error handling:
- Graceful fallback for decoding issues
- Skip problematic records
- Detailed error logging

## API Reference

### WebpageNLPProcessorWithDB Class

#### Methods

- `extract_webpage_content()`: Extract content from WARC file
- `process_all_webpages()`: Clean and analyze all webpages
- `create_tfidf_matrix()`: Create TF-IDF feature matrix
- `calculate_similarity_matrix()`: Calculate webpage similarities
- `find_most_similar_pairs(k)`: Find top-k similar pairs
- `perform_topic_modeling(n_topics)`: Discover topics
- `cluster_webpages(n_clusters)`: Group similar webpages
- `save_to_database()`: Save results to SQLite database


### Database Management

The project includes two database manager implementations:

1. **SimpleDBManager** (`simple_db_manager.py`):
   - Lightweight database operations
   - Basic CRUD operations
   - Suitable for smaller datasets
   - Fast retrieval of webpage content

2. **FullDBManager** (`database_manager.py`):
   - Advanced database operations
   - Complex querying capabilities
   - Optimized for large datasets
   - Enhanced similarity tracking
   - Full-text search support

### WebpageDatabaseManager Class

#### Methods

- `add_webpage(webpage_data)`: Add webpage to database
- `add_similarity_relationships(pairs, id_map)`: Add similarity relationships
- `search_webpages(query, limit)`: Search webpages by URL/title
- `get_similar_webpages(webpage_id, limit, min_similarity)`: Get similar webpages
- `get_webpage_by_id(webpage_id)`: Get webpage details by ID
- `get_cluster_webpages(cluster_id, limit)`: Get webpages in a cluster
- `get_database_stats()`: Get comprehensive database statistics

## Streamlit Web Interface

The Streamlit app provides an interactive way to explore your NLP analysis results:

### Features
- **Dashboard**: Overview of database statistics and visualizations
- **Search**: Find webpages by URL or title
- **Similarity Analysis**: View similar webpages and clustering information
- **Database Statistics**: Detailed analysis and export capabilities

### Usage
1. Run the NLP processor: `python main.py`
2. Launch the web interface: `streamlit run streamlit_app.py`
3. Open your browser to the provided URL
4. Explore webpages, find similarities, and analyze clusters

## Utilities and Tools

### WARC Filtering (`filter_english_warc.py`)
Tool for filtering and processing WARC files:
- Extract English-language content
- Filter by content type
- Remove duplicate content
- Clean and normalize URLs

### Content Processing Tools
- `download_nltk_data.py`: Download required NLTK datasets
- 
## Testing

### Automated Tests
1. Installation Testing:
   ```bash
   python test_installation.py
   ```
   Verifies all dependencies and configurations.

2. Component Testing:
   - Database operations
   - WARC processing
   - NLP functionality
   - Content filtering

### Manual Testing
1. Sample Data Processing:
   ```bash
   python example_usage.py
   ```
   Processes sample data and verifies outputs.

2. Performance Testing:
   - Large WARC file processing
   - Database query optimization
   - Memory usage monitoring

## Contributing

Feel free to extend the processor with additional features:
- New text cleaning methods
- Additional similarity metrics (neo4j)
- More visualization options
- Performance optimizations
- Enhanced web interface features
- Support for additional languages
- Advanced filtering capabilities

## License

This project is open source

