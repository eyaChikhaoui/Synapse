# File: src/utils/file_parser.py
import pandas as pd
import io
import re
import logging
from fastapi import UploadFile
from PyPDF2 import PdfReader # Standard lightweight PDF text extractor

logger = logging.getLogger("FileParser")

class FileParser:
    @staticmethod
    async def parse_upload(file: UploadFile) -> list[str]:
        """
        Main entry point. Determines file type and extracts sequences.
        Returns a list of clean string sequences.
        """
        filename = file.filename.lower()
        content = await file.read()
        sequences = []

        try:
            # 1. JSON Handling
            if filename.endswith('.json'):
                df = pd.read_json(io.BytesIO(content))
                sequences = FileParser._extract_from_df(df)

            # 2. CSV/Excel Handling
            elif filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(content))
                sequences = FileParser._extract_from_df(df)
            elif filename.endswith('.xlsx') or filename.endswith('.xls'):
                df = pd.read_excel(io.BytesIO(content))
                sequences = FileParser._extract_from_df(df)

            # 3. PDF Handling (Text Extraction + Regex Hunt)
            elif filename.endswith('.pdf'):
                text = FileParser._extract_text_from_pdf(io.BytesIO(content))
                sequences = FileParser._regex_hunt(text)

            # 4. FASTA / TXT Handling
            elif filename.endswith('.fasta') or filename.endswith('.txt') or filename.endswith('.fna'):
                text = content.decode('utf-8')
                # Split by newline, ignore headers starting with >
                lines = text.split('\n')
                buffer = ""
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    if line.startswith(">"):
                        if buffer: sequences.append(buffer)
                        buffer = ""
                    else:
                        buffer += line
                if buffer: sequences.append(buffer)

            else:
                logger.warning(f"Unsupported file type: {filename}")

        except Exception as e:
            logger.error(f"Parsing Error: {e}")
            return []
        
        # Final Cleanup: Remove duplicates and empty strings
        unique_seqs = list(set([s.upper().strip() for s in sequences if len(s.strip()) > 3]))
        logger.info(f"📂 Parsed {len(unique_seqs)} unique sequences from {filename}")
        return unique_seqs

    @staticmethod
    def _extract_from_df(df: pd.DataFrame) -> list[str]:
        """Smart column detection for DataFrames"""
        # Look for likely column names
        target_cols = ['sequence', 'seq', 'dna', 'protein', 'nucleotide', 'amino_acid']
        found_col = next((col for col in df.columns if col.lower() in target_cols), None)
        
        if found_col:
            return df[found_col].dropna().astype(str).tolist()
        
        # Fallback: If one column is significantly longer strings, use it
        # (Heuristic: DNA/Protein seqs are usually long strings without spaces)
        return []

    @staticmethod
    def _extract_text_from_pdf(file_stream) -> str:
        """Extracts raw text from PDF pages"""
        try:
            reader = PdfReader(file_stream)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"PDF Read Error: {e}")
            return ""

    @staticmethod
    def _regex_hunt(text: str) -> list[str]:
        """
        Scans unstructured text for patterns looking like DNA or Protein.
        """
        cleaned_text = text.replace('\n', '').replace(' ', '')
        sequences = []

        # 1. DNA Pattern: Long strings of ACGT (min length 10)
        dna_matches = re.findall(r'[ACGTN]{10,}', cleaned_text, re.IGNORECASE)
        sequences.extend(dna_matches)

        # 2. Protein Pattern: Long strings of Amino Acids (min length 10)
        # Excludes common English chars like B, J, O, U, X, Z to reduce false positives
        # (Though some are valid ambiguity codes, we prioritize noise reduction)
        prot_matches = re.findall(r'[ACDEFGHIKLMNPQRSTVWY]{10,}', cleaned_text, re.IGNORECASE)
        sequences.extend(prot_matches)

        return sequences