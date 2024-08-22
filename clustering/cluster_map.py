from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

def perform_clustering(processed_keywords, num_clusters=20):
    """
    Perform K-Means clustering on the processed keywords.
    """
    print("Vectorizing keywords with TF-IDF...")
    vectorizer = TfidfVectorizer(max_features=1000)
    X = vectorizer.fit_transform(processed_keywords)
    
    print("Performing K-Means clustering...")
    kmeans = KMeans(n_clusters=num_clusters, random_state=0)
    clusters = kmeans.fit_predict(X)
    
    return X, clusters

def assign_cluster_labels(clusters, cluster_labels):
    """
    Map cluster numbers to human-readable category labels.
    """
    print("Mapping cluster numbers to labels...")
    return clusters.map(cluster_labels)
