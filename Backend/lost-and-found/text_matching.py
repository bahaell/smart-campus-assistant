from sentence_transformers import SentenceTransformer, util

class TextMatcher:
    def __init__(self):
        """
        Initialize SentenceTransformer model for text similarity.
        Uses all-MiniLM-L6-v2 model for embedding generation.
        """
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def compute_similarity(self, desc1, desc2):
        """
        Compute cosine similarity between two descriptions.
        Args:
            desc1 (str): First description.
            desc2 (str): Second description.
        Returns:
            float: Cosine similarity score (0 to 1).
        """
        # Encode descriptions
        embeddings = self.model.encode([desc1, desc2], convert_to_tensor=True)
        # Compute cosine similarity
        similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
        return similarity

if __name__ == "__main__":
    # Example usage
    matcher = TextMatcher()
    sim = matcher.compute_similarity("Blue backpack with laptop", "Navy blue backpack")
    print(f"Similarity: {sim}")