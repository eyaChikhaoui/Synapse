import numpy as np
import json
from datetime import datetime

class MockEncoder:
    """
    نسخة مؤقتة لمحاكاة موديل الذكاء الاصطناعي
    """
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        print(f"[MockEncoder] Initialized with Dimension: {self.dimension}")

    def encode(self, sequence: str) -> np.ndarray:
        # توليد أرقام ثابتة بناءً على طول السلسلة للمحاكاة
        np.random.seed(len(sequence))
        embedding = np.random.randn(self.dimension).astype(np.float32)
        norm = np.linalg.norm(embedding)
        return embedding / norm