from typing import List, Dict, Any

class MockVectorDB:
    """
    نسخة مؤقتة لمحاكاة قاعدة بيانات Qdrant
    """
    def __init__(self):
        print("⚠️  MOCK DB INITIALIZED: Returning static data only.")

    def search_similar(self, vector: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
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
            }
        ]
        return mock_results[:top_k]