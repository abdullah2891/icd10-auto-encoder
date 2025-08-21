. ICD-10 Auto-Coder

What it does: User inputs a description like “Patient presents with chest pain and shortness of breath” → AI suggests possible ICD-10 codes with confidence levels.

Tech:

Use a pre-trained medical embeddings model (BioBERT, ClinicalBERT).

Fallback to LLM for text → code mapping.

PostgreSQL table to store mapping history.

Why it works: Demonstrates automation in medical coding, which ties directly to claims + insurance.
