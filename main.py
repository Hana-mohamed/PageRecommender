from english_nlp_processor import EnglishWebpageProcessor
from simple_db_manager import SimpleWebpageDBManager

def main():
    # Initialize processors
    processor = EnglishWebpageProcessor('english.warc.gz')
    db_manager = SimpleWebpageDBManager()
    
    # Process webpages
    print("Processing WARC file...")
    processor.process_warc_file()
    
    # Save to database
    print("Saving to database...")
    webpage_ids = {}
    for i, page in enumerate(processor.processed_pages, 1):
        webpage_ids[i] = db_manager.add_webpage(page)
    
    # Calculate and save similarities
    print("Calculating similarities...")
    similarities = processor.calculate_similarities()
    
    # Map similarity indices to database IDs
    mapped_similarities = [
        (webpage_ids[i], webpage_ids[j], score)
        for i, j, score in similarities
        if i in webpage_ids and j in webpage_ids
    ]
    
    db_manager.add_similarities(mapped_similarities)
    
    # Test recommendation
    if processor.processed_pages:
        first_id = webpage_ids[1]
        similar_pages = db_manager.get_similar_webpages(first_id)
        
        print("\nExample recommendations:")
        print(f"For webpage: {processor.processed_pages[0]['url']}")
        print("\nSimilar pages:")
        for page in similar_pages:
            print(f"- {page['url']} (similarity: {page['similarity']:.2f})")

if __name__ == "__main__":
    main()