from process import preprocess_keywords
from cluster_map import perform_clustering, assign_cluster_labels
import pandas as pd

category_mapping = {
    'cars': ['cars', 'car rental', 'car insurance', 'car lease', 'GAP insurance', 'liability', 'car loan', 'car accident', 'car'],
    'credit score': ['FICO', 'credit score', 'experian', 'transunion', 'equifax', 'build credit', 'rebuild credit'],
    'mortgages': ['mortgages', 'mortgage', 'preapproval', 'home loan', 'home equity', 'debt', 'interest rates'],
    'banking': ['bank', 'bank', 'online banking', 'bank review', 'bank account', 'checking account', 'savings account', 'overdraft', 'cd'],
    'loans': ['personal loan', 'federal loan', 'private loan', 'student loan', 'home loan',],
    'credit cards': ['credit card', 'cash back cards', 'discover', 'american express', 'travel card', 'capital one', 'balance transfer']
}

def categorize_keyword(keyword):
    if isinstance(keyword, str):  # Ensure the keyword is a string
        keyword = keyword.lower()
        for category, keywords in category_mapping.items():
            for kw in keywords:
                if kw in keyword:  # Check if the keyword contains any of the predefined words
                    return category
    return 'other'  # Default category if no match is found or the keyword is not a string


def categorize_keywords(input_file, output_file, num_clusters=20):
    print("Loading data...")
    # Load the keywords from the CSV file
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} keywords")

    print("Categorizing keywords...")
    df['category'] = df['keyword'].apply(categorize_keyword)

    print("Preprocessing keywords...")
    # Preprocess the keywords
    df['processed_keyword'] = preprocess_keywords(df['keyword'])
    print("Preprocessing complete.")

    print("Performing clustering...")
    # Perform clustering
    X, clusters = perform_clustering(df['processed_keyword'], num_clusters)
    df['cluster'] = clusters
    print("Clustering complete.")

    # Assign category labels to the clusters
    print("Assigning category labels...")
    cluster_labels = {
        0: "Stock Market",
        1: "Cars",
        2: 'Credit Score',
        3: 'Mortgages',
        4: 'Banking',
        5: 'Loans',
        6: 'Credit Cards',
        7: 'Investing',
        8: 'Retirement',
        9: 'Real Estate',
        10: 'Insurance',
        11: 'Taxes',
        12: 'Budgeting',
        13: 'Savings',
        14: 'Debt',
        15: 'Financial Planning',
        16: 'Student Loans',
        17: 'Identity Theft',
        18: 'Small Business',
        19: 'Personal Finance',
        20: 'Other'
    }

    df['category'] = assign_cluster_labels(df['cluster'], cluster_labels)
    print("Category labels assigned.")

    print("Saving the results...")
    # Save the categorized keywords to a CSV file
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    categorize_keywords('keywords.csv', 'categorized_keywords.csv', num_clusters=20)
