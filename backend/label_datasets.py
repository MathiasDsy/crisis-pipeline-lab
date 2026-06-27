"""
Lit tous les CSV dans /storage/datasets, ajoute une colonne `label` (True/False)
basée sur la colonne `Informativeness`, et écrase le fichier en place.

Règle : label = True ssi Informativeness == "Related and informative"

Usage :
    python label_datasets.py
    python label_datasets.py --dry-run   # affiche sans écrire
"""

import argparse
from pathlib import Path

import pandas as pd

DATASETS_DIR = Path(__file__).parent / "storage" / "datasets"
INFORMATIVE_VALUE = "Related and informative"


def label_dataset(path: Path, dry_run: bool) -> None:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()

    if "Informativeness" not in df.columns:
        print(f"  [SKIP] {path.name} — colonne 'Informativeness' absente")
        return

    df["label"] = df["Informativeness"].str.strip() == INFORMATIVE_VALUE

    counts = df["label"].value_counts()
    true_count = counts.get(True, 0)
    false_count = counts.get(False, 0)
    print(f"  [OK]   {path.name} — {true_count} True / {false_count} False")

    if not dry_run:
        df.to_csv(path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Affiche sans écrire")
    args = parser.parse_args()

    if not DATASETS_DIR.exists():
        print(f"Dossier introuvable : {DATASETS_DIR}")
        return

    csv_files = sorted(DATASETS_DIR.glob("*.csv"))

    if not csv_files:
        print("Aucun CSV trouvé.")
        return

    mode = "DRY RUN" if args.dry_run else "ÉCRITURE"
    print(f"=== label_datasets [{mode}] — {len(csv_files)} fichier(s) ===\n")

    for path in csv_files:
        label_dataset(path, dry_run=args.dry_run)

    print("\nTerminé.")


if __name__ == "__main__":
    main()
