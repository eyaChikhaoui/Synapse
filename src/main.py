import numpy as np
from encoders.dna_encoder import DNAEncoder
from encoders.protein_encoder import ProteinEncoder

class SynapseOrchestrator:
    """
    The Central AI Brain of Synapse.
    Managed by Person 1 (ML Lead).
    """
    def __init__(self):
        print("🚀 [Synapse] Initializing Multimodal Orchestrator...")
        self.dna_engine = DNAEncoder()
        self.protein_engine = ProteinEncoder()
        print("✅ [Synapse] All systems online. Shared Latent Space (768) active.")

    def process_sequence(self, sequence: str, mode: str = "dna"):
        """
        Routes a sequence to the correct encoder and returns the 768-dim vector.
        """
        mode = mode.lower()
        if mode == "dna":
            return self.dna_engine.get_vector(sequence)
        elif mode == "protein" or mode == "prot":
            return self.protein_engine.get_vector(sequence)
        else:
            raise ValueError("Invalid mode. Choose 'dna' or 'protein'.")

if __name__ == "__main__":
    # --- DAY 1 FINAL DEMO ---
    synapse = SynapseOrchestrator()
    
    # 1. Process DNA
    dna_seq = "ATGCGTACGTTAG"
    dna_vector = synapse.process_sequence(dna_seq, mode="dna")
    
    # 2. Process Protein
    prot_seq = "GIVEQCCTSICSLYQLENYCN"
    prot_vector = synapse.process_sequence(prot_seq, mode="protein")
    
    print("\n--- DAY 1 FINAL REPORT ---")
    print(f"🔹 DNA Input: {dna_seq} -> Vector({len(dna_vector)})")
    print(f"🔹 Protein Input: {prot_seq} -> Vector({len(prot_vector)})")
    
    # Cross-check
    if len(dna_vector) == len(prot_vector) == 768:
        print("\n🏆 STATUS: MISSION ACCOMPLISHED.")
        print("The Shared Latent Space is unified at 768 dimensions.")
    else:
        print("\n⚠️ STATUS: CRITICAL FAILURE. Dimension desync detected.")