import pandas as pd

def load_keywords(file_path):
    """
    Load keywords from a CSV file.
    """
    return pd.read_csv(file_path)

def save_results(df, file_path):
    """
    Save the resulting DataFrame to a CSV file.
    """
    df.to_csv(file_path, index=False)