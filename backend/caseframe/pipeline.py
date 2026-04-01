from __future__ import annotations

import copy
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from pydantic import ValidationError
from tqdm import tqdm

from caseframe.constitution import (
    build_clause_text_map,
    format_constitution_block,
    load_articles_json,
    normalize_model_article,
    resolve_whitelist,
)
from caseframe.llm_openai import (
    detect_discussed_clauses,
    detect_discussed_clauses_from_images,
    extract_frames_from_images,
    extract_frames_from_text,
    load_openai_config,
)
from caseframe.mentions import plausibly_mentioned_in_text
from caseframe.pdf import extract_text_fast, render_pages_as_png_b64
from caseframe.schema import Frame


@dataclass
class RunConfig:
    input_dir: Path
    output_dir: Path
    annotator_id: str
    dataset_name: str = "casedata.json"
    notes: str = "Manual RQ1 clause interpretation frame"
    vision_pages: int = 10
    combine_jsonl: bool = True
    clauses: Optional[tuple[str, ...]] = None
    constitution_path: Optional[Path] = None


def _ensure_dirs(out: Path) -> dict[str, Path]:
    paths = {
        "root": out,
        "json": out / "json",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def _frame_id_prefix_for(pdf_path: Path, pdf_index_1based: int) -> str:
    stem = pdf_path.stem.upper().replace(" ", "_")[:40]
    return f"RQ1_{stem}_{pdf_index_1based:03d}"


def _sanitize_filename_part(s: str, max_len: int = 48) -> str:
    import re

    s = (s or "").strip()
    if not s:
        return "clause"
    s = re.sub(r'[<>:"/\\|?*]', "_", s)
    s = re.sub(r"\s+", "_", s)
    return s[:max_len] if len(s) > max_len else s


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _unify_case_block(frames_data: list[dict[str, Any]]) -> None:
    if len(frames_data) < 2:
        return
    first = frames_data[0].get("case")
    if not isinstance(first, dict):
        return
    canonical = copy.deepcopy(first)
    for f in frames_data[1:]:
        if isinstance(f, dict):
            f["case"] = copy.deepcopy(canonical)


def _resolve_constitution_path(cfg: RunConfig) -> Path:
    p = cfg.constitution_path or Path("constitution/articles.json")
    if not p.is_absolute():
        p = Path.cwd() / p
    return p


def _post_filter_frames(
    frames: list[dict[str, Any]],
    *,
    source_text: str,
    discussed_keys: list[str],
    key_to_text: dict[str, str],
    is_scanned: bool,
) -> tuple[list[dict[str, Any]], int]:
    """Drop frames whose clause is not in discussed_keys or not plausibly in text (when text exists)."""
    allow = set(discussed_keys)
    kept: list[dict[str, Any]] = []
    dropped = 0
    text_ok = bool(source_text and len(source_text.strip()) > 800)
    for fr in frames:
        cl = fr.get("clause")
        if not isinstance(cl, dict):
            dropped += 1
            continue
        raw_art = cl.get("article")
        ak = normalize_model_article(str(raw_art) if raw_art is not None else None, key_to_text)
        if not ak or ak not in allow:
            dropped += 1
            continue
        if text_ok and not is_scanned and not plausibly_mentioned_in_text(ak, source_text):
            dropped += 1
            continue
        cl["article"] = ak
        if ak in key_to_text:
            cl["text"] = key_to_text[ak]
        fr["clause"] = cl
        kept.append(fr)
    return kept, dropped


def run_batch(cfg: RunConfig) -> None:
    load_dotenv(override=False)
    oai_cfg = load_openai_config()

    const_path = _resolve_constitution_path(cfg)
    key_to_text: dict[str, str] = {}
    constitution_ok = const_path.is_file()
    if constitution_ok:
        try:
            key_to_text = build_clause_text_map(load_articles_json(const_path))
        except Exception:
            constitution_ok = False

    paths = _ensure_dirs(cfg.output_dir)
    pdfs = sorted(cfg.input_dir.glob("*.pdf"))
    if not pdfs:
        raise RuntimeError(f"No PDFs found in {cfg.input_dir}")

    clauses_list: Optional[list[str]] = list(cfg.clauses) if cfg.clauses else None
    resolved_whitelist: list[str] = []
    unknown_whitelist: list[str] = []
    if clauses_list:
        resolved_whitelist, unknown_whitelist = resolve_whitelist(clauses_list, key_to_text)

    jsonl_path = cfg.output_dir / "frames.jsonl"
    jsonl_f = jsonl_path.open("w", encoding="utf-8") if cfg.combine_jsonl else None

    manifest: dict[str, Any] = {
        "input_dir": str(cfg.input_dir),
        "output_dir": str(cfg.output_dir),
        "count_pdfs": len(pdfs),
        "vision_pages": cfg.vision_pages,
        "combine_jsonl": cfg.combine_jsonl,
        "clauses_filter": list(cfg.clauses) if cfg.clauses else None,
        "resolved_whitelist": resolved_whitelist,
        "unknown_whitelist_keys": unknown_whitelist,
        "constitution_path": str(const_path),
        "constitution_loaded": constitution_ok,
        "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        "vision_model": os.getenv("OPENAI_VISION_MODEL", os.getenv("OPENAI_MODEL", "gpt-4.1-mini")),
        "files": [],
    }

    try:
        for i, pdf in enumerate(tqdm(pdfs, desc="Processing PDFs")):
            prefix = _frame_id_prefix_for(pdf, i + 1)
            fast = extract_text_fast(str(pdf))
            full_text = fast.text or ""
            is_scanned = fast.used_ocr_or_vision_needed

            raw_frames: list[dict[str, Any]] = []
            mode: str
            discussed: list[str] = []

            if clauses_list:
                if not resolved_whitelist:
                    manifest["files"].append(
                        {
                            "pdf": pdf.name,
                            "mode": "skipped",
                            "pages": fast.page_count,
                            "frame_count": 0,
                            "reason": "no whitelist keys resolved against constitution/articles.json",
                            "output_json_files": [],
                        }
                    )
                    continue

                if is_scanned:
                    mode = "vision"
                    pages_b64 = render_pages_as_png_b64(str(pdf), max_pages=cfg.vision_pages)
                    const_block = format_constitution_block(resolved_whitelist, key_to_text)
                    discussed = detect_discussed_clauses_from_images(
                        cfg=oai_cfg,
                        pdf_filename=pdf.name,
                        page_png_b64=pages_b64,
                        allowed_keys=resolved_whitelist,
                        constitution_block=const_block,
                    )
                    if not discussed:
                        raw_frames = []
                    else:
                        sub_block = format_constitution_block(discussed, key_to_text)
                        raw_frames = extract_frames_from_images(
                            cfg=oai_cfg,
                            frame_id_prefix=prefix,
                            annotator_id=cfg.annotator_id,
                            dataset_name=cfg.dataset_name,
                            notes=cfg.notes,
                            pdf_filename=pdf.name,
                            page_png_b64=pages_b64,
                            clauses=discussed,
                            constitution_block=sub_block,
                        )
                else:
                    mode = "text"
                    candidates = [k for k in resolved_whitelist if plausibly_mentioned_in_text(k, full_text)]
                    if not candidates:
                        discussed = []
                        raw_frames = []
                    else:
                        const_block = format_constitution_block(candidates, key_to_text)
                        discussed = detect_discussed_clauses(
                            cfg=oai_cfg,
                            pdf_filename=pdf.name,
                            full_text=full_text,
                            allowed_keys=candidates,
                            constitution_block=const_block,
                        )
                        if not discussed:
                            raw_frames = []
                        else:
                            sub_block = format_constitution_block(discussed, key_to_text)
                            raw_frames = extract_frames_from_text(
                                cfg=oai_cfg,
                                frame_id_prefix=prefix,
                                annotator_id=cfg.annotator_id,
                                dataset_name=cfg.dataset_name,
                                notes=cfg.notes,
                                pdf_filename=pdf.name,
                                full_text=full_text,
                                clauses=discussed,
                                constitution_block=sub_block,
                            )
            else:
                if is_scanned:
                    mode = "vision"
                    pages_b64 = render_pages_as_png_b64(str(pdf), max_pages=cfg.vision_pages)
                    raw_frames = extract_frames_from_images(
                        cfg=oai_cfg,
                        frame_id_prefix=prefix,
                        annotator_id=cfg.annotator_id,
                        dataset_name=cfg.dataset_name,
                        notes=cfg.notes,
                        pdf_filename=pdf.name,
                        page_png_b64=pages_b64,
                        clauses=None,
                        constitution_block="",
                    )
                else:
                    mode = "text"
                    raw_frames = extract_frames_from_text(
                        cfg=oai_cfg,
                        frame_id_prefix=prefix,
                        annotator_id=cfg.annotator_id,
                        dataset_name=cfg.dataset_name,
                        notes=cfg.notes,
                        pdf_filename=pdf.name,
                        full_text=full_text,
                        clauses=None,
                        constitution_block="",
                    )

            dropped_n = 0
            if clauses_list and discussed:
                raw_frames, dropped_n = _post_filter_frames(
                    raw_frames,
                    source_text=full_text,
                    discussed_keys=discussed,
                    key_to_text=key_to_text,
                    is_scanned=is_scanned,
                )

            if not raw_frames:
                manifest["files"].append(
                    {
                        "pdf": pdf.name,
                        "mode": mode,
                        "pages": fast.page_count,
                        "frame_count": 0,
                        "discussed_clauses": discussed if clauses_list else None,
                        "dropped_frames": dropped_n if clauses_list else 0,
                        "output_json_files": [],
                    }
                )
                continue

            for j, raw in enumerate(raw_frames):
                clause_article = None
                cl = raw.get("clause")
                if isinstance(cl, dict):
                    clause_article = cl.get("article")
                slug = _sanitize_filename_part(str(clause_article) if clause_article else f"C{j + 1:02d}")
                raw["frame_id"] = f"{prefix}_C{j + 1:02d}__{slug}"
                raw["annotator_id"] = cfg.annotator_id
                raw.setdefault("source", {})
                raw["source"]["dataset"] = cfg.dataset_name
                raw["source"]["notes"] = cfg.notes

            _unify_case_block(raw_frames)

            validated: list[dict[str, Any]] = []
            output_paths: list[str] = []

            for j, raw_obj in enumerate(raw_frames):
                try:
                    frame = Frame.model_validate(raw_obj)
                except ValidationError:
                    raw_path = paths["json"] / f"{pdf.stem}.raw_{j + 1:02d}.json"
                    _write_json(raw_path, {"frames": raw_frames})
                    raise

                out_obj = frame.model_dump(mode="json")
                clause_article = (
                    out_obj.get("clause", {}).get("article")
                    if isinstance(out_obj.get("clause"), dict)
                    else None
                )
                slug = _sanitize_filename_part(str(clause_article) if clause_article else f"C{j + 1:02d}")
                out_path = paths["json"] / f"{pdf.stem}__{slug}.json"
                if out_path.exists():
                    out_path = paths["json"] / f"{pdf.stem}__{slug}_{j + 1:02d}.json"
                _write_json(out_path, out_obj)
                validated.append(out_obj)
                output_paths.append(str(out_path))

                if jsonl_f:
                    jsonl_f.write(json.dumps(out_obj, ensure_ascii=False) + "\n")

            manifest["files"].append(
                {
                    "pdf": pdf.name,
                    "mode": mode,
                    "pages": fast.page_count,
                    "frame_count": len(validated),
                    "discussed_clauses": discussed if clauses_list else None,
                    "dropped_frames": dropped_n if clauses_list else 0,
                    "output_json_files": output_paths,
                }
            )
    finally:
        if jsonl_f:
            jsonl_f.close()

    _write_json(cfg.output_dir / "manifest.json", manifest)
