
"""
Metabolic Pathway Finder
- Input: two metabolites + species
- Output: common pathways, involved enzymes, enzyme sequences
- Data sources: KEGG REST API + UniProt REST API
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import requests
import re
import math
import heapq
from collections import defaultdict, deque

# ============================================================
# KEGG API Functions
# ============================================================

KEGG_BASE = "https://rest.kegg.jp"

SPECIES_MAP = {
    "Human": "hsa",
    "Mouse": "mmu",
    "Rat": "rno",
    "E. coli K-12": "eco",
    "S. cerevisiae (Yeast)": "sce",
    "D. melanogaster (Fruit fly)": "dme",
    "C. elegans": "cel",
    "A. thaliana": "ath",
    "Zebrafish": "dre",
    "Chicken": "gga",
}

SPECIES_NAMES = {v: k for k, v in SPECIES_MAP.items()}

# Currency metabolites — cofactors/carriers that appear in nearly all pathways
CURRENCY_METABOLITES = {
    # Water, protons, inorganic
    "C00001",  # H2O
    "C00009",  # Orthophosphate
    "C00013",  # Diphosphate
    "C00059",  # Sulfate
    "C00076",  # Calcium cation
    "C00080",  # H+
    "C00014",  # NH3
    "C00011",  # CO2
    # Nucleotide energy carriers
    "C00002",  # ATP
    "C00008",  # ADP
    "C00020",  # AMP
    "C00044",  # GTP
    "C00035",  # GDP
    "C00063",  # CTP
    "C00075",  # UTP
    "C00015",  # UDP
    # Redox cofactors
    "C00003",  # NAD+
    "C00004",  # NADH
    "C00005",  # NADPH
    "C00006",  # NADP+
    "C00016",  # FAD
    "C01352",  # FADH2
    "C00138",  # Ferredoxin (reduced)
    "C00139",  # Ferredoxin (oxidized)
    # Coenzymes / carriers
    "C00010",  # CoA
    "C00019",  # S-Adenosyl-L-methionine (SAM)
    "C00021",  # S-Adenosyl-L-homocysteine
    "C00120",  # Biotin
    "C00194",  # Cobamide coenzyme
    "C00255",  # Riboflavin
    "C00053",  # 3'-Phosphoadenosine 5'-phosphosulfate (PAPS)
    "C00054",  # Adenosine 3',5'-bisphosphate
    # Ubiquitous amino-group carriers (hub metabolites)
    "C00025",  # L-Glutamate
    "C00026",  # 2-Oxoglutarate (alpha-Ketoglutarate)
    "C00064",  # L-Glutamine
    # Ubiquitous C1/C2 carriers
    "C00024",  # Acetyl-CoA
    "C00033",  # Acetate
    "C00227",  # Acetaldehyde
    # Thioester / acyl carriers
    "C00229",  # Acyl-carrier protein
    "C00068",  # Thiamin diphosphate
    # Reactive oxygen / generic acceptors
    "C00027",  # Hydrogen peroxide (H2O2)
    "C00007",  # Oxygen (O2)
    "C00028",  # Acceptor (generic KEGG placeholder)
    "C00030",  # Reduced acceptor (generic)
    "C00144",  # GMP
    # SAM reaction byproducts
    "C00073",  # L-Methionine (SAM demethylation product)
    "C05198",  # 5'-Deoxyadenosine (radical SAM byproduct)
    "C15809",  # Iminoglycine (deamination byproduct)
    # Generic / ubiquitous small molecules
    "C00058",  # Formate
    "C00048",  # Glyoxylate
    # Electron carriers (quinones)
    "C15602",  # Quinone (generic electron acceptor)
    "C15603",  # Hydroquinone (generic electron donor)
}


def search_organism(name):
    """Search KEGG organism list for matches.
    Returns list of (org_code, full_name) tuples.
    """
    resp = requests.get(f"{KEGG_BASE}/list/organism", timeout=15)
    if resp.status_code != 200 or not resp.text.strip():
        return []
    query = name.lower()
    results = []
    for line in resp.text.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) >= 3:
            org_code = parts[1]
            org_name = parts[2]
            if query in org_name.lower() or query in org_code.lower():
                results.append((org_code, org_name))
    return results


def search_compound(name):
    """Search KEGG for compounds matching the given name.
    Returns list of (compound_id, compound_name) tuples.
    Currency metabolites (ATP, H2O, NAD+, etc.) are filtered out.
    """
    resp = requests.get(f"{KEGG_BASE}/find/compound/{name}", timeout=15)
    if resp.status_code != 200 or not resp.text.strip():
        return []
    results = []
    for line in resp.text.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) >= 2:
            cpd_id = parts[0].replace("cpd:", "")
            if cpd_id in CURRENCY_METABOLITES:
                continue
            cpd_names = parts[1].split(";")
            results.append((cpd_id, cpd_names[0].strip()))
    return results


def get_pathways_for_compound(compound_id):
    """Get all pathways containing the given compound.
    Returns list of (pathway_id, pathway_id) tuples — map pathways only.
    """
    resp = requests.get(f"{KEGG_BASE}/link/pathway/{compound_id}", timeout=15)
    if resp.status_code != 200 or not resp.text.strip():
        return []
    pathways = []
    for line in resp.text.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) >= 2:
            pw = parts[1].replace("path:", "")
            # Only keep map (reference) pathways
            if pw.startswith("map"):
                pathways.append(pw)
    return list(set(pathways))


def get_pathway_name(pathway_id):
    """Get the name of a pathway from KEGG."""
    resp = requests.get(f"{KEGG_BASE}/get/{pathway_id}", timeout=15)
    if resp.status_code != 200:
        return pathway_id
    for line in resp.text.split("\n"):
        if line.startswith("NAME"):
            return line.replace("NAME", "").strip()
    return pathway_id


# ============================================================
# Pathway Finding Logic
# ============================================================


def find_common_pathways_multi(compound_ids_1, compound_ids_2, progress_cb=None):
    """Find pathways common between any compound in group 1 and any in group 2.
    Returns sorted list of common pathway IDs.
    progress_cb: optional callback(current, total) for progress updates.
    """
    total = len(compound_ids_1) + len(compound_ids_2)
    done = 0

    pw_set1 = set()
    for cid in compound_ids_1:
        pw_set1.update(get_pathways_for_compound(cid))
        done += 1
        if progress_cb:
            progress_cb(done, total)

    pw_set2 = set()
    for cid in compound_ids_2:
        pw_set2.update(get_pathways_for_compound(cid))
        done += 1
        if progress_cb:
            progress_cb(done, total)

    common = pw_set1 & pw_set2
    return sorted(common)


# Overview pathways to exclude (too broad to be useful)
OVERVIEW_PATHWAYS = {
    "map01100", "map01110", "map01120", "map01130", "map01200",
    "map01210", "map01212", "map01230", "map01232", "map01240",
}


class MetaboliteNetwork:
    """Compound-reaction network from KEGG with BFS route finding.
    Routes are validated against reaction equations (substrate/product sides)
    and ranked by pathway coherence to prioritize biologically meaningful paths.
    """

    # Compounds with degree >= this threshold are auto-classified as hubs
    HUB_DEGREE_THRESHOLD = 50

    # Compounds with degree >= this threshold are auto-classified as hubs
    HUB_DEGREE_THRESHOLD = 50

    def __init__(self):
        self.rxn_to_cpds = defaultdict(set)
        self.cpd_to_rxns = defaultdict(set)
        self.rxn_to_enzymes = defaultdict(set)
        self.rxn_to_pathways = defaultdict(set)
        self.rxn_equations = {}  # rxn_id -> (left_cpds_set, right_cpds_set)
        self.hub_metabolites = set()  # auto-detected high-degree hubs
        # Directed adjacency: cpd -> [(neighbor, rxn_id, direction), ...]
        self.directed_edges = defaultdict(list)
        self._loaded = False
        self._org_pathways_cache = {}  # org_code -> set of map IDs

    def _get_org_pathways(self, org_code, progress_cb=None):
        """Get set of pathway map IDs that exist for a given organism."""
        if org_code in self._org_pathways_cache:
            return self._org_pathways_cache[org_code]
        if progress_cb:
            progress_cb(f"Downloading {org_code} pathway list...")
        resp = requests.get(f"{KEGG_BASE}/list/pathway/{org_code}", timeout=30)
        pathways = set()
        if resp.status_code == 200 and resp.text.strip():
            for line in resp.text.strip().split("\n"):
                parts = line.split("\t")
                if parts:
                    # Convert "hsa00010" or "path:hsa00010" -> "map00010"
                    raw = parts[0].replace("path:", "")
                    pw = "map" + raw[len(org_code):]
                    pathways.add(pw)
        self._org_pathways_cache[org_code] = pathways
        return pathways

    def load(self, progress_cb=None):
        """Download KEGG bulk data and build the network."""
        if self._loaded:
            return

        if progress_cb:
            progress_cb("Downloading reaction-compound links...")
        resp = requests.get(f"{KEGG_BASE}/link/compound/reaction", timeout=60)
        # Build reaction-pathway mapping first (to filter reactions)
        if progress_cb:
            progress_cb("Downloading reaction-pathway links...")
        resp_pw = requests.get(f"{KEGG_BASE}/link/pathway/reaction", timeout=60)
        for line in resp_pw.text.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) == 2:
                rxn = parts[0].replace("rn:", "")
                pw = parts[1].replace("path:", "")
                if pw.startswith("map") and pw not in OVERVIEW_PATHWAYS:
                    self.rxn_to_pathways[rxn].add(pw)

        # Phase 1: Build full compound-reaction graph (filter only manual list)
        raw_cpd_to_rxns = defaultdict(set)
        raw_rxn_to_cpds = defaultdict(set)
        for line in resp.text.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) == 2:
                rxn = parts[0].replace("rn:", "")
                cpd = parts[1].replace("cpd:", "")
                if cpd not in CURRENCY_METABOLITES and rxn in self.rxn_to_pathways:
                    raw_rxn_to_cpds[rxn].add(cpd)
                    raw_cpd_to_rxns[cpd].add(rxn)

        # Phase 2: Auto-detect hub metabolites by degree
        self.hub_metabolites = set()
        for cpd, rxns in raw_cpd_to_rxns.items():
            if len(rxns) >= self.HUB_DEGREE_THRESHOLD:
                self.hub_metabolites.add(cpd)

        if progress_cb:
            progress_cb(f"Auto-detected {len(self.hub_metabolites)} hub metabolites "
                        f"(degree >= {self.HUB_DEGREE_THRESHOLD})")

        # Keep raw graph for source/target lookup
        self.raw_cpd_to_rxns = raw_cpd_to_rxns
        self.raw_rxn_to_cpds = raw_rxn_to_cpds

        # Phase 3: Rebuild graph without hubs
        for rxn, cpds in raw_rxn_to_cpds.items():
            for cpd in cpds:
                if cpd not in self.hub_metabolites:
                    self.rxn_to_cpds[rxn].add(cpd)
                    self.cpd_to_rxns[cpd].add(rxn)

        if progress_cb:
            progress_cb("Downloading reaction-enzyme links...")
        resp_enz = requests.get(f"{KEGG_BASE}/link/enzyme/reaction", timeout=60)
        for line in resp_enz.text.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) == 2:
                rxn = parts[0].replace("rn:", "")
                ec = parts[1].replace("ec:", "")
                self.rxn_to_enzymes[rxn].add(ec)

        # Phase 4: Fetch all reaction equations and build directed edges
        all_rxn_ids = set(self.rxn_to_cpds.keys())
        if progress_cb:
            progress_cb(f"Downloading reaction equations ({len(all_rxn_ids)} reactions)...")
        self._fetch_equations(all_rxn_ids, progress_cb)

        # Build directed adjacency: substrate→product and product→substrate
        # Only skip CURRENCY_METABOLITES (true cofactors); hubs are penalized, not blocked
        for rxn, (left, right) in self.rxn_equations.items():
            if rxn not in self.rxn_to_pathways:
                continue
            left_valid = left - CURRENCY_METABOLITES
            right_valid = right - CURRENCY_METABOLITES
            for s in left_valid:
                for p in right_valid:
                    self.directed_edges[s].append((p, rxn, "forward"))
                    self.directed_edges[p].append((s, rxn, "reverse"))

        self._loaded = True
        if progress_cb:
            progress_cb(f"Network ready: {len(self.rxn_to_cpds)} reactions, "
                        f"{len(self.cpd_to_rxns)} compounds, "
                        f"{len(self.directed_edges)} routable compounds")

    def _pathway_coherence(self, path):
        """Score a route by how well it stays within connected pathways.
        Higher score = better (more reactions share pathways).
        Returns float between 0.0 and 1.0.
        """
        if len(path) < 2:
            return 1.0
        rxns = [rxn for _, rxn in path if rxn]
        if len(rxns) <= 1:
            return 1.0
        shared = 0
        for i in range(len(rxns) - 1):
            pw_a = self.rxn_to_pathways.get(rxns[i], set())
            pw_b = self.rxn_to_pathways.get(rxns[i + 1], set())
            if pw_a & pw_b:
                shared += 1
        return shared / (len(rxns) - 1)

    def _fetch_equations(self, rxn_ids, progress_cb=None):
        """Batch-fetch reaction equations from KEGG (10 per request).
        Populates self.rxn_equations with {rxn_id: (left_cpds, right_cpds)}.
        """
        to_fetch = [r for r in rxn_ids if r not in self.rxn_equations]
        if not to_fetch:
            return
        for i in range(0, len(to_fetch), 10):
            batch = to_fetch[i:i + 10]
            if progress_cb:
                progress_cb(f"Verifying reactions ({i + len(batch)}/{len(to_fetch)})...")
            query = "+".join(batch)
            try:
                resp = requests.get(f"{KEGG_BASE}/get/{query}", timeout=30)
            except requests.RequestException:
                continue
            if resp.status_code != 200:
                continue
            current_rxn = None
            for line in resp.text.split("\n"):
                if line.startswith("ENTRY"):
                    match = re.search(r'(R\d+)', line)
                    if match:
                        current_rxn = match.group(1)
                elif line.startswith("EQUATION") and current_rxn:
                    eq_text = line.replace("EQUATION", "").strip()
                    sides = re.split(r'\s*<=>\s*', eq_text)
                    if len(sides) == 2:
                        left = set(re.findall(r'(C\d{5})', sides[0]))
                        right = set(re.findall(r'(C\d{5})', sides[1]))
                        self.rxn_equations[current_rxn] = (left, right)
                    current_rxn = None

    def get_step_direction(self, from_cpd, to_cpd, rxn_id):
        """Check directionality of a step in a route.
        Returns 'forward', 'reverse', or None (invalid: same side).
        """
        if rxn_id not in self.rxn_equations:
            return "forward"
        left, right = self.rxn_equations[rxn_id]
        if from_cpd in left and to_cpd in right:
            return "forward"
        if from_cpd in right and to_cpd in left:
            return "reverse"
        return None  # both on same side — invalid

    def _validate_route(self, path):
        """Returns True if every step crosses from one side to the other."""
        for i in range(1, len(path)):
            cpd, rxn = path[i]
            prev_cpd = path[i - 1][0]
            if self.get_step_direction(prev_cpd, cpd, rxn) is None:
                return False
        return True

    def find_routes(self, source_ids, target_ids, org_code=None,
                    max_depth=15, max_candidates=1000, progress_cb=None):
        """Dijkstra route finder on directed graph (substrate→product edges).
        Edges are pre-validated during load, so no post-hoc validation needed.
        Routes ranked by pathway coherence.
        """
        targets = set(target_ids)

        # Build organism-filtered reaction set
        if org_code:
            org_pws = self._get_org_pathways(org_code, progress_cb)
            org_rxns = {rxn for rxn, pws in self.rxn_to_pathways.items()
                        if pws & org_pws}
        else:
            org_rxns = None

        if progress_cb:
            progress_cb("Searching routes...")

        # Dijkstra with hub penalty
        pq = []
        counter = 0
        best_cost = {}

        for sid in source_ids:
            heapq.heappush(pq, (0.0, counter, sid, [(sid, None)]))
            best_cost[sid] = 0.0
            counter += 1

        candidates = []
        max_cost = None
        nodes_explored = 0

        while pq and len(candidates) < max_candidates:
            cost, _, cpd, path = heapq.heappop(pq)
            depth = len(path) - 1
            nodes_explored += 1

            if max_cost is not None and cost > max_cost * 3:
                break
            if depth >= max_depth:
                continue

            path_cpds = {c for c, _ in path}

            for neighbor, rxn, direction in self.directed_edges.get(cpd, []):
                if neighbor in path_cpds:
                    continue
                if org_rxns is not None and rxn not in org_rxns:
                    continue

                # Penalize hub metabolites as transit nodes
                if neighbor in self.hub_metabolites and neighbor not in targets:
                    new_cost = cost + math.log2(
                        len(self.raw_cpd_to_rxns.get(neighbor, [])) + 1)
                else:
                    new_cost = cost + 1.0

                if neighbor in targets:
                    full_path = path + [(neighbor, rxn)]
                    candidates.append(full_path)
                    if max_cost is None:
                        max_cost = cost + 1.0
                    continue

                if neighbor not in best_cost or new_cost < best_cost[neighbor]:
                    best_cost[neighbor] = new_cost
                    heapq.heappush(pq, (new_cost, counter, neighbor,
                                        path + [(neighbor, rxn)]))
                    counter += 1

            if progress_cb and nodes_explored % 2000 == 0:
                progress_cb(f"Exploring... ({nodes_explored} nodes, "
                            f"{len(candidates)} candidates)")

        if not candidates:
            return []

        # Rank by pathway coherence (desc), then steps (asc)
        ranked = []
        for path in candidates:
            coherence = self._pathway_coherence(path)
            steps = len([r for _, r in path if r])
            ranked.append((-coherence, steps, path))

        if progress_cb:
            progress_cb(f"Found {len(candidates)} valid routes")

        ranked.sort()
        return [path for _, _, path in ranked[:10]]

    def get_compound_name(self, compound_id):
        """Get compound name from KEGG."""
        resp = requests.get(f"{KEGG_BASE}/get/{compound_id}", timeout=10)
        if resp.status_code != 200:
            return compound_id
        for line in resp.text.split("\n"):
            if line.startswith("NAME"):
                return line.replace("NAME", "").strip().rstrip(";")
        return compound_id


# Global network instance (loaded once, reused)
_network = MetaboliteNetwork()


# ============================================================
# GUI Application
# ============================================================


class PathwayFinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Metabolic Pathway Finder")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        self._build_input_frame()
        self._build_result_frame()
        self._build_status_bar()

        # State
        self.compound1_results = []
        self.compound2_results = []
        self.current_pathways = []

    # ---- Input Frame ----
    def _build_input_frame(self):
        frame = ttk.LabelFrame(self.root, text="Input", padding=10)
        frame.pack(fill="x", padx=10, pady=(10, 5))

        # Metabolite 1
        ttk.Label(frame, text="Metabolite 1:").grid(row=0, column=0, sticky="w", pady=2)
        self.met1_var = tk.StringVar()
        self.met1_entry = ttk.Entry(frame, textvariable=self.met1_var, width=30)
        self.met1_entry.grid(row=0, column=1, padx=5, pady=2)
        self.met1_btn = ttk.Button(frame, text="Search", command=lambda: self._search_compound(1))
        self.met1_btn.grid(row=0, column=2, padx=5)
        self.met1_combo = ttk.Combobox(frame, state="readonly", width=40)
        self.met1_combo.grid(row=0, column=3, padx=5)

        # Metabolite 2
        ttk.Label(frame, text="Metabolite 2:").grid(row=1, column=0, sticky="w", pady=2)
        self.met2_var = tk.StringVar()
        self.met2_entry = ttk.Entry(frame, textvariable=self.met2_var, width=30)
        self.met2_entry.grid(row=1, column=1, padx=5, pady=2)
        self.met2_btn = ttk.Button(frame, text="Search", command=lambda: self._search_compound(2))
        self.met2_btn.grid(row=1, column=2, padx=5)
        self.met2_combo = ttk.Combobox(frame, state="readonly", width=40)
        self.met2_combo.grid(row=1, column=3, padx=5)

        # Species — entry + search + combo (like metabolites)
        ttk.Label(frame, text="Species:").grid(row=2, column=0, sticky="w", pady=2)
        self.species_var = tk.StringVar()
        self.species_entry = ttk.Entry(frame, textvariable=self.species_var, width=30)
        self.species_entry.grid(row=2, column=1, padx=5, pady=2)
        self.species_btn = ttk.Button(frame, text="Search", command=self._search_species)
        self.species_btn.grid(row=2, column=2, padx=5)
        self.species_combo = ttk.Combobox(frame, state="readonly", width=40)
        self.species_combo.grid(row=2, column=3, padx=5)
        # Pre-populate with common species
        common_species = [f"{name} ({code})" for name, code in SPECIES_MAP.items()]
        self.species_results = [(code, name) for name, code in SPECIES_MAP.items()]
        self.species_combo["values"] = common_species
        self.species_combo.current(0)  # Human

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=1, columnspan=3, pady=(5, 0), sticky="e")
        self.find_btn = ttk.Button(btn_frame, text="Find Pathway", command=self._on_find)
        self.find_btn.pack(side="left", padx=5)
        self.route_btn = ttk.Button(btn_frame, text="Find Route", command=self._on_find_route)
        self.route_btn.pack(side="left", padx=5)

    # ---- Result Frame (Notebook with tabs) ----
    def _build_result_frame(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Pathway tab — multiple selection enabled
        pw_frame = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(pw_frame, text="Pathways")
        self.pathway_list = tk.Listbox(pw_frame, font=("Courier", 11),
                                       selectmode="extended")
        self.pathway_list.pack(fill="both", expand=True)
        # Routes tab
        route_frame = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(route_frame, text="Routes")
        self.route_text = tk.Text(route_frame, font=("Courier", 11), wrap="word",
                                  state="disabled")
        route_scroll = ttk.Scrollbar(route_frame, command=self.route_text.yview)
        self.route_text.configure(yscrollcommand=route_scroll.set)
        route_scroll.pack(side="right", fill="y")
        self.route_text.pack(fill="both", expand=True)
        route_btn_bar = ttk.Frame(route_frame)
        route_btn_bar.pack(fill="x", pady=(5, 0))
        ttk.Button(route_btn_bar, text="Copy",
                   command=self._copy_route_text).pack(side="right", padx=5)

    # ---- Status Bar ----
    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(fill="x", padx=10, pady=(0, 10))

    # ---- Compound Search ----
    def _search_compound(self, which):
        name = self.met1_var.get().strip() if which == 1 else self.met2_var.get().strip()
        if not name:
            messagebox.showwarning("Input Required", f"Please enter Metabolite {which} name.")
            return

        combo = self.met1_combo if which == 1 else self.met2_combo
        self.status_var.set(f"Searching KEGG for '{name}'...")

        def _do():
            try:
                results = search_compound(name)
                self.root.after(0, lambda: self._show_compound_results(which, results))
            except Exception as e:
                self.root.after(0, lambda: self._on_error(f"Search failed: {e}"))

        threading.Thread(target=_do, daemon=True).start()

    def _show_compound_results(self, which, results):
        combo = self.met1_combo if which == 1 else self.met2_combo
        if which == 1:
            self.compound1_results = results
        else:
            self.compound2_results = results

        if not results:
            combo["values"] = ["No results found"]
            self.status_var.set("No compounds found.")
            return

        display = [f"{cid} - {cname}" for cid, cname in results]
        combo["values"] = display
        combo.current(0)
        self.status_var.set(f"Found {len(results)} compound(s).")

    # ---- Species Search ----
    def _search_species(self):
        name = self.species_var.get().strip()
        if not name:
            messagebox.showwarning("Input Required", "Please enter a species name.")
            return
        self.status_var.set(f"Searching KEGG for organism '{name}'...")

        def _do():
            try:
                results = search_organism(name)
                self.root.after(0, lambda: self._show_species_results(results))
            except Exception as e:
                self.root.after(0, lambda: self._on_error(f"Species search failed: {e}"))

        threading.Thread(target=_do, daemon=True).start()

    def _show_species_results(self, results):
        self.species_results = results
        if not results:
            self.species_combo["values"] = ["No results found"]
            self.status_var.set("No organisms found.")
            return
        display = [f"{code} - {name}" for code, name in results]
        self.species_combo["values"] = display
        self.species_combo.current(0)
        self.status_var.set(f"Found {len(results)} organism(s).")

    def _get_selected_species(self):
        """Get the selected species org_code and display name."""
        idx = self.species_combo.current()
        if idx < 0 or idx >= len(self.species_results):
            return None, None
        code, name = self.species_results[idx]
        return code, name

    # ---- Find Pathway ----
    def _on_find(self):
        # Use ALL search results
        cpds1 = [cid for cid, _ in self.compound1_results]
        cpds2 = [cid for cid, _ in self.compound2_results]
        if not cpds1 or not cpds2:
            messagebox.showwarning("Selection Required",
                                   "Please search both metabolites first.")
            return

        species, species_name = self._get_selected_species()
        if not species:
            messagebox.showwarning("Species Required", "Please search and select a species.")
            return

        self.find_btn.config(state="disabled")
        self.pathway_list.delete(0, "end")

        total = len(cpds1) + len(cpds2)
        self.status_var.set(f"Comparing {len(cpds1)} x {len(cpds2)} compounds (0/{total})...")

        def _progress(done, total):
            self.root.after(0, lambda: self.status_var.set(
                f"Fetching pathways... ({done}/{total} compounds)"))

        def _do():
            try:
                common = find_common_pathways_multi(cpds1, cpds2, progress_cb=_progress)
                pw_info = []
                for pw_id in common:
                    name = get_pathway_name(pw_id)
                    pw_info.append((pw_id, name))
                self.root.after(0, lambda: self._show_pathways(pw_info, species, species_name))
            except Exception as e:
                self.root.after(0, lambda: self._on_error(f"Pathway search failed: {e}"))
            finally:
                self.root.after(0, lambda: self.find_btn.config(state="normal"))

        threading.Thread(target=_do, daemon=True).start()

    def _get_selected_compound(self, which):
        combo = self.met1_combo if which == 1 else self.met2_combo
        results = self.compound1_results if which == 1 else self.compound2_results
        idx = combo.current()
        if idx < 0 or idx >= len(results):
            return None
        return results[idx][0]

    def _show_pathways(self, pw_info, species, species_name=""):
        self.current_pathways = pw_info
        self.current_species = species
        self.current_species_name = species_name
        self.pathway_list.delete(0, "end")

        if not pw_info:
            self.pathway_list.insert("end", "No common pathways found.")
            self.status_var.set("No common pathways found.")
            return

        for pw_id, name in pw_info:
            self.pathway_list.insert("end", f"{pw_id}  |  {name}")
        self.status_var.set(f"Found {len(pw_info)} common pathway(s).")
        self.notebook.select(0)

    # ---- Error ----
    # ---- Find Route (BFS through metabolite network) ----
    def _on_find_route(self):
        cpds1 = [cid for cid, _ in self.compound1_results]
        cpds2 = [cid for cid, _ in self.compound2_results]
        if not cpds1 or not cpds2:
            messagebox.showwarning("Selection Required",
                                   "Please search both metabolites first.")
            return

        species, species_name = self._get_selected_species()
        if not species:
            messagebox.showwarning("Species Required", "Please search and select a species.")
            return

        self.route_btn.config(state="disabled")
        self.find_btn.config(state="disabled")
        self._set_route_text("Loading metabolite network...")

        def _do():
            try:
                def _progress(msg):
                    self.root.after(0, lambda: self.status_var.set(msg))

                _network.load(progress_cb=_progress)

                _progress(f"Searching routes for {species_name} ({species})...")
                routes = _network.find_routes(
                    cpds1, cpds2, org_code=species,
                    max_depth=20, max_candidates=1000, progress_cb=_progress)

                if not routes:
                    self.root.after(0, lambda: self._show_routes(
                        "No routes found between these metabolites.", species, species_name))
                    return

                # Build display text with compound names and enzyme info
                _progress("Resolving compound and enzyme names...")
                # Cache compound names
                cpd_names = {}
                for route in routes:
                    for cpd, _ in route:
                        if cpd not in cpd_names:
                            cpd_names[cpd] = _network.get_compound_name(cpd)

                lines = []
                for i, route in enumerate(routes):
                    reactions = [rxn for _, rxn in route if rxn]
                    coherence = _network._pathway_coherence(route)
                    lines.append(f"{'='*60}")
                    lines.append(f"Route {i+1}  ({len(reactions)} steps, "
                                 f"coherence: {coherence:.0%})")
                    lines.append(f"{'='*60}")
                    for j, (cpd, rxn) in enumerate(route):
                        name = cpd_names.get(cpd, cpd)
                        if rxn:
                            prev_cpd = route[j - 1][0]
                            direction = _network.get_step_direction(prev_cpd, cpd, rxn)
                            dir_tag = "" if direction == "forward" else " (reverse)"
                            ecs = _network.rxn_to_enzymes.get(rxn, set())
                            pws = _network.rxn_to_pathways.get(rxn, set())
                            ec_str = ", ".join(sorted(ecs)[:3]) if ecs else "?"
                            pw_str = ", ".join(sorted(pws)[:2]) if pws else ""
                            lines.append(f"  | [{rxn}]{dir_tag} EC:{ec_str}")
                            if pw_str:
                                lines.append(f"  |  Pathway: {pw_str}")
                            lines.append(f"  v")
                        lines.append(f"  {cpd}  {name}")
                    lines.append("")

                result_text = "\n".join(lines)
                self.root.after(0, lambda: self._show_routes(
                    result_text, species, species_name))

            except Exception as e:
                self.root.after(0, lambda: self._on_error(f"Route search failed: {e}"))
            finally:
                self.root.after(0, lambda: self.route_btn.config(state="normal"))
                self.root.after(0, lambda: self.find_btn.config(state="normal"))

        threading.Thread(target=_do, daemon=True).start()

    def _set_route_text(self, text):
        self.route_text.config(state="normal")
        self.route_text.delete("1.0", "end")
        self.route_text.insert("1.0", text)
        self.route_text.config(state="disabled")

    def _copy_route_text(self):
        text = self.route_text.get("1.0", "end").strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_var.set("Copied to clipboard.")

    def _show_routes(self, text, species, species_name):
        self._set_route_text(text)
        self.current_species = species
        self.current_species_name = species_name
        # Switch to Routes tab
        self.notebook.select(1)
        route_count = text.count("Route ")
        self.status_var.set(f"Found {route_count} route(s).")

    # ---- Error ----
    def _on_error(self, msg):
        self.status_var.set(msg)
        messagebox.showerror("Error", msg)


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = PathwayFinderApp(root)
    root.mainloop()
