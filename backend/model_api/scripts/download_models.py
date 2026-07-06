#!/usr/bin/env python3
"""
Download the models required by the pipeline from the HuggingFace Hub.

Each model is downloaded **in full** (weights + config + tokenizer + everything the
loader needs) with `snapshot_download` into a sibling temp dir, then swapped into
the storage directory atomically. A completion marker (`.download_complete`) is
written *inside* that temp dir, right before the swap — so the marker only ever
appears in storage when the whole download succeeded. An interrupted download
leaves no marker and is retried on the next run.

After a successful download the manifest's `metadata.json` is (re)written, since
that file — not the Hub contents — drives model discovery in pipeline-api.

Idempotent:
  - a dir with the completion marker is trusted and skipped;
  - a pre-existing dir without the marker but that looks complete (weights +
    tokenizer + config, e.g. downloaded manually) is adopted — the marker is
    written and it is not re-downloaded;
  - anything else (missing, or only partially downloaded) is (re)downloaded.

Configuration via environment variables:
  MODELS_DIR  target directory          (default: backend/storage/models)
  HF_TOKEN    HF token for private repos (optional)

Usage:
  python download_models.py [path/to/models_manifest.json]
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

COMPLETE_MARKER = ".download_complete"
WEIGHT_SUFFIXES = (".safetensors", ".bin")
# tokenizer artifacts across model families (transformers, gliner, sentencepiece)
TOKENIZER_FILES = ("tokenizer.json", "tokenizer_config.json", "sentencepiece.bpe.model", "vocab.txt", "spm.model")


def _looks_complete(target: Path) -> bool:
    """
    Heuristic used only to adopt pre-existing (marker-less) dirs: a model dir looks
    complete when it holds weights AND a tokenizer AND a config. We check file
    *kinds*, not exact names from the manifest — the manifest's filenames are not
    always accurate (e.g. it lists pytorch_model.bin while the repo ships
    model.safetensors), whereas the loader only needs one file of each kind.
    """
    if not target.is_dir():
        return False

    names = {p.name for p in target.iterdir() if p.is_file()}

    has_weights = any(n.endswith(WEIGHT_SUFFIXES) and n != "training_args.bin" for n in names)
    has_tokenizer = any(n in names for n in TOKENIZER_FILES)
    has_config = any(n.endswith("config.json") for n in names)  # config.json / gliner_config.json

    return has_weights and has_tokenizer and has_config


def _ensure_tokenizer(model_dir: Path, hf_token: str | None) -> None:
    """
    GLiNER-style models ship only weights + `gliner_config.json`; their tokenizer
    lives in the base model repo (`config.model_name`). GLiNER's `_load_tokenizer`
    reads the tokenizer from the model dir when a `tokenizer_config.json` is present,
    otherwise it falls back to the base name — which fails under `local_files_only`.
    So, for offline loading, fetch the base tokenizer once and save it into the dir.
    """
    gliner_config = model_dir / "gliner_config.json"
    if not gliner_config.is_file():
        return  # not a gliner-style model — nothing to do
    if (model_dir / "tokenizer_config.json").is_file():
        return  # tokenizer already present

    base_model = json.loads(gliner_config.read_text(encoding="utf-8")).get("model_name")
    if not base_model:
        return

    print(f"       fetching tokenizer from base model '{base_model}'")
    from transformers import AutoTokenizer

    AutoTokenizer.from_pretrained(base_model, token=hf_token).save_pretrained(str(model_dir))


def _download_into_place(snapshot_download, repo_id: str, target: Path, hf_token: str | None) -> None:
    """
    Download the full repo into a sibling temp dir, mark it complete, then atomically
    swap it in. Guarantees `target` is either the previous content or the complete
    new content — never a partial mix.
    """
    models_dir = target.parent
    tmp_dir = Path(tempfile.mkdtemp(dir=models_dir, prefix=f".{target.name}.tmp-"))

    try:
        snapshot_download(repo_id=repo_id, local_dir=str(tmp_dir), token=hf_token)
        # snapshot_download leaves an internal .cache folder in local_dir; drop it
        shutil.rmtree(tmp_dir / ".cache", ignore_errors=True)
        # GLiNER repos carry no tokenizer — pull it from the base model if needed
        _ensure_tokenizer(tmp_dir, hf_token)
        # marker is the LAST thing written before the swap → proves the dl finished
        (tmp_dir / COMPLETE_MARKER).write_text(json.dumps({"repo_id": repo_id}), encoding="utf-8")

        # swap: move any existing dir aside, put the new one in place, then clean up
        backup = target.with_name(target.name + ".old") if target.exists() else None
        if backup is not None:
            shutil.rmtree(backup, ignore_errors=True)
            target.rename(backup)

        try:
            tmp_dir.rename(target)
        except OSError:
            if backup is not None:  # restore previous content on failure
                backup.rename(target)
            raise
        finally:
            if backup is not None:
                shutil.rmtree(backup, ignore_errors=True)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    manifest_path = Path(sys.argv[1]) if len(sys.argv) > 1 else script_dir / "models_manifest.json"
    models_dir = Path(os.environ.get("MODELS_DIR", repo_root / "backend" / "storage" / "models"))
    hf_token = os.environ.get("HF_TOKEN") or None

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("ERROR: huggingface_hub is not installed (pip install huggingface_hub)", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    models = manifest.get("models", [])
    models_dir.mkdir(parents=True, exist_ok=True)

    print(f"Models directory : {models_dir}")
    print(f"Manifest         : {manifest_path}")
    print(f"{len(models)} model(s) to provision\n")

    for entry in models:
        repo_id = entry["repo_id"]
        target = models_dir / entry["target_dir"]
        metadata = entry["metadata"]

        if (target / COMPLETE_MARKER).exists() and _looks_complete(target):
            print(f"[skip] {entry['target_dir']} — already complete")
        elif _looks_complete(target):
            print(f"[adopt] {entry['target_dir']} — existing download, marking complete")
            (target / COMPLETE_MARKER).write_text(json.dumps({"repo_id": repo_id}), encoding="utf-8")
        else:
            print(f"[dl]   {entry['target_dir']} <- {repo_id}")
            try:
                _download_into_place(snapshot_download, repo_id, target, hf_token)
            except Exception as e:  # noqa: BLE001
                print(f"ERROR downloading '{repo_id}': {e}", file=sys.stderr)
                return 1

        # the manifest's metadata.json is the source of truth for discovery
        (target / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(f"       metadata.json written ({metadata['model_key']})")

    print("\nModels ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
