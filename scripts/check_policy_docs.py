#!/usr/bin/env python3

from pathlib import Path
from pypdf import PdfReader

RAW_DIR = Path("policy_docs/raw")

files = sorted(RAW_DIR.glob("*"))

if not files:
    print("ERROR: no files found in policy_docs/raw")
    raise SystemExit(1)

print("Policy document check")
print("=" * 80)

ok = True

for path in files:
    size = path.stat().st_size
    print(f"\nFile: {path.name}")
    print(f"Size: {size} bytes")

    if size == 0:
        print("Status: ERROR empty file")
        ok = False
        continue

    if path.suffix.lower() == ".pdf":
        try:
            reader = PdfReader(str(path))
            print(f"Type: PDF")
            print(f"Pages: {len(reader.pages)}")

            first_text = reader.pages[0].extract_text() or ""
            first_text = " ".join(first_text.split())[:300]
            print(f"First text: {first_text}")
            print("Status: OK")
        except Exception as e:
            print(f"Status: ERROR cannot read PDF: {e}")
            ok = False
    else:
        try:
            text = path.read_text(errors="replace")
            print(f"Type: {path.suffix or 'text'}")
            print(f"Chars: {len(text)}")
            print(f"First text: {' '.join(text.split())[:300]}")
            print("Status: OK")
        except Exception as e:
            print(f"Status: ERROR cannot read text file: {e}")
            ok = False

print("\n" + "=" * 80)

if not ok:
    print("One or more files failed validation. Fix before ingestion.")
    raise SystemExit(1)

print("All policy documents are readable.")
