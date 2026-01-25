class DNAController:
    @staticmethod
    async def process_analysis(dna_input: str):
        # 1. Clean the data
        seq = dna_input.strip().upper()

        # 2. Logic: Calculate GC Content
        if not seq:
            return {"error": "Sequence is empty"}, 400

        length = len(seq)

        # 3. Return raw data (JSON)
        return {
            "result": seq,
            "length":length
        }