"""
Create compact Phase 1 summary tables from extracted CSV files.

The summary outputs are designed for quick review and later inclusion in
methods appendices or journal-supporting materials.
"""

from __future__ import annotations

import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = Path(os.environ.get("BANK_DROP_WORKSPACE", REPOSITORY_ROOT))
OUTPUTS = Path(os.environ.get("BANK_DROP_OUTPUTS_DIR", WORKSPACE / "outputs"))
PHASE1_OUTPUT = OUTPUTS / "phase1_markdown_baseline"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    corpus = read_csv(PHASE1_OUTPUT / "corpus_index.csv")
    keywords = read_csv(PHASE1_OUTPUT / "keyword_counts_long.csv")
    entities = read_csv(PHASE1_OUTPUT / "entity_mentions_long.csv")
    prices = read_csv(PHASE1_OUTPUT / "price_mentions.csv")
    images = read_csv(PHASE1_OUTPUT / "image_references.csv")

    keyword_totals: dict[str, Counter] = defaultdict(Counter)
    for row in keywords:
        source = row["source"] or "(no_source)"
        keyword = row["keyword"]
        count = int(row["count"])
        present = int(row["present"])
        keyword_totals[(source, keyword)]["hit_count"] += count
        keyword_totals[(source, keyword)]["file_count"] += present

    keyword_rows = [
        {
            "source": source,
            "keyword": keyword,
            "file_count": counter["file_count"],
            "hit_count": counter["hit_count"],
        }
        for (source, keyword), counter in sorted(keyword_totals.items())
    ]
    write_csv(
        PHASE1_OUTPUT / "keyword_summary_by_source.csv",
        keyword_rows,
        ["source", "keyword", "file_count", "hit_count"],
    )

    entity_totals: dict[tuple[str, str, str], int] = Counter()
    for row in entities:
        source = row["source"] or "(no_source)"
        entity_totals[(source, row["entity_type"], row["entity"])] += int(row["count"])
    entity_rows = [
        {
            "source": source,
            "entity_type": entity_type,
            "entity": entity,
            "hit_count": count,
        }
        for (source, entity_type, entity), count in entity_totals.most_common()
    ]
    write_csv(
        PHASE1_OUTPUT / "entity_summary_by_source.csv",
        entity_rows,
        ["source", "entity_type", "entity", "hit_count"],
    )

    amounts_by_currency: dict[str, list[float]] = defaultdict(list)
    amount_counter = Counter()
    currency_counter = Counter()
    source_price_counter = Counter()
    for row in prices:
        amount = float(row["amount"])
        currency = row["currency"]
        amounts_by_currency[currency].append(amount)
        amount_counter[(currency, amount)] += 1
        currency_counter[currency] += 1
        source_price_counter[row["source"] or "(no_source)"] += 1

    top_price_rows = [
        {"currency": currency, "amount": f"{amount:.8f}".rstrip("0").rstrip("."), "mention_count": count}
        for (currency, amount), count in amount_counter.most_common(50)
    ]
    write_csv(PHASE1_OUTPUT / "top_price_amounts.csv", top_price_rows, ["currency", "amount", "mention_count"])

    image_exists = Counter(row["image_exists_in_vault_root"] for row in images)
    overall = {
        "note_count": len(corpus),
        "source_count": len({row["source"] for row in corpus if row["source"]}),
        "image_reference_count": len(images),
        "image_reference_existing_count": image_exists["1"],
        "image_reference_missing_or_external_count": image_exists["0"],
        "price_mention_count": len(prices),
        "entity_mention_rows": len(entities),
        "keyword_rows": len(keywords),
        "price_mentions_by_currency": dict(currency_counter.most_common()),
        "price_range_by_currency": {
            currency: {"min": min(values), "max": max(values)}
            for currency, values in sorted(amounts_by_currency.items())
        },
    }

    source_note_counts = Counter(row["source"] or "(no_source)" for row in corpus)
    overall["source_note_counts"] = dict(source_note_counts.most_common())
    overall["price_mentions_by_source"] = dict(source_price_counter.most_common())

    (PHASE1_OUTPUT / "phase1_summary.json").write_text(
        json.dumps(overall, indent=2), encoding="utf-8"
    )
    print(json.dumps(overall, indent=2))


if __name__ == "__main__":
    main()
