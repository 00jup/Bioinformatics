#!/usr/bin/env python3
"""
BioAligner: DNA/Protein Multiple Sequence Alignment GUI
- No biopython required
- FASTA parsing: pure Python
- Alignment: Needleman-Wunsch (global) implemented from scratch
- MSA: Center-Star algorithm
- GUI: tkinter (standard library)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import io


# ─────────────────────────────────────────────────────────────────────────────
#  Substitution matrices & gap penalties
# ─────────────────────────────────────────────────────────────────────────────

# BLOSUM62 matrix (subset of common amino acids)
BLOSUM62 = {
    ('A','A'): 4,  ('A','R'):-1,  ('A','N'):-2,  ('A','D'):-2,  ('A','C'): 0,
    ('A','Q'):-1,  ('A','E'):-1,  ('A','G'): 0,  ('A','H'):-2,  ('A','I'):-1,
    ('A','L'):-1,  ('A','K'):-1,  ('A','M'):-1,  ('A','F'):-2,  ('A','P'):-1,
    ('A','S'): 1,  ('A','T'): 0,  ('A','W'):-3,  ('A','Y'):-2,  ('A','V'): 0,
    ('R','R'): 5,  ('R','N'):-0,  ('R','D'):-2,  ('R','C'):-3,  ('R','Q'): 1,
    ('R','E'): 0,  ('R','G'):-2,  ('R','H'): 0,  ('R','I'):-3,  ('R','L'):-2,
    ('R','K'): 2,  ('R','M'):-1,  ('R','F'):-3,  ('R','P'):-2,  ('R','S'):-1,
    ('R','T'):-1,  ('R','W'):-3,  ('R','Y'):-2,  ('R','V'):-3,
    ('N','N'): 6,  ('N','D'): 1,  ('N','C'):-3,  ('N','Q'): 0,  ('N','E'): 0,
    ('N','G'): 0,  ('N','H'): 1,  ('N','I'):-3,  ('N','L'):-3,  ('N','K'): 0,
    ('N','M'):-2,  ('N','F'):-3,  ('N','P'):-2,  ('N','S'): 1,  ('N','T'): 0,
    ('N','W'):-4,  ('N','Y'):-2,  ('N','V'):-3,
    ('D','D'): 6,  ('D','C'):-3,  ('D','Q'): 0,  ('D','E'): 2,  ('D','G'):-1,
    ('D','H'):-1,  ('D','I'):-3,  ('D','L'):-4,  ('D','K'):-1,  ('D','M'):-3,
    ('D','F'):-3,  ('D','P'):-1,  ('D','S'): 0,  ('D','T'):-1,  ('D','W'):-4,
    ('D','Y'):-3,  ('D','V'):-3,
    ('C','C'): 9,  ('C','Q'):-3,  ('C','E'):-4,  ('C','G'):-3,  ('C','H'):-3,
    ('C','I'):-1,  ('C','L'):-1,  ('C','K'):-3,  ('C','M'):-1,  ('C','F'):-2,
    ('C','P'):-3,  ('C','S'):-1,  ('C','T'):-1,  ('C','W'):-2,  ('C','Y'):-2,
    ('C','V'):-1,
    ('Q','Q'): 5,  ('Q','E'): 2,  ('Q','G'):-2,  ('Q','H'): 0,  ('Q','I'):-3,
    ('Q','L'):-2,  ('Q','K'): 1,  ('Q','M'): 0,  ('Q','F'):-3,  ('Q','P'):-1,
    ('Q','S'): 0,  ('Q','T'):-1,  ('Q','W'):-2,  ('Q','Y'):-1,  ('Q','V'):-2,
    ('E','E'): 5,  ('E','G'):-2,  ('E','H'): 0,  ('E','I'):-3,  ('E','L'):-3,
    ('E','K'): 1,  ('E','M'):-2,  ('E','F'):-3,  ('E','P'):-1,  ('E','S'): 0,
    ('E','T'):-1,  ('E','W'):-3,  ('E','Y'):-2,  ('E','V'):-2,
    ('G','G'): 6,  ('G','H'):-2,  ('G','I'):-4,  ('G','L'):-4,  ('G','K'):-2,
    ('G','M'):-3,  ('G','F'):-3,  ('G','P'):-2,  ('G','S'): 0,  ('G','T'):-2,
    ('G','W'):-2,  ('G','Y'):-3,  ('G','V'):-3,
    ('H','H'): 8,  ('H','I'):-3,  ('H','L'):-3,  ('H','K'):-1,  ('H','M'):-2,
    ('H','F'):-1,  ('H','P'):-2,  ('H','S'):-1,  ('H','T'):-2,  ('H','W'):-2,
    ('H','Y'): 2,  ('H','V'):-3,
    ('I','I'): 4,  ('I','L'): 2,  ('I','K'):-1,  ('I','M'): 1,  ('I','F'): 0,
    ('I','P'):-3,  ('I','S'):-2,  ('I','T'):-1,  ('I','W'):-3,  ('I','Y'):-1,
    ('I','V'): 3,
    ('L','L'): 4,  ('L','K'):-2,  ('L','M'): 2,  ('L','F'): 0,  ('L','P'):-3,
    ('L','S'):-2,  ('L','T'):-1,  ('L','W'):-2,  ('L','Y'):-1,  ('L','V'): 1,
    ('K','K'): 5,  ('K','M'):-1,  ('K','F'):-3,  ('K','P'):-1,  ('K','S'): 0,
    ('K','T'):-1,  ('K','W'):-3,  ('K','Y'):-2,  ('K','V'):-2,
    ('M','M'): 5,  ('M','F'): 0,  ('M','P'):-2,  ('M','S'):-1,  ('M','T'):-1,
    ('M','W'):-1,  ('M','Y'):-1,  ('M','V'): 1,
    ('F','F'): 6,  ('F','P'):-4,  ('F','S'):-2,  ('F','T'):-2,  ('F','W'): 1,
    ('F','Y'): 3,  ('F','V'):-1,
    ('P','P'): 7,  ('P','S'):-1,  ('P','T'):-1,  ('P','W'):-4,  ('P','Y'):-3,
    ('P','V'):-2,
    ('S','S'): 4,  ('S','T'): 1,  ('S','W'):-3,  ('S','Y'):-2,  ('S','V'):-2,
    ('T','T'): 5,  ('T','W'):-2,  ('T','Y'):-2,  ('T','V'): 0,
    ('W','W'):11,  ('W','Y'): 2,  ('W','V'):-3,
    ('Y','Y'): 7,  ('Y','V'):-1,
    ('V','V'): 4,
}

def blosum62_score(a, b):
    """Look up BLOSUM62 score (symmetric)."""
    a, b = a.upper(), b.upper()
    if a == b:
        return BLOSUM62.get((a, a), 0)
    return BLOSUM62.get((a, b), BLOSUM62.get((b, a), -1))

# Valid character sets
DNA_VALID    = set("ACGTNRYSWKMBDHVacgtnryswkmbdhv-")
PROTEIN_VALID = set("ACDEFGHIKLMNPQRSTVWYBZXacdefghiklmnpqrstvwybzx*-")


# ─────────────────────────────────────────────────────────────────────────────
#  FASTA parser (pure Python)
# ─────────────────────────────────────────────────────────────────────────────

def parse_fasta(text):
    """Parse FASTA text; return list of (id, sequence) tuples."""
    records = []
    current_id = None
    current_seq = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if current_id is not None:
                records.append((current_id, "".join(current_seq)))
            current_id = line[1:].split()[0]  # first word after >
            current_seq = []
        else:
            current_seq.append(line)
    if current_id is not None:
        records.append((current_id, "".join(current_seq)))
    return records


# ─────────────────────────────────────────────────────────────────────────────
#  Needleman-Wunsch global alignment
# ─────────────────────────────────────────────────────────────────────────────

def needleman_wunsch(seq1, seq2, seq_type="DNA"):
    """
    Global pairwise alignment using Needleman-Wunsch.
    Returns (aligned_seq1, aligned_seq2, score).
    """
    GAP_OPEN   = -2  if seq_type == "DNA" else -10
    GAP_EXTEND = -0.5

    def gap_penalty(n):
        return GAP_OPEN + GAP_EXTEND * (n - 1)

    def match(a, b):
        if seq_type == "DNA":
            return 2 if a.upper() == b.upper() else -1
        return blosum62_score(a, b)

    n, m = len(seq1), len(seq2)
    # Simple affine-gap DP with 3 matrices: M, IX (gap in seq1), IY (gap in seq2)
    NEG_INF = float('-inf')
    M  = [[NEG_INF] * (m + 1) for _ in range(n + 1)]
    IX = [[NEG_INF] * (m + 1) for _ in range(n + 1)]
    IY = [[NEG_INF] * (m + 1) for _ in range(n + 1)]

    M[0][0] = 0
    for i in range(1, n + 1):
        IX[i][0] = GAP_OPEN + GAP_EXTEND * (i - 1)
    for j in range(1, m + 1):
        IY[0][j] = GAP_OPEN + GAP_EXTEND * (j - 1)

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = match(seq1[i-1], seq2[j-1])
            M[i][j]  = max(M[i-1][j-1], IX[i-1][j-1], IY[i-1][j-1]) + s
            IX[i][j] = max(M[i-1][j]  + GAP_OPEN,
                           IX[i-1][j] + GAP_EXTEND,
                           IY[i-1][j] + GAP_OPEN)
            IY[i][j] = max(M[i][j-1]  + GAP_OPEN,
                           IX[i][j-1] + GAP_OPEN,
                           IY[i][j-1] + GAP_EXTEND)

    # Traceback
    a1, a2 = [], []
    i, j = n, m
    # Determine best terminal state
    terminal = max((M[n][m], 'M'), (IX[n][m], 'X'), (IY[n][m], 'Y'))
    score = terminal[0]
    state = terminal[1]

    while i > 0 or j > 0:
        if state == 'M':
            a1.append(seq1[i-1])
            a2.append(seq2[j-1])
            s = match(seq1[i-1], seq2[j-1])
            prev = max((M[i-1][j-1], 'M'), (IX[i-1][j-1], 'X'), (IY[i-1][j-1], 'Y'))
            state = prev[1]
            i -= 1; j -= 1
        elif state == 'X':
            a1.append(seq1[i-1])
            a2.append('-')
            prev = max((M[i-1][j] + GAP_OPEN,  'M'),
                       (IX[i-1][j] + GAP_EXTEND,'X'),
                       (IY[i-1][j] + GAP_OPEN,  'Y'))
            state = prev[1]
            i -= 1
        else:  # 'Y'
            a1.append('-')
            a2.append(seq2[j-1])
            prev = max((M[i][j-1] + GAP_OPEN,  'M'),
                       (IX[i][j-1] + GAP_OPEN,  'X'),
                       (IY[i][j-1] + GAP_EXTEND,'Y'))
            state = prev[1]
            j -= 1

    return ''.join(reversed(a1)), ''.join(reversed(a2)), score


def alignment_score(seq1, seq2, seq_type="DNA"):
    """Quick score without full traceback (reuse NW score return)."""
    _, _, score = needleman_wunsch(seq1, seq2, seq_type)
    return score


# ─────────────────────────────────────────────────────────────────────────────
#  Center-Star MSA
# ─────────────────────────────────────────────────────────────────────────────

def center_star_msa(seqs, ids, seq_type="DNA"):
    """
    Perform center-star multiple sequence alignment.
    Returns list of (id, aligned_sequence) tuples.
    """
    n = len(seqs)

    if n == 2:
        a1, a2, _ = needleman_wunsch(seqs[0], seqs[1], seq_type)
        return [(ids[0], a1), (ids[1], a2)]

    # Find center: sequence with highest total pairwise score
    total_scores = [0.0] * n
    for i in range(n):
        for j in range(i + 1, n):
            s = alignment_score(seqs[i], seqs[j], seq_type)
            total_scores[i] += s
            total_scores[j] += s
    center = total_scores.index(max(total_scores))

    # Pairwise align each sequence to center
    pairs = []  # (center_gapped, seq_gapped)
    for i in range(n):
        if i == center:
            pairs.append((seqs[center], seqs[center]))
        else:
            ca, sa, _ = needleman_wunsch(seqs[center], seqs[i], seq_type)
            pairs.append((ca, sa))

    # Build max-gap profile
    orig_len  = len(seqs[center])
    max_gaps  = _compute_max_gaps(pairs, orig_len)

    # Expand each sequence to master
    result = []
    for i in range(n):
        expanded = _expand_to_master(pairs[i][0], pairs[i][1], max_gaps, orig_len)
        result.append((ids[i], expanded))
    return result


def _compute_max_gaps(pairs, orig_len):
    """For each original center position, find maximum gaps inserted across alignments."""
    max_gaps = [0] * (orig_len + 1)
    for center_aln, _ in pairs:
        j = 0
        gap_count = 0
        for ch in center_aln:
            if ch == '-':
                gap_count += 1
            else:
                if gap_count > max_gaps[j]:
                    max_gaps[j] = gap_count
                gap_count = 0
                j += 1
        if gap_count > max_gaps[orig_len]:
            max_gaps[orig_len] = gap_count
    return max_gaps


def _expand_to_master(center_aln, other_aln, max_gaps, orig_len):
    """Expand other_aln to fit the master (merged-gap) alignment."""
    insert_before = []  # insertions before each center residue
    match_char    = []
    current_ins   = []

    for cc, oc in zip(center_aln, other_aln):
        if cc == '-':
            current_ins.append(oc)
        else:
            insert_before.append(current_ins[:])
            match_char.append(oc)
            current_ins = []
    insert_after = current_ins

    result = []
    for j in range(orig_len):
        ins    = insert_before[j] if j < len(insert_before) else []
        result.extend(ins)
        result.extend(['-'] * (max_gaps[j] - len(ins)))
        result.append(match_char[j] if j < len(match_char) else '-')

    result.extend(insert_after)
    result.extend(['-'] * (max_gaps[orig_len] - len(insert_after)))
    return ''.join(result)


# ─────────────────────────────────────────────────────────────────────────────
#  GUI Application
# ─────────────────────────────────────────────────────────────────────────────

class BioAlignerApp:
    BLOCK_SIZE = 60

    def __init__(self, root):
        self.root = root
        self.root.title("BioAligner: DNA/Protein Sequence Alignment")
        self.root.geometry("960x800")
        self.root.minsize(700, 600)
        self.seq_type = tk.StringVar(value="DNA")
        self._build_gui()

    # ── GUI layout ──────────────────────────────────────────────────────────

    def _build_gui(self):
        # Top section: Input
        input_lf = ttk.LabelFrame(
            self.root, text="Input sequences in FASTA format (2 or more):"
        )
        input_lf.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 4))

        self.input_text = scrolledtext.ScrolledText(
            input_lf, height=12, font=("Courier", 11), wrap=tk.NONE
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # Insert example placeholder
        self.input_text.insert(
            tk.END,
            ">Seq1\nATGCGATCGATCGATCGATCG\n>Seq2\nATGCGATCCATCGATCGATAG\n>Seq3\nATGCGATCGATCCAACGATCG\n"
        )

        # Middle section: Controls
        ctrl_frame = ttk.Frame(self.root)
        ctrl_frame.pack(fill=tk.X, padx=10, pady=4)

        ttk.Label(ctrl_frame, text="Sequence Type:").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Radiobutton(
            ctrl_frame, text="DNA", variable=self.seq_type, value="DNA"
        ).pack(side=tk.LEFT)
        ttk.Radiobutton(
            ctrl_frame, text="Protein", variable=self.seq_type, value="Protein"
        ).pack(side=tk.LEFT, padx=(4, 20))
        ttk.Button(
            ctrl_frame, text="Run Alignment", command=self.run_alignment
        ).pack(side=tk.LEFT)

        # Bottom section: Output
        output_lf = ttk.LabelFrame(self.root, text="Alignment Results:")
        output_lf.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 10))

        self.output_text = scrolledtext.ScrolledText(
            output_lf, height=18, font=("Courier", 11),
            state=tk.DISABLED, wrap=tk.NONE
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.output_text.tag_configure(
            "match_highlight", background="red", foreground="white"
        )

    # ── Alignment handler ────────────────────────────────────────────────────

    def run_alignment(self):
        raw = self.input_text.get("1.0", tk.END).strip()

        # Step 2a: Parse FASTA
        try:
            records = parse_fasta(raw)
        except Exception as e:
            messagebox.showerror(
                "Invalid Input",
                f"Please ensure data is in valid FASTA format.\n{e}"
            )
            return

        if not records:
            messagebox.showerror(
                "Invalid Input",
                "Please ensure data is in valid FASTA format."
            )
            return

        # Step 2b: Minimum count
        if len(records) < 2:
            messagebox.showerror(
                "Insufficient Data",
                "Please provide at least 2 sequences for alignment."
            )
            return

        # Step 2c: Sequence type validation
        seq_type = self.seq_type.get()
        valid_set = DNA_VALID if seq_type == "DNA" else PROTEIN_VALID
        for seq_id, seq in records:
            bad = set(seq) - valid_set
            if bad:
                messagebox.showerror(
                    "Type Mismatch",
                    f"Sequence '{seq_id}' contains invalid {seq_type} "
                    f"characters: {''.join(sorted(bad))}"
                )
                return

        # Step 2d: Run alignment (may be slow for long sequences — shown in status)
        ids  = [r[0] for r in records]
        seqs = [r[1] for r in records]

        try:
            aligned = center_star_msa(seqs, ids, seq_type)
        except Exception as e:
            messagebox.showerror("Alignment Error", str(e))
            return

        self._display_results(aligned)

    # ── Output formatter ─────────────────────────────────────────────────────

    def _display_results(self, aligned):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)

        ids  = [a[0] for a in aligned]
        seqs = [a[1] for a in aligned]

        aln_len = max(len(s) for s in seqs)
        seqs = [s.ljust(aln_len, '-') for s in seqs]

        # Find 100% identity columns (all same, no gaps)
        identity_cols = set()
        for col in range(aln_len):
            chars = [s[col].upper() for s in seqs]
            if '-' not in chars and len(set(chars)) == 1:
                identity_cols.add(col)

        id_width = max(len(i) for i in ids) + 2

        # Header
        self.output_text.insert(
            tk.END,
            f"Multiple Sequence Alignment  |  {len(aligned)} sequences  |  "
            f"Length: {aln_len} columns\n"
            + "=" * 80 + "\n\n"
        )

        for block_start in range(0, aln_len, self.BLOCK_SIZE):
            block_end = min(block_start + self.BLOCK_SIZE, aln_len)

            # Position ruler
            ruler = [' '] * (id_width + block_end - block_start)
            for col in range(block_start, block_end):
                pos = col + 1
                if pos % 10 == 0:
                    marker = str(pos)
                    rp = id_width + (col - block_start) - len(marker) + 1
                    for k, ch in enumerate(marker):
                        if 0 <= rp + k < len(ruler):
                            ruler[rp + k] = ch
            self.output_text.insert(tk.END, ''.join(ruler) + "\n")

            # Each sequence line
            for seq_id, seq in zip(ids, seqs):
                self.output_text.insert(tk.END, seq_id.ljust(id_width))
                for i, char in enumerate(seq[block_start:block_end]):
                    col = block_start + i
                    if col in identity_cols:
                        self.output_text.insert(tk.END, char, "match_highlight")
                    else:
                        self.output_text.insert(tk.END, char)
                self.output_text.insert(tk.END, "\n")

            self.output_text.insert(tk.END, "\n")

        self.output_text.config(state=tk.DISABLED)


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app = BioAlignerApp(root)
    root.mainloop()
