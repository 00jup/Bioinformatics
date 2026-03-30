# Slide 214: DNA → RNA Transcription
# DNA의 T(Thymine)를 U(Uracil)로 치환하는 전사(Transcription) 과정

def dna_to_rna(dna_sequence):
    # Slide 214: T → U 치환 (전사 규칙)
    return dna_sequence.upper().replace("T", "U")


# 실행 예시
dna = "ATGCTAGCTTAGC"
rna = dna_to_rna(dna)

print(f"DNA: {dna}")
print(f"RNA: {rna}")
