import spacy

# Load the spaCy English model
nlp = spacy.load('en_core_web_sm')

def extract_category(text):
    """Extracts the base product category from a text string.

    Args:
        text: The input text string.

    Returns:
        A string representing the base category, or 'None' if no category is found.
    """
    doc = nlp(text)
    
    # Initialize an empty list to store relevant tokens
    relevant_tokens = []

    # Look for tokens that are either nouns or adjectives preceding "for" or other indicators
    for token in doc:
        if token.pos_ in ['NOUN', 'ADJ']:
            relevant_tokens.append(token.text)
        # Stop appending when the token is 'for' or any other indicator that a specific attribute is starting
        if token.text.lower() == 'for':
            break
    
    # Join the relevant tokens to form the base category
    core_phrase = ' '.join(relevant_tokens)
    
    # Return 'None' if the core phrase is the same as the original to avoid duplication
    if not core_phrase or core_phrase.lower() == text.lower():
        return "None"
    return core_phrase

# Read long terms from the input file
with open('long_terms.txt', 'r') as file:
    queries = [line.strip() for line in file.readlines()]

with open('core_terms.txt', 'w') as file:
    for query in queries:
        core_phrase = extract_category(query)
        file.write(query + '\n')
        file.write(core_phrase + '\n')

print("Extraction completed. Core terms have been saved to core_terms.txt.")
