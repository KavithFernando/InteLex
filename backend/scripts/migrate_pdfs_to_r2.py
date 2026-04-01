"""
One-time migration: upload all local PDFs to Cloudflare R2 and update the DB.

Run from the backend/ directory:
    python -m scripts.migrate_pdfs_to_r2

Requires the following env vars (add to backend/.env before running):
    R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
    R2_BUCKET_NAME, R2_PUBLIC_URL
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# ── Bootstrap path so imports work when run as a script ───────────────────────
_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

load_dotenv(_BACKEND_DIR / ".env")

from config.settings import (  # noqa: E402
    PDF_DIR,
    R2_ACCOUNT_ID,
    R2_ACCESS_KEY_ID,
    R2_BUCKET_NAME,
    R2_PUBLIC_URL,
    R2_SECRET_ACCESS_KEY,
)
from db.connection import get_connection  # noqa: E402


def _r2_client():
    if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        raise RuntimeError(
            "R2 credentials not set. Add R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, "
            "R2_SECRET_ACCESS_KEY to backend/.env"
        )
    return boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def _object_exists(s3, key: str) -> bool:
    try:
        s3.head_object(Bucket=R2_BUCKET_NAME, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise


def main() -> None:
    if not R2_PUBLIC_URL:
        raise RuntimeError("R2_PUBLIC_URL is not set in backend/.env")

    pdf_dir = Path(PDF_DIR)
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {pdf_dir}")
        return

    print(f"Found {len(pdfs)} PDF(s) in {pdf_dir}")
    s3 = _r2_client()

    conn = get_connection()
    cur = conn.cursor()

    uploaded = skipped = updated = no_case = errors = 0

    for pdf_path in pdfs:
        filename = pdf_path.name
        r2_key = f"pdfs/{filename}"
        public_url = f"{R2_PUBLIC_URL.rstrip('/')}/{r2_key}"

        # Upload to R2
        try:
            if _object_exists(s3, r2_key):
                print(f"  [SKIP]   {filename} — already in R2")
                skipped += 1
            else:
                with open(pdf_path, "rb") as f:
                    s3.put_object(
                        Bucket=R2_BUCKET_NAME,
                        Key=r2_key,
                        Body=f.read(),
                        ContentType="application/pdf",
                    )
                print(f"  [UPLOAD] {filename}")
                uploaded += 1
        except Exception as exc:
            print(f"  [ERROR]  {filename} — upload failed: {exc}")
            errors += 1
            continue

        # Update matching case row in DB
        # The legacy pdf_relative_path stores just the filename (no path prefix)
        cur.execute(
            "SELECT id, pdf_relative_path FROM cases WHERE pdf_relative_path = %s",
            (filename,),
        )
        rows = cur.fetchall()

        if not rows:
            # Also try with a path prefix in case it was stored that way
            cur.execute(
                "SELECT id, pdf_relative_path FROM cases WHERE pdf_relative_path LIKE %s",
                (f"%{filename}",),
            )
            rows = cur.fetchall()

        if not rows:
            print(f"           └─ WARNING: no case row found for {filename!r}")
            no_case += 1
            continue

        for row in rows:
            case_id, old_path = row[0], row[1]
            cur.execute(
                "UPDATE cases SET pdf_relative_path = %s WHERE id = %s",
                (public_url, case_id),
            )
            print(f"           └─ Updated case id={case_id}: {old_path!r} → R2 URL")
            updated += 1

    conn.commit()
    cur.close()
    conn.close()

    print("\n── Migration complete ─────────────────────────────────────────")
    print(f"  Uploaded  : {uploaded}")
    print(f"  Skipped   : {skipped} (already existed in R2)")
    print(f"  DB rows updated: {updated}")
    print(f"  No DB match    : {no_case}  ← check these manually")
    print(f"  Errors         : {errors}")


if __name__ == "__main__":
    main()
