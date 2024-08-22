import spacy

# Load spaCy's English model
nlp = spacy.load('en_core_web_sm')

def preprocess_text(text):
    """
    Preprocess a single text string by tokenizing, lemmatizing, and removing stopwords.
    """
    if isinstance(text, str):  # Ensure the input is a string
        doc = nlp(text.lower())
        tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
        return ' '.join(tokens)
    else:
        return ''  # Return an empty string if the input is not a string

def preprocess_keywords(keywords):
    """
    Apply preprocessing to a list of keywords.
    """
    print("Applying preprocessing to keywords...")
    return keywords.apply(preprocess_text)
