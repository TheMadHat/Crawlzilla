from process import preprocess_keywords
from cluster_map import perform_clustering, assign_cluster_labels
import pandas as pd

def categorize_keywords(input_file, output_file, num_clusters=20):
    print("Loading data...")
    # Load the keywords from the CSV file
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} keywords")

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
        0: "Category 1",
        1: "Category 2",
        # Add more labels as needed
    }
    df['category'] = assign_cluster_labels(df['cluster'], cluster_labels)
    print("Category labels assigned.")

    print("Saving the results...")
    # Save the categorized keywords to a CSV file
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    categorize_keywords('keywords.csv', 'categorized_keywords.csv', num_clusters=20)
