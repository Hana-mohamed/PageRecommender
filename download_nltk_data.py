#!/usr/bin/env python3
import nltk
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

def download_nltk_data():
    print("Downloading required NLTK data...")
    
    # required NLTK data
    required_data = [
        'punkt',
        'stopwords', 
        'wordnet',
        'averaged_perceptron_tagger'
    ]
    
    for data_name in required_data:
        try:
            print(f"Downloading {data_name}...")
            nltk.download(data_name)
            print(f"✓ {data_name} downloaded successfully")
        except Exception as e:
            print(f"✗ Failed to download {data_name}: {e}")
    
    try:
        print("Downloading averaged_perceptron_tagger_eng...")
        nltk.download('averaged_perceptron_tagger_eng')
        print("✓ averaged_perceptron_tagger_eng downloaded successfully")
    except Exception as e:
        print(f"Note: averaged_perceptron_tagger_eng not available: {e}")
    
    print("\nNLTK data download completed!")
    print("You can now run the NLP processor.")

if __name__ == "__main__":
    download_nltk_data()
