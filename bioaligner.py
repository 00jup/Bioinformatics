#!/usr/bin/env python3
"""
BioAligner: DNA/Protein Sequence Alignment
Tkinter GUI application for multiple sequence alignment.
No external dependencies — pure Python + tkinter.
"""

import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

from alignment_engine import parse_fasta, perform_msa


# Valid characters per sequence type
DNA_VALID = set("ACGTN")
PROTEIN_VALID = set("ACDEFGHIKLMNPQRSTVWYBZXUO*")


class BioAlignerApp:
    """Main GUI application."""

    def __init__(self, root):
        self.root = root
        self.root.title("BioAligner: DNA/Protein Sequence Alignment")
        self.root.geometry("950x750")
        self.root.minsize(750, 550)
        self._build_gui()

    # ----------------------------------------------------------------
    # GUI Construction
    # ----------------------------------------------------------------
    def _build_gui(self):
        # ---- Top: FASTA Input ----
        inp = tk.Frame(self.root)
        inp.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

        tk.Label(
            inp, text="Input sequences in FASTA format (2 or more):",
            font=("Helvetica", 11),
        ).pack(anchor=tk.W)

        self.input_text = ScrolledText(inp, height=10, wrap=tk.WORD,
                                       font=("Courier", 10))
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(3, 0))

        # ---- Middle: Controls ----
        ctrl = tk.Frame(self.root)
        ctrl.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(ctrl, text="Sequence Type:",
                 font=("Helvetica", 11)).pack(side=tk.LEFT)

        self.seq_type = tk.StringVar(value="DNA")
        tk.Radiobutton(ctrl, text="DNA", variable=self.seq_type, value="DNA",
                       font=("Helvetica", 10)).pack(side=tk.LEFT, padx=(8, 2))
        tk.Radiobutton(ctrl, text="Protein", variable=self.seq_type,
                       value="Protein",
                       font=("Helvetica", 10)).pack(side=tk.LEFT, padx=(2, 2))

        self.run_btn = tk.Button(
            ctrl, text="Run Alignment", command=self._on_run,
            bg="#4CAF50", fg="white", font=("Helvetica", 11, "bold"),
            padx=20, pady=4,
        )
        self.run_btn.pack(side=tk.LEFT, padx=(25, 0))

        # ---- Bottom: Output ----
        out = tk.Frame(self.root)
        out.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        tk.Label(out, text="Alignment Results:",
                 font=("Helvetica", 11)).pack(anchor=tk.W)

        box = tk.Frame(out)
        box.pack(fill=tk.BOTH, expand=True, pady=(3, 0))
        box.grid_rowconfigure(0, weight=1)
        box.grid_columnconfigure(0, weight=1)

        self.output_text = tk.Text(box, wrap=tk.NONE, font=("Courier", 11),
                                   state=tk.DISABLED)
        self.output_text.grid(row=0, column=0, sticky="nsew")

        ys = tk.Scrollbar(box, orient=tk.VERTICAL,
                          command=self.output_text.yview)
        ys.grid(row=0, column=1, sticky="ns")
        xs = tk.Scrollbar(box, orient=tk.HORIZONTAL,
                          command=self.output_text.xview)
        xs.grid(row=1, column=0, sticky="ew")

        self.output_text.config(yscrollcommand=ys.set, xscrollcommand=xs.set)

        # Highlight tag: red background, white text
        self.output_text.tag_configure("match_highlight",
                                       background="red", foreground="white")

    # ----------------------------------------------------------------
    # Run Button Action
    # ----------------------------------------------------------------
    def _on_run(self):
        # Step 2a: FASTA parsing
        raw = self.input_text.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showerror("Invalid Input",
                                 "Please ensure data is in valid FASTA format.")
            return

        records = parse_fasta(raw)
        if not records:
            messagebox.showerror("Invalid Input",
                                 "Please ensure data is in valid FASTA format.")
            return

        # Empty sequence check
        for name, seq in records:
            if not seq:
                messagebox.showerror(
                    "Invalid Input",
                    f"Sequence '{name}' is empty. "
                    "Please ensure data is in valid FASTA format.")
                return

        # Step 2b: minimum 2 sequences
        if len(records) < 2:
            messagebox.showerror("Insufficient Data",
                                 "Please provide at least 2 sequences "
                                 "for alignment.")
            return

        # Step 2c: sequence type validation
        stype = self.seq_type.get()
        valid = DNA_VALID if stype == "DNA" else PROTEIN_VALID

        for name, seq in records:
            bad = set(seq) - valid
            if bad:
                messagebox.showerror(
                    "Type Mismatch",
                    f"Sequence '{name}' contains invalid characters for "
                    f"{stype}: {', '.join(sorted(bad))}.\n\n"
                    "Please verify the sequence type selection.")
                return

        # Step 2d: perform alignment
        self.run_btn.config(state=tk.DISABLED, text="Aligning...")
        self.root.update_idletasks()

        try:
            aligned = perform_msa(records, stype)
        except Exception as e:
            messagebox.showerror("Alignment Error",
                                 f"Error during alignment:\n{e}")
            self.run_btn.config(state=tk.NORMAL, text="Run Alignment")
            return

        self._show_results(aligned)
        self.run_btn.config(state=tk.NORMAL, text="Run Alignment")

    # ----------------------------------------------------------------
    # Output Formatting
    # ----------------------------------------------------------------
    def _show_results(self, aligned):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)

        if not aligned:
            self.output_text.config(state=tk.DISABLED)
            return

        names = [a[0] for a in aligned]
        seqs  = [a[1] for a in aligned]
        alen  = len(seqs[0])
        pad   = max(len(n) for n in names) + 4

        # 100 % identity columns (no gaps)
        id_cols = set()
        for c in range(alen):
            chars = [s[c] for s in seqs]
            if chars[0] != '-' and all(ch == chars[0] for ch in chars):
                id_cols.add(c)

        block = 60
        for bs in range(0, alen, block):
            be = min(bs + block, alen)

            # Ruler
            ruler = self._ruler(bs, be)
            self.output_text.insert(tk.END, ' ' * pad + ruler + '\n')

            # Sequences
            for name, seq in aligned:
                self.output_text.insert(tk.END, name.ljust(pad))
                for c in range(bs, be):
                    sp = self.output_text.index(tk.INSERT)
                    self.output_text.insert(tk.END, seq[c])
                    if c in id_cols:
                        ep = self.output_text.index(tk.INSERT)
                        self.output_text.tag_add("match_highlight", sp, ep)
                self.output_text.insert(tk.END, '\n')

            self.output_text.insert(tk.END, '\n')

        self.output_text.config(state=tk.DISABLED)

    @staticmethod
    def _ruler(start, end):
        """Position ruler: numbers every 10th column (1-based)."""
        length = end - start
        r = [' '] * length
        for pos in range(start, end):
            p1 = pos + 1
            if p1 % 10 == 0:
                label = str(p1)
                ei = pos - start
                si = ei - len(label) + 1
                for i, ch in enumerate(label):
                    idx = si + i
                    if 0 <= idx < length:
                        r[idx] = ch
        return ''.join(r)


# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    BioAlignerApp(root)
    root.mainloop()
