import os
from mlte.session import set_context, set_store

def set_context_and_store():
    # Set up the path for where we are storing artifacts
    store_path = os.path.join(os.getcwd(), "store")
    os.makedirs(
        store_path, exist_ok=True
    )

    # Initialize the context
    set_context(namespace_id="MovieRecommendation",
                model_id='svd_recommender', 
                version_id="0.0.1")
    # Set the artifact storage path
    set_store(f"local://{store_path}")