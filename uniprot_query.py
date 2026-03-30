"""
UniProt Protein Sequence Retriever
Retrieves a protein's UniProt ID and full sequence
based on a user-provided gene name and species name.
"""

import requests


UNIPROT_SEARCH_URL = "https://rest.uniprot.org/uniprotkb/search"


def fetch_protein(gene_name, species_name):
    """
    Search UniProt for a protein by gene name and species.
    Prioritizes reviewed (Swiss-Prot) entries.

    Returns:
        dict with 'accession' and 'sequence', or None if not found.
    """
    query = f'gene:{gene_name} AND organism_name:"{species_name}"'

    params = {
        "query": query,
        "format": "json",
        "size": 10,
        "fields": "accession,gene_names,organism_name,sequence,reviewed",
    }

    try:
        resp = requests.get(UNIPROT_SEARCH_URL, params=params, timeout=15)
        resp.raise_for_status()
    except requests.ConnectionError:
        print("[Error] Cannot connect to UniProt API. Check your internet.")
        return None
    except requests.Timeout:
        print("[Error] Request timed out.")
        return None
    except requests.HTTPError as e:
        print(f"[Error] HTTP error: {e}")
        return None

    data = resp.json()
    results = data.get("results", [])

    if not results:
        print(f"[Error] No results found for gene='{gene_name}', "
              f"species='{species_name}'.")
        return None

    # Prioritize reviewed (Swiss-Prot) entries
    reviewed = [r for r in results if r.get("entryType") == "UniProtKB reviewed (Swiss-Prot)"]
    entry = reviewed[0] if reviewed else results[0]

    accession = entry.get("primaryAccession", "N/A")
    seq_info = entry.get("sequence", {})
    sequence = seq_info.get("value", "")

    return {"accession": accession, "sequence": sequence}


def format_sequence(seq, width=60):
    """Format sequence with line breaks every `width` characters."""
    return "\n".join(seq[i:i + width] for i in range(0, len(seq), width))


def main():
    print("=" * 50)
    print("  UniProt Protein Sequence Retriever")
    print("=" * 50)

    gene = input("\nGene name (e.g. Sox2): ").strip()
    if not gene:
        print("[Error] Gene name cannot be empty.")
        return

    species = input("Species name (e.g. Homo sapiens): ").strip()
    if not species:
        print("[Error] Species name cannot be empty.")
        return

    print(f"\nSearching UniProt for gene={gene}, species={species}...")

    result = fetch_protein(gene, species)
    if not result:
        return

    print("\n" + "-" * 50)
    print(f"  UniProt ID : {result['accession']}")
    print(f"  Length     : {len(result['sequence'])} aa")
    print("-" * 50)
    print(f"\n{format_sequence(result['sequence'])}\n")


if __name__ == "__main__":
    main()
