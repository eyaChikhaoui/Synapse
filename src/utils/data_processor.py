import re
import logging

# Setup local logger
logger = logging.getLogger("DataProcessor")
logging.basicConfig(level=logging.INFO)

class DataProcessor:
    """
    Utility for cleaning and preparing biological data.
    Updated for NTv3 High-Performance Context Window.
    """
    
    @staticmethod
    def clean_dna(sequence: str) -> str:
        """
        Removes whitespace, newlines, and non-base characters.
        Converts to uppercase.
        """
        if not sequence:
            raise ValueError("Input sequence cannot be empty.")

        # Remove anything that isn't A, C, G, T, or N (Unknown)
        cleaned = re.sub(r'[^ACGTNacgtn]', '', sequence).upper()
        
        if len(cleaned) == 0:
            logger.error("DNA Sequence is empty after cleaning!")
            raise ValueError("Invalid DNA sequence provided. Must contain A, C, G, T, or N.")
            
        return cleaned

    @staticmethod
    def clean_protein(sequence: str) -> str:
        """
        Removes whitespace and validates against standard Amino Acid codes.
        """
        cleaned = re.sub(r'[^ACDEFGHIKLMNPQRSTVWYXacdefghiklmnpqrstvwyx]', '', sequence).upper()
        
        if len(cleaned) == 0:
            logger.error("Protein Sequence is empty after cleaning!")
            raise ValueError("Invalid Protein sequence provided.")
            
        return cleaned

    @staticmethod
    def validate_length(sequence: str, max_len: int = 2048):
        """
        Ensures the sequence fits within the NTv3 High-Performance context window.
        Old Limit: 512
        New Limit: 2048 (SOTA)
        """
        if len(sequence) > max_len:
            logger.warning(f"⚠️ Sequence length {len(sequence)} exceeds limit {max_len}. Truncating to fit model.")
            return sequence[:max_len]
        return sequence

if __name__ == "__main__":
    # Smoke Test
    dp = DataProcessor()
    test_seq = "A" * 3000
    valid_seq = dp.validate_length(test_seq)
    print(f"Original: 3000 -> Validated: {len(valid_seq)} (Should be 2048)")