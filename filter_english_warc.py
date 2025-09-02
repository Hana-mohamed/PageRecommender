import gzip
import zlib
import re
import string
from warcio.archiveiterator import ArchiveIterator
from langdetect import detect, LangDetectException
from warcio.warcwriter import WARCWriter
from io import BytesIO
from bs4 import BeautifulSoup

input_warc = 'sample.warc.gz'
output_warc = 'english.warc.gz'

def extract_text_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    # Remove scripts and styles
    for tag in soup(['script', 'style']):
        tag.decompose()
    return soup.get_text(separator=' ', strip=True)

def decompress_http_body_if_needed(body_bytes, http_headers):
	"""Return decompressed bytes based on HTTP Content-Encoding when present."""
	if not http_headers:
		return body_bytes
	encoding = http_headers.get_header('Content-Encoding')
	if not encoding:
		return body_bytes
	encoding = encoding.lower()
	try:
		if 'gzip' in encoding:
			return gzip.decompress(body_bytes)
		if 'deflate' in encoding:
			# Try raw deflate first, then zlib wrapper
			try:
				return zlib.decompress(body_bytes, -zlib.MAX_WBITS)
			except zlib.error:
				return zlib.decompress(body_bytes)
		# Unsupported encodings (e.g., br) – return as-is
		return body_bytes
	except Exception:
		# If decompression fails, fall back to original bytes
		return body_bytes

COMMON_EN_STOPWORDS = {
	"the","and","is","are","was","were","be","been","being","to","of","in","for","on","with","as","at","by","from",
	"that","this","it","an","a","or","if","not","can","will","would","should","could","about","into","over","after",
	"before","between","during","than","then","so","but","because","such","these","those","we","you","they","he","she",
	"his","her","our","your","their","have","has","had","do","does","did","all","any","some","no","more","most","other",
	"one","also","may","there","here","when","where","which","who","whom","what","how","why"
}

def looks_like_meaningful_english(text):
	"""Heuristic filter to reject gibberish/random character pages.

	Rules (all must pass):
	- Sufficient amount of words (>= 10)
	- Majority of letters are ASCII (>= 0.85)
	- Reasonable vowel ratio among letters (>= 0.25)
	- Contains some common English stopwords
	- Not dominated by non-printable or symbol characters
	"""
	if not text:
		return False

	# Normalize whitespace
	text_norm = re.sub(r"\s+", " ", text).strip()
	if len(text_norm) < 30:
		return False

	# Character statistics
	letters = sum(1 for c in text_norm if c.isalpha())
	ascii_letters = sum(1 for c in text_norm if c in string.ascii_letters)
	vowels = sum(1 for c in text_norm.lower() if c in "aeiou")
	total_chars = len(text_norm)
	printable_ascii = set(string.printable)
	non_printable = sum(1 for c in text_norm if c not in printable_ascii)

	if letters == 0:
		return False
	ascii_letter_ratio = ascii_letters / letters
	vowel_ratio = vowels / letters
	letter_density = letters / total_chars
	non_printable_ratio = non_printable / total_chars

	if ascii_letter_ratio < 0.85:
		return False
	if vowel_ratio < 0.25:
		return False
	if letter_density < 0.20:
		return False
	if non_printable_ratio > 0.15:
		return False

	# Token statistics
	words = re.findall(r"[A-Za-z]+", text_norm)
	if len(words) < 10:
		return False
	avg_len = sum(len(w) for w in words) / len(words)
	if avg_len < 3 or avg_len > 12:
		return False
	stopword_hits = sum(1 for w in words if w.lower() in COMMON_EN_STOPWORDS)
	if (stopword_hits / len(words)) < 0.01:
		return False

	return True

with gzip.open(input_warc, 'rb') as stream, gzip.open(output_warc, 'wb') as out_stream:
	writer = WARCWriter(out_stream, gzip=True)
	for record in ArchiveIterator(stream):
		if record.rec_type != 'response':
			continue

		payload = record.content_stream().read()
		http_headers = record.http_headers
		content_type = http_headers.get_header('Content-Type') if http_headers else None

		# Only process likely text-based content
		if content_type:
			ct_lower = content_type.lower()
			if (not ct_lower.startswith('text')) and ('html' not in ct_lower):
				continue

		# Decompress HTTP body if necessary before decoding/analysis
		body_bytes = decompress_http_body_if_needed(payload, http_headers)

		try:
			text = body_bytes.decode('utf-8', errors='ignore')
		except UnicodeDecodeError:
			text = body_bytes.decode('latin-1', errors='ignore')

		# If HTML, extract visible text content
		if content_type and 'html' in content_type.lower():
			text = extract_text_from_html(text)

		if not text or not text.strip():
			continue

		try:
			lang = detect(text)
		except (LangDetectException, UnicodeDecodeError):
			continue

		# Additional heuristic filter for gibberish
		if lang == 'en' and looks_like_meaningful_english(text):
			new_record = writer.create_warc_record(
				record.rec_headers.get_header('WARC-Target-URI'),
				'response',
				payload=BytesIO(payload),
				http_headers=record.http_headers
			)
			writer.write_record(new_record)