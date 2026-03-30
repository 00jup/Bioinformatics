# Slide 215 : DNA → Reverse Complement Sequence
# Reverse Complement Sequence
# DNA 서열의 역보수(Reverse Complement)를 구하는 과정
# Complement: A↔T, G↔C 치환 후 전체 서열을 역순으로 반전


def reverse_complement(dna_sequence):
    # Complement: A↔T, G↔C 치환
    complement_map = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
    complement_sequence = ''.join(complement_map.get(base, base) for base in dna_sequence.upper())
    
    # Reverse: 서열을 역순으로 반전
    return complement_sequence[::-1]


# 실행 예시
dna = "ATGCTAGCTTAGC"
rev_comp = reverse_complement(dna)

print(f"DNA: {dna}")
print(f"Reverse Complement: {rev_comp}")
