import os
import csv
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin

from bs4 import BeautifulSoup  # type: ignore


BASE_DIR = r"C:\Users\abc\Pictures\code"
INPUT_DIR = os.path.join(BASE_DIR, "chay")
OUTPUT_CSV = os.path.join(BASE_DIR, "same_day_products_from_html.csv")


def read_file_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def find_container_with_lead_time(node) -> Optional[object]:
    current = node
    for _ in range(6):
        if not current:
            return None
        lead = current.find(class_="PriceLeadTime_leadTime__airE7")
        if lead is not None:
            return current
        current = getattr(current, "parent", None)
    return None


def extract_text(el) -> str:
    if not el:
        return ""
    text = el.get_text(" ", strip=True)
    if text:
        return text
    title = el.get("title")
    return title.strip() if isinstance(title, str) else ""


def normalize_url(href: Optional[str], base_url: str = "https://vn.misumi-ec.com") -> str:
    if not href:
        return ""
    try:
        return urljoin(base_url, href)
    except Exception:
        return href


def parse_html_file(file_path: str) -> List[Dict[str, str]]:
    html = read_file_text(file_path)
    soup = BeautifulSoup(html, "html.parser")

    results: List[Dict[str, str]] = []

    # Strategy: iterate anchors with series link class, then validate Same Day within a nearby/ancestor container
    for a in soup.find_all("a", class_="PhotoItem_seriesNameLink__9PQQh"):
        container = find_container_with_lead_time(a)
        if not container:
            # Fallback: look within the same parent chain up to 2 levels for lead time block
            container = a.parent if a else None
        if not container:
            continue

        lead_el = container.find(class_="PriceLeadTime_leadTime__airE7") if container else None
        lead_text = extract_text(lead_el)
        if "same day" not in lead_text.lower():
            continue

        name_el = container.find(class_="PhotoItem_tooltips__Zif27")
        name = extract_text(name_el) or extract_text(a)
        link = normalize_url(a.get("href"))

        if not name and not link:
            continue

        results.append({
            "Name": name,
            "Product URL": link,
        })

    return results


def collect_html_files(limit: int = 10) -> List[str]:
    if not os.path.isdir(INPUT_DIR):
        return []
    entries = [
        os.path.join(INPUT_DIR, f)
        for f in os.listdir(INPUT_DIR)
        if f.lower().endswith(".html") or f.lower().endswith(".htm")
    ]
    entries.sort()
    return entries[:limit]


def save_to_csv(rows: List[Dict[str, str]], output_csv: str) -> None:
    if not rows:
        # Create an empty file with headers for consistency
        headers = ["Name", "Product URL"]
        with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
        return

    headers = ["Name", "Product URL"]
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def deduplicate_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen: Set[str] = set()
    deduped: List[Dict[str, str]] = []
    for row in rows:
        key = f"{row.get('Name','').strip()}|{row.get('Product URL','').strip()}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def main() -> None:
    html_files = collect_html_files(limit=10)
    if not html_files:
        print(f"No HTML files found in {INPUT_DIR}")
        save_to_csv([], OUTPUT_CSV)
        return

    all_rows: List[Dict[str, str]] = []
    for idx, file_path in enumerate(html_files, start=1):
        print(f"Processing {idx}/{len(html_files)}: {file_path}")
        try:
            rows = parse_html_file(file_path)
            all_rows.extend(rows)
        except Exception as e:
            print(f"  Error parsing {file_path}: {e}")

    all_rows = deduplicate_rows(all_rows)
    save_to_csv(all_rows, OUTPUT_CSV)
    print(f"Saved {len(all_rows)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()


