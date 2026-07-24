"""
Phase 3 typology coding for the Bank Drop Project.

This script creates an auditable deterministic baseline for financial-crime
typology coding. It combines Markdown note text with Phase 2 OCR text, applies
an explicit codebook of regex patterns, extracts short evidence snippets, and
summarises typologies, criminal objectives, and AML indicator candidates.

No LLM or external API is used.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = Path(os.environ.get("BANK_DROP_WORKSPACE", REPOSITORY_ROOT))
VAULT = Path(os.environ.get("BANK_DROP_VAULT", WORKSPACE / "work" / "bank_drop_project" / "DW Project"))
OUTPUTS = Path(os.environ.get("BANK_DROP_OUTPUTS_DIR", WORKSPACE / "outputs"))
PHASE1_OUTPUT = OUTPUTS / "phase1_markdown_baseline"
PHASE2_OUTPUT = OUTPUTS / "phase2_image_ocr"
PHASE3_OUTPUT = OUTPUTS / "phase3_typology_coding"


CODEBOOK = {
    "bank_log_sale": {
        "label": "Compromised bank log sale or discussion",
        "objective": "Reference bank-log or associated account-access material",
        "patterns": [
            r"\bbank\s+logs?\b",
            r"\baccount\s+logs?\b",
            r"\blogz\b",
            r"bank\s+logins?",
            r"logs?\s+with\s+(?:email|cookie|cookies|access)",
        ],
    },
    "bank_drop_sale": {
        "label": "Bank drop sale or bank-drop infrastructure",
        "objective": "Reference bank-drop or receiving-account material",
        "patterns": [
            r"\bbank\s+drops?\b",
            r"\bbankdrop\b",
            r"\bdrop\s+account\b",
            r"\bdrop\s+shop\b",
            r"fresh\s+bank\s+drop",
        ],
    },
    "fullz_identity_package": {
        "label": "Fullz or identity package",
        "objective": "Reference identity packages or credentials relevant to KYC or account access",
        "patterns": [
            r"\bfullz\b",
            r"identity package",
            r"stolen credentials?",
            r"synthetic id",
            r"personal identifiable information",
            r"\bPII\b",
            r"credit report",
        ],
    },
    "email_access_takeover": {
        "label": "Email-access-enabled account takeover",
        "objective": "Reference email, recovery, or session access alongside account access",
        "patterns": [
            r"\bemail access\b",
            r"\b(?:bank|account)\s+(?:email|mailbox)\b",
            r"\b(?:bank|account|login)\b.{0,120}\b(?:password reset|MFA|OTP|security questions?|session cookies?)\b",
            r"\b(?:password reset|MFA|OTP|security questions?|session cookies?)\b.{0,120}\b(?:bank|account|login)\b",
        ],
    },
    "mule_recruitment": {
        "label": "Mule recruitment or account-holder solicitation",
        "objective": "Reference mule or account-holder recruitment and solicitation",
        "patterns": [
            r"\bmoney mules?\b",
            r"\brecruit(?:ing|ment)?\b.{0,100}\b(?:mules?|account holders?)\b",
            r"\baccount holders?\b.{0,100}\b(?:receive|move|transfer|cash out)\b.{0,80}\b(?:funds?|money|payments?)\b",
            r"\bdirect owners?\b.{0,80}\b(?:bank|account)\b",
            r"\blooking for individuals\b.{0,100}\b(?:bank|account|receive|transfer)\b",
            r"\breal people with real bank accounts\b",
            r"\breceive wires?\b.{0,80}\b(?:fee|commission|percentage|cut)\b",
        ],
    },
    "cashout_laundering_service": {
        "label": "Cash-out or laundering service",
        "objective": "Reference cash-out, laundering, or conversion services",
        "patterns": [
            r"\bcash[\s-]?out(?:s|ing)?\b",
            r"\b(?:launder(?:ing)?|wash(?:ing)?)\b.{0,80}\b(?:money|funds?|crypto|service)\b",
            r"\b(?:dirty crypto|stolen funds?|fraud proceeds?)\b.{0,120}\b(?:clean cash|withdraw|bank transfer|wire|western union|moneygram)\b",
            r"\b(?:western union|moneygram|bank transfer|wire|ACH)\b.{0,100}\b(?:cash[\s-]?out|fee|commission|service)\b",
        ],
    },
    "crypto_payment_or_conversion": {
        "label": "Cryptocurrency payment or conversion reference",
        "objective": "Reference cryptocurrency payment, conversion, or obfuscation contexts",
        "patterns": [
            r"\b(?:bitcoin|BTC|monero|XMR|USDT|cryptocurrency|crypto)\b",
            r"\b(?:bitcoin|BTC|monero|XMR|USDT|cryptocurrency|crypto)\b.{0,100}\b(?:pay|payment|convert|exchange|cash|bank|wire|wallet|mixer|mixing)\b",
            r"\b(?:tornado cash|crypto mixer|coin mixer)\b",
        ],
    },
    "telegram_off_platform": {
        "label": "Telegram or private-channel coordination reference",
        "objective": "Reference Telegram or private channels in market-related content",
        "patterns": [
            r"\btelegram\b",
            r"\bTG\b",
            r"\bDMs?\b",
            r"\bprivate chat\b",
            r"\binvite-only\b",
        ],
    },
    "escrow_trust_reputation": {
        "label": "Escrow, trust, reputation, or scam-risk discourse",
        "objective": "Reference escrow, trust, reputation, or scam-risk discourse",
        "patterns": [
            r"escrow",
            r"multisig",
            r"multi-signature",
            r"finali[sz]e early",
            r"exit scam",
            r"trusted vendor",
            r"vouch",
            r"red flag",
            r"\bscam(?:mer|med|s)?\b",
        ],
    },
    "tutorial_training_recruitment": {
        "label": "Tutorial, guide, or training content",
        "objective": "Reference tutorial, guide, method, or training content",
        "patterns": [
            r"\b(?:tutorial|guide|method|training|course)\b",
            r"\bhow[\s-]+to\b",
            r"\bbeginners?\b",
        ],
    },
    "jurisdiction_localisation": {
        "label": "Jurisdiction-specific bank or account reference",
        "objective": "Reference jurisdiction-specific banks, accounts, drops, or logs",
        "patterns": [
            r"\b(?:Australia|Australian|New Zealand|USA|United States|Canada)\b.{0,100}\b(?:bank|account|drop|log)\b",
            r"\b(?:bank|account|drop|log)\b.{0,100}\b(?:Australia|Australian|New Zealand|USA|United States|Canada)\b",
            r"\b(?:domestic bank|local financial systems?|region-specific accounts?)\b",
        ],
    },
    "vulnerable_group_exploitation": {
        "label": "Vulnerable group or migrant/student exploitation",
        "objective": "Reference possible exploitation of financially or migration-vulnerable people",
        "patterns": [
            r"\b(?:international students?|temporary migrants?|migrants?|vulnerable (?:people|persons?|groups?))\b.{0,120}\b(?:recruit|target|exploit|account|identity|data|cash[\s-]?out|mule)\b",
            r"\b(?:recruit|target|exploit|account|identity|data|cash[\s-]?out|mule)\b.{0,120}\b(?:international students?|temporary migrants?|migrants?|vulnerable (?:people|persons?|groups?))\b",
        ],
    },
    "market_access_limitation": {
        "label": "Market access limitation, outage, login wall, or collection barrier",
        "objective": "Describe data-access constraints affecting evidence collection",
        "patterns": [
            r"requires?\s+(?:an?\s+)?account",
            r"requires?\s+login",
            r"unable to connect",
            r"connection was refused",
            r"taken offline",
            r"not responding",
            r"search function",
            r"no longer active",
        ],
    },
}


AML_INDICATORS = {
    "bank_log_plus_email_access": {
        "label": "Bank log packaged with email/cookie access",
        "patterns": [
            r"\bbank\s+logs?\b.{0,120}\bemail access\b",
            r"\bemail access\b.{0,120}\bbank\s+logs?\b",
            r"\bbank\s+logs?\b.{0,80}\b(?:session )?cookies?\b",
        ],
    },
    "domestic_account_preference": {
        "label": "Jurisdiction-specific bank or account reference",
        "patterns": [
            r"\b(?:domestic bank|local financial systems?|region-specific accounts?)\b",
            r"\b(?:Australia|Australian|New Zealand|USA|United States|Canada)\b.{0,100}\b(?:bank|account|drop|log)\b",
            r"\b(?:bank|account|drop|log)\b.{0,100}\b(?:Australia|Australian|New Zealand|USA|United States|Canada)\b",
        ],
    },
    "telegram_sales_or_proof": {
        "label": "Telegram used for vendor proof, negotiation, or sales",
        "patterns": [
            r"\btelegram\b.{0,120}\b(?:proof|vendor|group|media|contact|DMs?)\b",
            r"\b(?:vendor|proof|contact|DMs?)\b.{0,120}\btelegram\b",
        ],
    },
    "crypto_to_bank_cashout": {
        "label": "Crypto-to-bank or crypto-to-cash conversion",
        "patterns": [
            r"\b(?:bitcoin|crypto)\b.{0,120}\b(?:bank|cash|wire|western union)\b",
            r"\bdirty crypto\b.{0,120}\bclean cash\b",
        ],
    },
    "escrow_or_exit_scam_risk": {
        "label": "Escrow or exit-scam discourse",
        "patterns": [r"\bescrow\b", r"\bexit scam\b", r"\bfinali[sz]e early\b", r"\bmultisig\b"],
    },
    "mule_or_account_holder_recruitment": {
        "label": "Mule or account-holder recruitment",
        "patterns": [
            r"\bmoney mules?\b",
            r"\brecruit(?:ing|ment)?\b.{0,100}\b(?:mules?|account holders?)\b",
            r"\blooking for individuals\b.{0,100}\b(?:bank|account|receive|transfer)\b",
            r"\breal people with real bank accounts\b",
        ],
    },
}


@dataclass(frozen=True)
class Note:
    note_id: str
    relative_path: str
    source: str
    collection_date: str
    markdown_text: str
    ocr_text: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def normalise_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return text


def source_from_path(relative_path: str) -> str:
    parts = list(Path(relative_path).parts)
    root_parts = ["Project - Binary Fusion", "10. Operation GroundTruth", "Core Trace"]
    for index in range(0, max(0, len(parts) - len(root_parts)) + 1):
        if parts[index : index + len(root_parts)] == root_parts:
            source_index = index + len(root_parts)
            if source_index < len(parts) - 1:
                return parts[source_index]
    return ""


def date_from_name(name: str) -> str:
    for pattern in [r"(20\d{2})[ -]+(\d{2})[ -]+(\d{2})", r"(20\d{2})(\d{2})(\d{2})"]:
        match = re.search(pattern, name)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"
    return ""


def load_notes() -> list[Note]:
    ocr_by_note = {}
    ocr_path = PHASE2_OUTPUT / "ocr_text_by_note.csv"
    if ocr_path.exists():
        for row in read_csv(ocr_path):
            ocr_by_note[row["note_id"]] = row.get("joined_ocr_text", "")

    notes = []
    for path in sorted(VAULT.rglob("*.md")):
        # Stable across Windows and POSIX reruns. Older Phase 2 exports used
        # platform-native separators, so retain a lookup fallback while those
        # controlled artifacts remain in circulation.
        relative_path = path.relative_to(VAULT).as_posix()
        legacy_relative_path = str(path.relative_to(VAULT))
        note_id = sha256_text(relative_path)[:16]
        legacy_note_id = sha256_text(legacy_relative_path)[:16]
        markdown_text = path.read_text(encoding="utf-8", errors="replace")
        notes.append(
            Note(
                note_id=note_id,
                relative_path=relative_path,
                source=source_from_path(relative_path),
                collection_date=date_from_name(path.name),
                markdown_text=normalise_text(markdown_text),
                ocr_text=normalise_text(
                    ocr_by_note.get(note_id, ocr_by_note.get(legacy_note_id, ""))
                ),
            )
        )
    return notes


def compile_patterns(patterns: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(pattern, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns]


def short_snippet(text: str, start: int, end: int, window: int = 170) -> str:
    left = max(0, start - window)
    right = min(len(text), end + window)
    snippet = " ".join(text[left:right].split())
    # Defang obvious onion/http strings in audit snippets.
    snippet = snippet.replace("http://", "hxxp://").replace("https://", "hxxps://").replace(".onion", "[.]onion")
    return snippet[:520]


def code_text(text: str, codebook: dict) -> tuple[dict[str, int], dict[str, int], list[dict[str, object]]]:
    hit_counts = {}
    pattern_counts = {}
    snippets = []
    for code, entry in codebook.items():
        code_hits = []
        code_pattern_count = 0
        for pattern in compile_patterns(entry["patterns"]):
            matches = list(pattern.finditer(text))
            if matches:
                code_pattern_count += 1
                code_hits.extend(matches)
        hit_counts[code] = len(code_hits)
        pattern_counts[code] = code_pattern_count
        for match in code_hits[:3]:
            snippets.append(
                {
                    "code": code,
                    "matched_text": match.group(0)[:120],
                    "snippet": short_snippet(text, match.start(), match.end()),
                }
            )
    return hit_counts, pattern_counts, snippets


def rule_match_intensity_from_counts(hit_count: int, pattern_count: int, text_sources: int) -> str:
    if hit_count >= 5 and pattern_count >= 2 and text_sources >= 1:
        return "high"
    if hit_count >= 2 or pattern_count >= 2:
        return "medium"
    if hit_count == 1:
        return "low"
    return "none"


def main() -> None:
    PHASE3_OUTPUT.mkdir(parents=True, exist_ok=True)
    if not VAULT.exists():
        raise FileNotFoundError(f"Missing vault: {VAULT}")
    if not (PHASE2_OUTPUT / "ocr_text_by_note.csv").exists():
        raise FileNotFoundError("Phase 2 OCR output not found. Run Phase 2 first.")

    notes = load_notes()
    coding_rows = []
    snippet_rows = []
    aml_rows = []
    combined_rows = []

    for note in notes:
        combined_text = "\n\n".join(part for part in [note.markdown_text, note.ocr_text] if part.strip())
        markdown_present = 1 if note.markdown_text.strip() else 0
        ocr_present = 1 if note.ocr_text.strip() else 0
        text_sources = markdown_present + ocr_present
        word_count = len(re.findall(r"\b\w+\b", combined_text))

        combined_rows.append(
            {
                "note_id": note.note_id,
                "relative_path": note.relative_path,
                "source": note.source,
                "collection_date": note.collection_date,
                "markdown_present": markdown_present,
                "ocr_present": ocr_present,
                "combined_word_count": word_count,
                "combined_text_sha256": sha256_text(combined_text),
                "combined_text": combined_text,
            }
        )

        hit_counts, pattern_counts, snippets = code_text(combined_text, CODEBOOK)
        aml_hit_counts, aml_pattern_counts, aml_snippets = code_text(combined_text, AML_INDICATORS)

        for code, entry in CODEBOOK.items():
            rule_match_intensity = rule_match_intensity_from_counts(hit_counts[code], pattern_counts[code], text_sources)
            present = 1 if hit_counts[code] else 0
            coding_rows.append(
                {
                    "note_id": note.note_id,
                    "relative_path": note.relative_path,
                    "source": note.source,
                    "collection_date": note.collection_date,
                    "code": code,
                    "label": entry["label"],
                    "criminal_objective": entry["objective"],
                    "present": present,
                    "hit_count": hit_counts[code],
                    "pattern_count": pattern_counts[code],
                    "rule_match_intensity": rule_match_intensity,
                    "markdown_present": markdown_present,
                    "ocr_present": ocr_present,
                    "combined_word_count": word_count,
                }
            )

        for item in snippets:
            snippet_rows.append(
                {
                    "note_id": note.note_id,
                    "relative_path": note.relative_path,
                    "source": note.source,
                    "collection_date": note.collection_date,
                    "code": item["code"],
                    "label": CODEBOOK[item["code"]]["label"],
                    "matched_text": item["matched_text"],
                    "snippet": item["snippet"],
                }
            )

        for code, entry in AML_INDICATORS.items():
            present = 1 if aml_hit_counts[code] else 0
            aml_rows.append(
                {
                    "note_id": note.note_id,
                    "relative_path": note.relative_path,
                    "source": note.source,
                    "collection_date": note.collection_date,
                    "aml_indicator": code,
                    "label": entry["label"],
                    "present": present,
                    "hit_count": aml_hit_counts[code],
                    "pattern_count": aml_pattern_counts[code],
                    "rule_match_intensity": rule_match_intensity_from_counts(aml_hit_counts[code], aml_pattern_counts[code], text_sources),
                }
            )

    write_csv(
        PHASE3_OUTPUT / "combined_corpus_with_ocr.csv",
        combined_rows,
        [
            "note_id",
            "relative_path",
            "source",
            "collection_date",
            "markdown_present",
            "ocr_present",
            "combined_word_count",
            "combined_text_sha256",
            "combined_text",
        ],
    )
    write_csv(
        PHASE3_OUTPUT / "typology_coding_long.csv",
        coding_rows,
        [
            "note_id",
            "relative_path",
            "source",
            "collection_date",
            "code",
            "label",
            "criminal_objective",
            "present",
            "hit_count",
            "pattern_count",
            "rule_match_intensity",
            "markdown_present",
            "ocr_present",
            "combined_word_count",
        ],
    )
    write_csv(
        PHASE3_OUTPUT / "evidence_snippets.csv",
        snippet_rows,
        ["note_id", "relative_path", "source", "collection_date", "code", "label", "matched_text", "snippet"],
    )
    write_csv(
        PHASE3_OUTPUT / "aml_indicator_coding_long.csv",
        aml_rows,
        [
            "note_id",
            "relative_path",
            "source",
            "collection_date",
            "aml_indicator",
            "label",
            "present",
            "hit_count",
            "pattern_count",
            "rule_match_intensity",
        ],
    )

    summary_by_code = defaultdict(Counter)
    summary_by_source_code = defaultdict(Counter)
    objective_summary = defaultdict(Counter)
    aml_summary = defaultdict(Counter)

    for row in coding_rows:
        if int(row["present"]):
            code = row["code"]
            source = row["source"] or "(no_source)"
            objective = row["criminal_objective"]
            summary_by_code[code]["note_count"] += 1
            summary_by_code[code]["hit_count"] += int(row["hit_count"])
            summary_by_code[code][row["rule_match_intensity"]] += 1
            summary_by_source_code[(source, code)]["note_count"] += 1
            summary_by_source_code[(source, code)]["hit_count"] += int(row["hit_count"])
            if code != "market_access_limitation":
                objective_summary[objective]["note_count"] += 1
                objective_summary[objective]["hit_count"] += int(row["hit_count"])

    for row in aml_rows:
        if int(row["present"]):
            indicator = row["aml_indicator"]
            source = row["source"] or "(no_source)"
            aml_summary[(indicator, source)]["note_count"] += 1
            aml_summary[(indicator, source)]["hit_count"] += int(row["hit_count"])

    write_csv(
        PHASE3_OUTPUT / "typology_summary.csv",
        [
            {
                "code": code,
                "label": CODEBOOK[code]["label"],
                "criminal_objective": CODEBOOK[code]["objective"],
                "note_count": counter["note_count"],
                "hit_count": counter["hit_count"],
                "high_rule_match_intensity_notes": counter["high"],
                "medium_rule_match_intensity_notes": counter["medium"],
                "low_rule_match_intensity_notes": counter["low"],
            }
            for code, counter in sorted(summary_by_code.items(), key=lambda item: (-item[1]["note_count"], item[0]))
        ],
        [
            "code",
            "label",
            "criminal_objective",
            "note_count",
            "hit_count",
            "high_rule_match_intensity_notes",
            "medium_rule_match_intensity_notes",
            "low_rule_match_intensity_notes",
        ],
    )
    write_csv(
        PHASE3_OUTPUT / "typology_summary_by_source.csv",
        [
            {
                "source": source,
                "code": code,
                "label": CODEBOOK[code]["label"],
                "note_count": counter["note_count"],
                "hit_count": counter["hit_count"],
            }
            for (source, code), counter in sorted(
                summary_by_source_code.items(), key=lambda item: (item[0][0], -item[1]["note_count"], item[0][1])
            )
        ],
        ["source", "code", "label", "note_count", "hit_count"],
    )
    write_csv(
        PHASE3_OUTPUT / "criminal_objective_summary.csv",
        [
            {
                "criminal_objective": objective,
                "note_count": counter["note_count"],
                "hit_count": counter["hit_count"],
            }
            for objective, counter in sorted(objective_summary.items(), key=lambda item: (-item[1]["note_count"], item[0]))
        ],
        ["criminal_objective", "note_count", "hit_count"],
    )
    write_csv(
        PHASE3_OUTPUT / "aml_indicator_summary_by_source.csv",
        [
            {
                "aml_indicator": indicator,
                "label": AML_INDICATORS[indicator]["label"],
                "source": source,
                "note_count": counter["note_count"],
                "hit_count": counter["hit_count"],
            }
            for (indicator, source), counter in sorted(
                aml_summary.items(), key=lambda item: (item[0][0], -item[1]["note_count"], item[0][1])
            )
        ],
        ["aml_indicator", "label", "source", "note_count", "hit_count"],
    )

    codebook_md = ["# Phase 3 Typology Codebook", "", "Deterministic regex-based coding. No LLM or external API was used.", ""]
    for code, entry in CODEBOOK.items():
        codebook_md.extend(
            [
                f"## {code}",
                f"- Label: {entry['label']}",
                f"- Criminal objective: {entry['objective']}",
                "- Patterns:",
            ]
        )
        codebook_md.extend([f"  - `{pattern}`" for pattern in entry["patterns"]])
        codebook_md.append("")
    codebook_md.extend(["# AML Indicator Candidates", ""])
    for code, entry in AML_INDICATORS.items():
        codebook_md.extend([f"## {code}", f"- Label: {entry['label']}", "- Patterns:"])
        codebook_md.extend([f"  - `{pattern}`" for pattern in entry["patterns"]])
        codebook_md.append("")
    (PHASE3_OUTPUT / "CODEBOOK_PHASE3.md").write_text("\n".join(codebook_md), encoding="utf-8")

    metadata = {
        "phase": "phase3_typology_coding",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "vault_path": str(VAULT),
        "phase2_output_path": str(PHASE2_OUTPUT),
        "phase3_output_path": str(PHASE3_OUTPUT),
        "note_count": len(notes),
        "typology_code_count": len(CODEBOOK),
        "aml_indicator_count": len(AML_INDICATORS),
        "coding_rows": len(coding_rows),
        "evidence_snippet_rows": len(snippet_rows),
        "aml_coding_rows": len(aml_rows),
    }
    (PHASE3_OUTPUT / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    checkpoint = f"""# Phase 3 Typology Coding Checkpoint

## What Was Produced

Phase 3 combined Markdown text with Phase 2 OCR text and applied a deterministic typology codebook for financial-crime analysis.

## Key Counts

- Notes coded: {len(notes)}
- Typology codes: {len(CODEBOOK)}
- AML indicator candidates: {len(AML_INDICATORS)}
- Typology coding rows: {len(coding_rows)}
- Evidence snippet rows: {len(snippet_rows)}
- AML indicator coding rows: {len(aml_rows)}

## Main Output Files

- `combined_corpus_with_ocr.csv`
- `typology_coding_long.csv`
- `typology_summary.csv`
- `typology_summary_by_source.csv`
- `criminal_objective_summary.csv`
- `aml_indicator_coding_long.csv`
- `aml_indicator_summary_by_source.csv`
- `evidence_snippets.csv`
- `CODEBOOK_PHASE3.md`
- `run_metadata.json`

## Interpretation Limits

This is an auditable baseline coding, not a final qualitative interpretation. Regex rules can produce false positives and false negatives, especially in noisy OCR text. Journal-grade findings should use this table for sampling, manual validation, and later interpretive analysis.
"""
    (PHASE3_OUTPUT / "PHASE3_CHECKPOINT_SUMMARY.md").write_text(checkpoint, encoding="utf-8")

    zip_base = PHASE3_OUTPUT.parent / "phase3_typology_coding_outputs"
    zip_path = Path(str(zip_base) + ".zip")
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(zip_base), "zip", PHASE3_OUTPUT)

    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
