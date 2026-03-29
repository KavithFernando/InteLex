from __future__ import annotations

import argparse
from pathlib import Path

from caseframe.pipeline import RunConfig, run_batch


def main() -> None:
    ap = argparse.ArgumentParser(description="Convert case-report PDFs into RQ1 JSON frames.")
    ap.add_argument("--input", required=True, help="Folder containing PDFs")
    ap.add_argument("--output", required=True, help="Output folder")
    ap.add_argument("--annotator_id", required=True, help="Your name/initials for annotator_id")
    ap.add_argument("--dataset_name", default="casedata.json")
    ap.add_argument("--notes", default="Manual RQ1 clause interpretation frame")
    ap.add_argument("--vision_pages", type=int, default=10, help="Max pages to render for scanned PDFs")
    ap.add_argument("--no_jsonl", action="store_true", help="Do not write combined frames.jsonl")
    ap.add_argument(
        "--clauses",
        default=None,
        help=(
            "Comma-separated whitelist of clause/article refs for EVERY PDF in the batch "
            '(e.g. "12(1),14(1)"). The pipeline emits frames for listed clauses discussed in the case; '
            "non-listed clauses are discarded."
        ),
    )
    ap.add_argument(
        "--constitution",
        type=Path,
        default=Path("constitution/articles.json"),
        help="Path to constitution/articles.json (for clause.text injection and whitelist validation).",
    )
    args = ap.parse_args()

    clauses_tuple: tuple[str, ...] | None = None
    if args.clauses:
        parts = [p.strip() for p in args.clauses.split(",") if p.strip()]
        if not parts:
            raise SystemExit("--clauses was empty after parsing")
        clauses_tuple = tuple(parts)

    cfg = RunConfig(
        input_dir=Path(args.input),
        output_dir=Path(args.output),
        annotator_id=args.annotator_id,
        dataset_name=args.dataset_name,
        notes=args.notes,
        vision_pages=args.vision_pages,
        combine_jsonl=not args.no_jsonl,
        clauses=clauses_tuple,
        constitution_path=args.constitution,
    )
    run_batch(cfg)


if __name__ == "__main__":
    main()

