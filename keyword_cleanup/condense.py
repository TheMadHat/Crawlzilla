import pandas as pd
import re

def extract_item(sentence):
  """
  Extracts the relevant item from a sentence.

  Args:
    sentence: The sentence to analyze.

  Returns:
    The extracted item, or None if no item is found.
  """
  # Match "What type of [item]" or "What [characteristic] [item]"
  match = re.search(r"(What type of|What [a-zA-Z]+) ([a-zA-Z ]+)", sentence)
  if match:
    return match.group(2).strip()

  # Match "The best [item]"
  match = re.search(r"The best ([a-zA-Z ]+)", sentence)
  if match:
    return match.group(1).strip()

  # Match "[item] [characteristic] is best"
  match = re.search(r"([a-zA-Z ]+) [a-zA-Z ]+ is best", sentence)
  if match:
    return match.group(1).strip()

  return None  # No item found

# Read the spreadsheet
df = pd.read_csv("lifestyle.csv") 

# Extract items and add them to a new column
df["extracted_item"] = df["Query"].apply(extract_item)

# Save the results
df.to_csv("extracted_items.csv", index=False)