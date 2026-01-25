import re
import logging

# Setup local logger
logger = logging.getLogger("DataProcessor")
logging.basicConfig(level=logging.INFO)

class DataProcessor:
    """
    Person 1 (ML Lead) - Utility for cleaning and preparing biological data.
    Ensures that input sequences are valid before hitting the expensive Transformer models.
    """
    
    @staticmethod
    def clean_dna(sequence: str) -> str:
        """
        Removes whitespace, newlines, and non-base characters.
        Converts to uppercase.
        """
        # Remove anything that isn't A, C, G, T, or N (Unknown)
        cleaned = re.sub(r'[^ACGTNacgtn]', '', sequence).upper()
        
        if len(cleaned) == 0:
            logger.error("DNA Sequence is empty after cleaning!")
            raise ValueError("Invalid DNA sequence provided.")
            
        return cleaned

    @staticmethod
    def clean_protein(sequence: str) -> str:
        """
        Removes whitespace and validates against standard Amino Acid codes.
        """
        # Standard 20 amino acids + X (unknown)
        cleaned = re.sub(r'[^ACDEFGHIKLMNPQRSTVWYXacdefghiklmnpqrstvwyx]', '', sequence).upper()
        
        if len(cleaned) == 0:
            logger.error("Protein Sequence is empty after cleaning!")
            raise ValueError("Invalid Protein sequence provided.")
            
        return cleaned

    @staticmethod
    def generate_kmers(sequence: str, k: int = 6) -> str:
        """
        Sliding window k-merization. 
        Example (k=3): "ATGC" -> "ATG TGC"
        Many DNA models (like DNABERT) prefer k-mer strings over raw sequences.
        """
        return " ".join([sequence[i:i+k] for i in range(len(sequence) - k + 1)])

    @staticmethod
    def validate_length(sequence: str, max_len: int = 512):
        """
        Ensures the sequence fits within the model's context window.
        """
        if len(sequence) > max_len:
            logger.warning(f"Sequence length {len(sequence)} exceeds max {max_len}. Truncating.")
            return sequence[:max_len]
        return sequence

if __name__ == "__main__":
    # --- Quick Diagnostic ---
    dp = DataProcessor()
    
    raw_dna = "atg cgt acg tta g!!\n"
    clean_dna = dp.clean_dna(raw_dna)
    kmers = dp.generate_kmers(clean_dna, k=3)
    
    print("🧪 Data Processor Smoke Test:")
    print(f"Original DNA: {raw_dna.strip()}")
    print(f"Cleaned DNA:  {clean_dna}")
    print(f"K-mers (k=3): {kmers}")
    
    raw_prot = "give qcct sic s lyq len ycn"
    clean_prot = dp.clean_protein(raw_prot)
    print(f"Cleaned Prot: {clean_prot}")