<<<<<<< HEAD
# TO-DO: Person 2 (Backend Lead) will write the code here

def search_similar(vector):
    """
    P2: Write your Qdrant search logic here.
    Input: Vector (list of floats)
    Output: List of dictionaries (protein names & scores)
    """
    # حالياً، هذا كود مؤقت
    # P2: امسح هذا واكتب كود الاتصال بـ Qdrant الحقيقي
    return [
        {"name": "Protein X (Demo)", "similarity": 0.99, "id": "P001"},
        {"name": "Protein Y (Demo)", "similarity": 0.85, "id": "P002"}
    ]
=======
from typing import List, Dict, Any

class MockVectorDB:
    """
    A temporary mock class to simulate Qdrant vector search behaviors
    during Day 1 development.
    """
    
    def __init__(self):
        print("⚠️  MOCK DB INITIALIZED: Returning static data only.")

    def search_similar(self, vector: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Simulates finding the nearest neighbors in the vector space.
        
        Args:
            vector (List[float]): The embedding vector (e.g., from Person 1's encoder).
            top_k (int): Number of results to return.

        Returns:
            List[Dict]: A list of mock protein 'payloads'.
        """
        # We ignore the input vector and return hardcoded data 
        # as requested in the To-Do List
        mock_results = [
            {
                "id": "P123", 
                "name": "Hemoglobin Subunit Alpha", 
                "function": "Oxygen Transport", 
                "score": 0.98
            },
            {
                "id": "P456", 
                "name": "Insulin", 
                "function": "Glucose Metabolism Regulation", 
                "score": 0.95
            },
            {
                "id": "P789", 
                "name": "Spike Protein (SARS-CoV-2)", 
                "function": "Viral Entry", 
                "score": 0.88
            }
        ]
        
        return mock_results[:top_k]

# Simple test to verify it works if run directly
if __name__ == "__main__":
    db = MockVectorDB()
    # Sending a fake vector of zeros just to test the interface
    fake_vector = [0.0] * 768 
    results = db.search_similar(fake_vector)
    print("Search Results:", results)
>>>>>>> 72f6233b6c18d5c0c844a9fd9ea1160810c80b74
