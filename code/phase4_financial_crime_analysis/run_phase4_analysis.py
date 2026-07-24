"""
Phase 4 financial-crime analysis for the Bank Drop Project.

This script synthesises Phase 3 deterministic coding into an interpretive but
auditable financial-crime analysis package. It does not call an external LLM or
API. It creates report-ready Markdown and CSV outputs grounded in the Phase 3
tables and short evidence snippets.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = Path(os.environ.get("BANK_DROP_WORKSPACE", REPOSITORY_ROOT))
OUTPUTS = Path(os.environ.get("BANK_DROP_OUTPUTS_DIR", WORKSPACE / "outputs"))
PHASE1_OUTPUT = OUTPUTS / "phase1_markdown_baseline"
PHASE2_OUTPUT = OUTPUTS / "phase2_image_ocr"
PHASE3_OUTPUT = OUTPUTS / "phase3_typology_coding"
PHASE4_OUTPUT = OUTPUTS / "phase4_financial_crime_analysis"

DATA_QUALITY_CODES = {"market_access_limitation"}


FINDING_NARRATIVES = {
    "cashout_laundering_service": {
        "finding": "Cash-out and laundering-service terms appear in the provisional rule-based coding.",
        "analysis": (
            "The rule-based coding identifies terms concerning cash-out, laundering, and conversion services. "
            "These lexical matches are consistent with a downstream-monetisation hypothesis, but they do not show that a service was genuine, supplied, or used. "
            "The completed ICR supports coder consistency, but direct contextual evidence and close reading remain required before making a substantive movement-of-value claim."
        ),
        "result_type": "Can support a typology of conversion services and post-compromise monetisation.",
        "controls": "Monitor abrupt inbound/outbound movement, beneficiary changes, mule-like receiving behaviour, and crypto-to-bank conversion narratives.",
    },
    "bank_log_sale": {
        "finding": "Bank-log sale or discussion terms are the most frequent provisional typology.",
        "analysis": (
            "Bank-log material indicates demand for access to existing accounts rather than only newly opened accounts. "
            "The operational risk is account takeover followed by rapid monetisation, especially where logs are bundled "
            "with recovery-channel access."
        ),
        "result_type": "Can support a typology of account-takeover commodity markets.",
        "controls": "Prioritise unusual device/session, geolocation, cookie/session reuse, and recovery-channel changes.",
    },
    "telegram_off_platform": {
        "finding": "Telegram and private-channel references appear in market-related records.",
        "analysis": (
            "The rule identifies Telegram or private-channel terms in market-related text. It does not by itself show that negotiation, proof, "
            "or transaction coordination moved elsewhere. Human review is required before interpreting off-platform migration; "
            "captured forum material may omit context outside the retained record."
        ),
        "result_type": "Can support a validation target concerning private-channel references and possible coordination.",
        "controls": "Treat open-forum posts as lead generation; do not assume the whole transaction is visible in the captured page.",
    },
    "tutorial_training_recruitment": {
        "finding": "Tutorial/method/training material is substantial.",
        "analysis": (
            "The dataset includes content that appears to lower barriers to entry or package criminal knowledge. "
            "This supports analysis of capability diffusion, recruitment, and monetisation of know-how, not just commodity sales."
        ),
        "result_type": "Can support a typology of criminal learning and recruitment infrastructure.",
        "controls": "Consider education-style material as a risk amplifier that can expand participation and standardise methods.",
    },
    "jurisdiction_localisation": {
        "finding": "Jurisdiction and domestic-account terms appear across sources.",
        "analysis": (
            "The rule-based coding records country and local-bank terms near bank, account, drop, or log terms. "
            "It does not establish actor preference, reduced scrutiny, or completed domestic or cross-border money movement."
        ),
        "result_type": "Can support analysis of localised mule/drop demand and geography-specific bank targeting.",
        "controls": "Assess domestic receiving-account patterns, especially where victim geography and receiving-account geography align.",
    },
    "crypto_payment_or_conversion": {
        "finding": "Cryptocurrency payment and conversion terms appear in the provisional coding.",
        "analysis": (
            "Crypto references occur alongside cash-out, escrow, and market-payment language. This suggests crypto is not just a payment method "
            "or was actually converted, obfuscated, or settled; those are hypotheses for human review."
        ),
        "result_type": "Can support analysis of crypto-to-fiat conversion points and settlement rails.",
        "controls": "Focus on fiat off-ramp points, exchange account misuse, rapid movement after crypto conversion, and mule account inflows.",
    },
    "escrow_trust_reputation": {
        "finding": "Escrow, trust, reputation, and scam-risk discourse are prominent.",
        "analysis": (
            "A large trust-risk signal means the dataset also captures criminal-market governance problems. "
            "This is analytically important because some listings may be scams against other offenders, copied listings, or reputation-building content."
        ),
        "result_type": "Can support assessment of marketplace reliability and deception within illicit markets.",
        "controls": "Avoid treating all listings as real inventory; code credibility, repetition, escrow claims, and scam warnings separately.",
    },
    "fullz_identity_package": {
        "finding": "Fullz and identity-package terms appear frequently in the provisional coding.",
        "analysis": (
            "Fullz/identity signals connect bank drops and account takeover to KYC bypass, impersonation, account opening, and recovery-channel control. "
            "This is a key bridge between data theft and financial crime."
        ),
        "result_type": "Can support analysis of identity-enabled financial-crime workflows.",
        "controls": "Monitor identity-document reuse, abnormal KYC metadata, email/phone changes, and synthetic identity patterns.",
    },
    "bank_drop_sale": {
        "finding": "Bank-drop terms appear frequently in the provisional coding.",
        "analysis": (
            "Bank-drop signals indicate demand for accounts that can receive, hold, or move funds. "
            "This aligns with mule/drop account misuse and may include both compromised accounts and accounts opened or controlled for criminal use."
        ),
        "result_type": "Can support a bank-drop/mule-account typology.",
        "controls": "Look for newly active dormant accounts, inbound third-party funds, rapid onward transfer, and mismatch between customer profile and transaction behaviour.",
    },
    "email_access_takeover": {
        "finding": "Email access is a recurring enhancer of bank-log/account-takeover risk.",
        "analysis": (
            "Email access can strengthen persistence and allow control over password resets, notifications, and recovery paths. "
            "Where bank access and email access appear together, the account-takeover risk is materially higher."
        ),
        "result_type": "Can support an enhanced-risk sub-typology of bank log plus recovery-channel compromise.",
        "controls": "Treat email-change, inbox-rule, recovery-channel, and MFA-reset events as linked financial-crime risk indicators.",
    },
    "mule_recruitment": {
        "finding": "Mule/account-holder recruitment is present but less frequent than commodity and cash-out signals.",
        "analysis": (
            "The lower count does not mean low importance. Mule recruitment can be episodic, coded, or shifted to private channels. "
            "The signal is sufficient to support a targeted sub-analysis rather than a dominant dataset-wide claim."
        ),
        "result_type": "Can support a focused account-holder recruitment sub-study.",
        "controls": "Assess direct-owner language, long-term loading claims, account-age preferences, and payment-for-use narratives.",
    },
    "vulnerable_group_exploitation": {
        "finding": "Explicit vulnerable migrant/student exploitation is rare in the captured text.",
        "analysis": (
            "The project rationale is strongly concerned with migrants and vulnerable groups, but deterministic coding finds only a small explicit signal. "
            "This should be reported carefully: the dataset may still contain indirect evidence, but Phase 3 does not support broad prevalence claims without manual review."
        ),
        "result_type": "Can support a research gap/targeted sampling question, not a broad prevalence conclusion yet.",
        "controls": "Use manual sampling and targeted searches before making claims about migrant/student exploitation prevalence.",
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def md_table(headers: list[str], rows: list[list[object]]) -> str:
    out = []
    out.append("| " + " | ".join(headers) + " |")
    out.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        out.append("| " + " | ".join(str(item).replace("|", "\\|") for item in row) + " |")
    return "\n".join(out)


def top_by_source(source_rows: list[dict[str, str]], source: str, limit: int = 5) -> list[dict[str, str]]:
    rows = [row for row in source_rows if row["source"] == source]
    return sorted(rows, key=lambda r: int(r["note_count"]), reverse=True)[:limit]


def pick_snippets(snippet_rows: list[dict[str, str]], code: str, limit: int = 3) -> list[str]:
    selected = []
    seen = set()
    for row in snippet_rows:
        if row["code"] != code:
            continue
        text = row["snippet"].strip()
        key = text[:120].lower()
        if text and key not in seen:
            selected.append(text)
            seen.add(key)
        if len(selected) >= limit:
            break
    return selected


def main() -> None:
    PHASE4_OUTPUT.mkdir(parents=True, exist_ok=True)
    required = [
        PHASE3_OUTPUT / "typology_summary.csv",
        PHASE3_OUTPUT / "typology_summary_by_source.csv",
        PHASE3_OUTPUT / "criminal_objective_summary.csv",
        PHASE3_OUTPUT / "aml_indicator_summary_by_source.csv",
        PHASE3_OUTPUT / "evidence_snippets.csv",
        PHASE3_OUTPUT / "run_metadata.json",
    ]
    for path in required:
        if not path.exists():
            raise FileNotFoundError(f"Missing required Phase 3 file: {path}")

    typology = [row for row in read_csv(PHASE3_OUTPUT / "typology_summary.csv") if row["code"] not in DATA_QUALITY_CODES]
    source_typology = [
        row for row in read_csv(PHASE3_OUTPUT / "typology_summary_by_source.csv") if row["code"] not in DATA_QUALITY_CODES
    ]
    objectives = read_csv(PHASE3_OUTPUT / "criminal_objective_summary.csv")
    aml = read_csv(PHASE3_OUTPUT / "aml_indicator_summary_by_source.csv")
    snippets = read_csv(PHASE3_OUTPUT / "evidence_snippets.csv")
    phase3_meta = json.loads((PHASE3_OUTPUT / "run_metadata.json").read_text(encoding="utf-8"))

    findings_rows = []
    for rank, row in enumerate(typology, start=1):
        code = row["code"]
        narrative = FINDING_NARRATIVES.get(
            code,
            {
                "finding": row["label"],
                "analysis": "This typology appears in the deterministic coding results and requires manual review.",
                "result_type": "Exploratory signal.",
                "controls": "Manual validation required.",
            },
        )
        findings_rows.append(
            {
                "rank": rank,
                "code": code,
                "label": row["label"],
                "note_count": row["note_count"],
                "hit_count": row["hit_count"],
                "finding": narrative["finding"],
                "analysis": narrative["analysis"],
                "result_type": narrative["result_type"],
                "aml_or_detection_relevance": narrative["controls"],
            }
        )

    write_csv(
        PHASE4_OUTPUT / "financial_crime_findings.csv",
        findings_rows,
        [
            "rank",
            "code",
            "label",
            "note_count",
            "hit_count",
            "finding",
            "analysis",
            "result_type",
            "aml_or_detection_relevance",
        ],
    )

    aml_totals = defaultdict(Counter)
    for row in aml:
        aml_totals[row["aml_indicator"]]["note_count"] += int(row["note_count"])
        aml_totals[row["aml_indicator"]]["hit_count"] += int(row["hit_count"])
        aml_totals[row["aml_indicator"]]["sources"] += 1
        aml_totals[row["aml_indicator"]]["label"] = row["label"]

    aml_rows = [
        {
            "rank": rank,
            "aml_indicator": indicator,
            "label": counter["label"],
            "source_count": counter["sources"],
            "note_count": counter["note_count"],
            "hit_count": counter["hit_count"],
            "interpretation": interpretation_for_aml(indicator),
        }
        for rank, (indicator, counter) in enumerate(
            sorted(aml_totals.items(), key=lambda item: (-item[1]["note_count"], item[0])), start=1
        )
    ]
    write_csv(
        PHASE4_OUTPUT / "aml_red_flags_summary.csv",
        aml_rows,
        ["rank", "aml_indicator", "label", "source_count", "note_count", "hit_count", "interpretation"],
    )

    sources = sorted({row["source"] for row in source_typology})
    source_profile_rows = []
    for source in sources:
        top = top_by_source(source_typology, source, limit=5)
        source_profile_rows.append(
            {
                "source": source,
                "top_typologies": "; ".join(f"{row['code']} ({row['note_count']} notes)" for row in top),
                "dominant_typology": top[0]["code"] if top else "",
                "dominant_typology_notes": top[0]["note_count"] if top else "",
            }
        )
    write_csv(
        PHASE4_OUTPUT / "source_profile_summary.csv",
        source_profile_rows,
        ["source", "dominant_typology", "dominant_typology_notes", "top_typologies"],
    )

    recommendations = [
        {
            "priority": 1,
            "recommendation": "Validate top typologies with manual sampling before publication claims.",
            "reason": "Regex and OCR signals are strong for mapping but can include false positives or duplicated marketplace text.",
        },
        {
            "priority": 2,
            "recommendation": "Treat migrant/student exploitation as a targeted sub-analysis rather than a dataset-wide finding at this stage.",
            "reason": "Explicit vulnerable-group coding is low relative to other typologies.",
        },
        {
            "priority": 3,
            "recommendation": "Separate commodity-sale evidence from cash-out and laundering-service evidence in the article.",
            "reason": "The dataset captures both upstream account/data supply and downstream monetisation.",
        },
        {
            "priority": 4,
            "recommendation": "Use source profiles to select a stratified manual-validation sample.",
            "reason": "Different sources concentrate different signals, especially Pitch, Meta Banklogs, X Wave Market, Tor Shop, and Dread.",
        },
        {
            "priority": 5,
            "recommendation": "Report marketplace reliability and scam discourse as a finding, not only a limitation.",
            "reason": "Escrow, exit-scam, trust, and vendor-proof signals are part of the criminal-market ecology.",
        },
    ]
    write_csv(PHASE4_OUTPUT / "phase4_recommendations.csv", recommendations, ["priority", "recommendation", "reason"])

    report = build_report(typology, objectives, aml_rows, source_profile_rows, snippets, phase3_meta)
    (PHASE4_OUTPUT / "FINANCIAL_CRIME_ANALYSIS_REPORT.md").write_text(report, encoding="utf-8")

    checkpoint = f"""# Phase 4 Financial-Crime Analysis Checkpoint

## What Was Produced

Phase 4 converted the Phase 3 deterministic coding into an interpretive financial-crime analysis package.

## Key Inputs

- Notes coded in Phase 3: {phase3_meta.get('note_count')}
- Typology codes: {phase3_meta.get('typology_code_count')}
- AML indicator candidates: {phase3_meta.get('aml_indicator_count')}
- Evidence snippets available: {phase3_meta.get('evidence_snippet_rows')}

## Main Output Files

- `FINANCIAL_CRIME_ANALYSIS_REPORT.md`
- `financial_crime_findings.csv`
- `aml_red_flags_summary.csv`
- `source_profile_summary.csv`
- `phase4_recommendations.csv`
- `PHASE4_CHECKPOINT_SUMMARY.md`
- `run_metadata.json`

## Interpretation Limits

Phase 4 is an analytical synthesis based on deterministic Phase 3 coding. It should be treated as a structured first interpretation and should be manually validated before journal submission.
"""
    (PHASE4_OUTPUT / "PHASE4_CHECKPOINT_SUMMARY.md").write_text(checkpoint, encoding="utf-8")

    metadata = {
        "phase": "phase4_financial_crime_analysis",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_boundary": "controlled Phase 1-3 outputs",
        "output_boundary": "controlled Phase 4 output; local path not released",
        "typology_count": len(typology),
        "objective_count": len(objectives),
        "aml_indicator_count": len(aml_rows),
        "source_profile_count": len(source_profile_rows),
        "finding_count": len(findings_rows),
    }
    (PHASE4_OUTPUT / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    zip_base = PHASE4_OUTPUT.parent / "phase4_financial_crime_analysis_outputs"
    zip_path = Path(str(zip_base) + ".zip")
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(zip_base), "zip", PHASE4_OUTPUT)

    print(json.dumps(metadata, indent=2))


def interpretation_for_aml(indicator: str) -> str:
    mapping = {
        "bank_log_plus_email_access": "Rule match for bank-log terms near email or cookie-access terms; expert review must determine account-takeover relevance.",
        "domestic_account_preference": "Rule match for jurisdiction terms near bank, account, drop, or log terms; it does not establish preference or evasion intent.",
        "telegram_sales_or_proof": "Rule match for Telegram near vendor, proof, contact, or direct-message terms; it does not establish negotiation or a transaction.",
        "crypto_to_bank_cashout": "Rule match for cryptocurrency near bank, cash, wire, or conversion terms; it does not establish conversion or money movement.",
        "escrow_or_exit_scam_risk": "Rule match for escrow, exit-scam, finalise-early, or multisig terms; it does not establish listing reliability or transaction behaviour.",
        "mule_or_account_holder_recruitment": "Rule match for explicit mule, recruitment, or account-holder language; human review must confirm recruitment context.",
    }
    return mapping.get(indicator, "Manual interpretation required.")


def build_report(typology, objectives, aml_rows, source_profiles, snippets, phase3_meta) -> str:
    lines = []
    lines.append("# Financial Crime Analysis Report")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(
        "The rule-based analysis identifies a range of content signals around bank logs, bank drops, identity packages, "
        "cash-out services, crypto conversion, Telegram/private-channel references, and criminal-market trust terms. "
        "These lexical patterns motivate hypotheses about account access and conversion, but they do not establish genuine services or movement "
        "of value."
    )
    lines.append("")
    lines.append(
        "This report is based on deterministic Phase 3 coding over Markdown notes plus OCR text. It should be read as a "
        "structured first interpretation rather than a final qualitative conclusion. The strongest publication path is to "
        "use these findings to guide manual validation and targeted close reading."
    )
    lines.append("")

    lines.append("## Data And Method Boundary")
    lines.append("")
    lines.append(
        f"Phase 3 coded {phase3_meta.get('note_count')} notes using {phase3_meta.get('typology_code_count')} typology codes "
        f"and {phase3_meta.get('aml_indicator_count')} AML indicator candidates. Evidence snippets available for audit: "
        f"{phase3_meta.get('evidence_snippet_rows')}."
    )
    lines.append("")
    lines.append(
        "The method is deliberately conservative: Phase 1 indexed Markdown, Phase 2 OCR'd screenshots, Phase 3 applied a "
        "deterministic codebook, and Phase 4 synthesises those outputs. No external LLM or external API was used in Phase 4."
    )
    lines.append("")

    lines.append("## Ranked Typology Findings")
    lines.append("")
    lines.append(md_table(["Rank", "Typology", "Notes", "Hits"], [[i, row["label"], row["note_count"], row["hit_count"]] for i, row in enumerate(typology, 1)]))
    lines.append("")

    lines.append("## Criminal Objectives")
    lines.append("")
    lines.append(md_table(["Rank", "Criminal objective", "Notes", "Hits"], [[i, row["criminal_objective"], row["note_count"], row["hit_count"]] for i, row in enumerate(objectives, 1)]))
    lines.append("")

    lines.append("## Interpretation Of Main Typologies")
    lines.append("")
    for i, row in enumerate(typology[:10], 1):
        code = row["code"]
        narrative = FINDING_NARRATIVES.get(code)
        if not narrative:
            continue
        lines.append(f"### {i}. {narrative['finding']}")
        lines.append("")
        lines.append(f"Signal strength: {row['note_count']} notes; {row['hit_count']} pattern hits.")
        lines.append("")
        lines.append(narrative["analysis"])
        lines.append("")
        lines.append(f"Likely result that can be drawn: {narrative['result_type']}")
        lines.append("")
        lines.append(f"AML or detection relevance: {narrative['controls']}")
        lines.append("")
        lines.append("Evidence boundary: supporting snippets are retained in the separate Phase 3 `evidence_snippets.csv` audit file and are not reproduced in the narrative report.")
        lines.append("")

    lines.append("## AML Indicator Candidates")
    lines.append("")
    lines.append(md_table(["Rank", "Indicator", "Sources", "Notes", "Interpretation"], [[row["rank"], row["label"], row["source_count"], row["note_count"], row["interpretation"]] for row in aml_rows]))
    lines.append("")

    lines.append("## Source Profiles")
    lines.append("")
    lines.append(md_table(["Source", "Dominant typology", "Notes", "Top typologies"], [[row["source"], row["dominant_typology"], row["dominant_typology_notes"], row["top_typologies"]] for row in source_profiles]))
    lines.append("")

    lines.append("## Journal-Ready Findings To Validate")
    lines.append("")
    lines.append("1. The dataset is strongest for account-access, bank-drop, cash-out, crypto-conversion, and trust/reputation typologies.")
    lines.append("2. Forum/market evidence appears to capture both commodity supply and downstream monetisation infrastructure.")
    lines.append("3. Telegram/private-channel migration should be treated as a structural feature of the transaction pathway.")
    lines.append("4. Explicit migrant/student exploitation is not yet a high-volume coded finding and needs targeted manual sampling before any prevalence claim.")
    lines.append("5. Marketplace scam and escrow discourse should be analysed as part of the criminal ecology, not just as noise.")
    lines.append("")

    lines.append("## Limitations")
    lines.append("")
    lines.append("- OCR is noisy and may include navigation, URLs, repeated page furniture, and interface text.")
    lines.append("- Regex coding can create false positives and false negatives.")
    lines.append("- Marketplace listings may be fraudulent, copied, repeated, exaggerated, or scams against other offenders.")
    lines.append("- Counts indicate signal concentration, not true market prevalence.")
    lines.append("- The dataset is evidence of observed online content, not proof that advertised goods or services were delivered.")
    lines.append("")

    lines.append("## Recommended Next Step")
    lines.append("")
    lines.append(
        "Before journal submission, draw a stratified validation sample from `evidence_snippets.csv` and the source notes. "
        "Prioritise the top typologies and the lower-count but substantively important categories such as mule recruitment "
        "and vulnerable-group exploitation."
    )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
