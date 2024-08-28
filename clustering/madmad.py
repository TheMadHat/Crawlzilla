import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

# Step 1: Read the queries from the text file
with open('long_terms.txt', 'r') as file:
    queries = [line.strip() for line in file.readlines()]

# Step 2: Create a DataFrame
df = pd.DataFrame(queries, columns=['query'])

# Step 3: Calculate TF-IDF scores
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(df['query'])
tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=vectorizer.get_feature_names_out())

# Step 4: Extract the top 2 terms with the highest TF-IDF scores
def extract_top_keywords(row):
    top_keywords = row.nlargest(2).index.tolist()  # Find the top 2 terms
    return ', '.join(top_keywords)

df['top_keywords'] = tfidf_df.apply(extract_top_keywords, axis=1)

# Step 5: Save the result to a CSV file
output_file = 'top_keywords.csv'
df[['query', 'top_keywords']].to_csv(output_file, index=False)

print(f"Top keywords have been extracted and saved to {output_file}")
