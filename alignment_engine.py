"""
alignment_engine.py
Backend module for BioAligner: FASTA parsing, scoring matrices,
Needleman-Wunsch pairwise alignment, and Star (Center) MSA.
Pure Python — no external dependencies.
"""

# ============================================================
# FASTA Parser
# ============================================================

def parse_fasta(text):
    """
    Parse FASTA-formatted text into a list of (name, sequence) tuples.
    Returns empty list if the text is not valid FASTA.
    """
    records = []
    current_name = None
    current_seq = []

    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('>'):
            # Save previous record
            if current_name is not None:
                records.append((current_name, ''.join(current_seq).upper()))
            current_name = line[1:].split()[0] if len(line) > 1 else "unnamed"
            current_seq = []
        else:
            current_seq.append(line.replace(' ', ''))

    # Save last record
    if current_name is not None:
        records.append((current_name, ''.join(current_seq).upper()))

    return records


# ============================================================
# BLOSUM62 Substitution Matrix
# ============================================================

_BLOSUM62_DATA = {
    ('A','A'): 4,('A','R'):-1,('A','N'):-2,('A','D'):-2,('A','C'): 0,
    ('A','Q'):-1,('A','E'):-1,('A','G'): 0,('A','H'):-2,('A','I'):-1,
    ('A','L'):-1,('A','K'):-1,('A','M'):-1,('A','F'):-2,('A','P'):-1,
    ('A','S'): 1,('A','T'): 0,('A','W'):-3,('A','Y'):-2,('A','V'): 0,
    ('R','R'): 5,('R','N'): 0,('R','D'):-2,('R','C'):-3,('R','Q'): 1,
    ('R','E'): 0,('R','G'):-2,('R','H'): 0,('R','I'):-3,('R','L'):-2,
    ('R','K'): 2,('R','M'):-1,('R','F'):-3,('R','P'):-2,('R','S'):-1,
    ('R','T'):-1,('R','W'):-3,('R','Y'):-2,('R','V'):-3,
    ('N','N'): 6,('N','D'): 1,('N','C'):-3,('N','Q'): 0,('N','E'): 0,
    ('N','G'): 0,('N','H'): 1,('N','I'):-3,('N','L'):-3,('N','K'): 0,
    ('N','M'):-2,('N','F'):-3,('N','P'):-2,('N','S'): 1,('N','T'): 0,
    ('N','W'):-4,('N','Y'):-2,('N','V'):-3,
    ('D','D'): 6,('D','C'):-3,('D','Q'): 0,('D','E'): 2,('D','G'):-1,
    ('D','H'):-1,('D','I'):-3,('D','L'):-4,('D','K'):-1,('D','M'):-3,
    ('D','F'):-3,('D','P'):-1,('D','S'): 0,('D','T'):-1,('D','W'):-4,
    ('D','Y'):-3,('D','V'):-3,
    ('C','C'): 9,('C','Q'):-3,('C','E'):-4,('C','G'):-3,('C','H'):-3,
    ('C','I'):-1,('C','L'):-1,('C','K'):-3,('C','M'):-1,('C','F'):-2,
    ('C','P'):-3,('C','S'):-1,('C','T'):-1,('C','W'):-2,('C','Y'):-2,
    ('C','V'):-1,
    ('Q','Q'): 5,('Q','E'): 2,('Q','G'):-2,('Q','H'): 0,('Q','I'):-3,
    ('Q','L'):-2,('Q','K'): 1,('Q','M'): 0,('Q','F'):-3,('Q','P'):-1,
    ('Q','S'): 0,('Q','T'):-1,('Q','W'):-2,('Q','Y'):-1,('Q','V'):-2,
    ('E','E'): 5,('E','G'):-2,('E','H'): 0,('E','I'):-3,('E','L'):-3,
    ('E','K'): 1,('E','M'):-2,('E','F'):-3,('E','P'):-1,('E','S'): 0,
    ('E','T'):-1,('E','W'):-3,('E','Y'):-2,('E','V'):-2,
    ('G','G'): 6,('G','H'):-2,('G','I'):-4,('G','L'):-4,('G','K'):-2,
    ('G','M'):-3,('G','F'):-3,('G','P'):-2,('G','S'): 0,('G','T'):-2,
    ('G','W'):-2,('G','Y'):-3,('G','V'):-3,
    ('H','H'): 8,('H','I'):-3,('H','L'):-3,('H','K'):-1,('H','M'):-2,
    ('H','F'):-1,('H','P'):-2,('H','S'):-1,('H','T'):-2,('H','W'):-2,
    ('H','Y'): 2,('H','V'):-3,
    ('I','I'): 4,('I','L'): 2,('I','K'):-3,('I','M'): 1,('I','F'): 0,
    ('I','P'):-3,('I','S'):-2,('I','T'):-1,('I','W'):-3,('I','Y'):-1,
    ('I','V'): 3,
    ('L','L'): 4,('L','K'):-2,('L','M'): 2,('L','F'): 0,('L','P'):-3,
    ('L','S'):-2,('L','T'):-1,('L','W'):-2,('L','Y'):-1,('L','V'): 1,
    ('K','K'): 5,('K','M'):-1,('K','F'):-3,('K','P'):-1,('K','S'): 0,
    ('K','T'):-1,('K','W'):-3,('K','Y'):-2,('K','V'):-2,
    ('M','M'): 5,('M','F'): 0,('M','P'):-2,('M','S'):-1,('M','T'):-1,
    ('M','W'):-1,('M','Y'):-1,('M','V'): 1,
    ('F','F'): 6,('F','P'):-4,('F','S'):-2,('F','T'):-2,('F','W'): 1,
    ('F','Y'): 3,('F','V'):-1,
    ('P','P'): 7,('P','S'):-1,('P','T'):-1,('P','W'):-4,('P','Y'):-3,
    ('P','V'):-2,
    ('S','S'): 4,('S','T'): 1,('S','W'):-3,('S','Y'):-2,('S','V'):-2,
    ('T','T'): 5,('T','W'):-2,('T','Y'):-2,('T','V'): 0,
    ('W','W'):11,('W','Y'): 2,('W','V'):-3,
    ('Y','Y'): 7,('Y','V'):-1,
    ('V','V'): 4,
}

# Build symmetric lookup
BLOSUM62 = {}
for (a, b), v in _BLOSUM62_DATA.items():
    BLOSUM62[(a, b)] = v
    BLOSUM62[(b, a)] = v


def blosum62_score(a, b):
    """Look up BLOSUM62 score; return -1 for unknown pairs."""
    return BLOSUM62.get((a, b), -1)


# ============================================================
# Needleman-Wunsch Pairwise Alignment
# ============================================================

def needleman_wunsch(seq1, seq2, gap_penalty=-2, score_fn=None):
    """
    Global pairwise alignment using Needleman-Wunsch with linear gap penalty.

    Parameters:
        seq1, seq2: sequences to align (strings)
        gap_penalty: penalty per gap (negative)
        score_fn: function(a, b) -> int score. If None, uses match=1/mismatch=-1.

    Returns:
        (aligned_seq1, aligned_seq2, alignment_score)
    """
    if score_fn is None:
        def score_fn(a, b):
            return 1 if a == b else -1

    n, m = len(seq1), len(seq2)

    # DP table
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i * gap_penalty
    for j in range(1, m + 1):
        dp[0][j] = j * gap_penalty

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i][j] = max(
                dp[i - 1][j - 1] + score_fn(seq1[i - 1], seq2[j - 1]),
                dp[i - 1][j] + gap_penalty,
                dp[i][j - 1] + gap_penalty,
            )

    # Traceback
    a1, a2 = [], []
    i, j = n, m
    while i > 0 or j > 0:
        if (i > 0 and j > 0
                and dp[i][j] == dp[i-1][j-1] + score_fn(seq1[i-1], seq2[j-1])):
            a1.append(seq1[i - 1])
            a2.append(seq2[j - 1])
            i -= 1; j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + gap_penalty:
            a1.append(seq1[i - 1])
            a2.append('-')
            i -= 1
        else:
            a1.append('-')
            a2.append(seq2[j - 1])
            j -= 1

    return ''.join(reversed(a1)), ''.join(reversed(a2)), dp[n][m]


# ============================================================
# Star (Center) Multiple Sequence Alignment
# ============================================================

def perform_msa(records, seq_type):
    """
    Multiple Sequence Alignment using the Star (Center) method.

    Progressive alignment mimicking Clustal-like behavior:
      1. Compute all pairwise scores → find center sequence
      2. Align every sequence to the center
      3. Merge pairwise alignments into a single MSA via the center anchor

    Parameters:
        records: list of (name, sequence) tuples
        seq_type: "DNA" or "Protein"

    Returns:
        list of (name, aligned_sequence) tuples in original order
    """
    names = [r[0] for r in records]
    seqs  = [r[1] for r in records]
    num   = len(seqs)

    # Scoring configuration
    if seq_type == "DNA":
        gap_pen = -3
        def score_fn(a, b):
            return 2 if a == b else -1
    else:
        gap_pen = -5
        score_fn = blosum62_score

    # Two sequences → direct pairwise
    if num == 2:
        a1, a2, _ = needleman_wunsch(seqs[0], seqs[1], gap_pen, score_fn)
        return [(names[0], a1), (names[1], a2)]

    # Step 1: pairwise scores → find center
    scores = [[0.0] * num for _ in range(num)]
    for i in range(num):
        for j in range(i + 1, num):
            _, _, sc = needleman_wunsch(seqs[i], seqs[j], gap_pen, score_fn)
            scores[i][j] = sc
            scores[j][i] = sc

    totals = [sum(row) for row in scores]
    center = totals.index(max(totals))
    center_seq = seqs[center]
    clen = len(center_seq)

    # Step 2: align all others to center
    pw = []  # (aligned_center, aligned_other, index)
    for i in range(num):
        if i == center:
            continue
        ac, ao, _ = needleman_wunsch(center_seq, seqs[i], gap_pen, score_fn)
        pw.append((ac, ao, i))

    # Step 3: master gap pattern
    gaps_before = [0] * (clen + 1)
    for ac, _, _ in pw:
        cpos = 0
        gc = 0
        for ch in ac:
            if ch == '-':
                gc += 1
            else:
                gaps_before[cpos] = max(gaps_before[cpos], gc)
                cpos += 1
                gc = 0
        gaps_before[clen] = max(gaps_before[clen], gc)

    # Step 4: build MSA
    master = []
    for i in range(clen):
        master.extend(['-'] * gaps_before[i])
        master.append(center_seq[i])
    master.extend(['-'] * gaps_before[clen])

    result = {center: ''.join(master)}

    for ac, ao, oi in pw:
        ns = []
        ap = 0
        for i in range(clen):
            mg = gaps_before[i]
            pg = 0
            while ap < len(ac) and ac[ap] == '-':
                pg += 1
                ap += 1
            for k in range(pg):
                ns.append(ao[ap - pg + k])
            ns.extend(['-'] * (mg - pg))
            ns.append(ao[ap])
            ap += 1

        mg = gaps_before[clen]
        pg = 0
        while ap < len(ac) and ac[ap] == '-':
            pg += 1
            ap += 1
        for k in range(pg):
            ns.append(ao[ap - pg + k])
        ns.extend(['-'] * (mg - pg))

        result[oi] = ''.join(ns)

    return [(names[i], result[i]) for i in range(num)]
