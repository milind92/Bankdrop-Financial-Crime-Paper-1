# Financial Crime Analysis Report

**Historical exploratory output — journal-use hold.** This analysis used the 980-note structural screen, which includes researcher and collection-status material. The source-evidence denominator, image and Markdown provenance, OCR quality, and revised target validation have not been approved. Counts and narratives below are archived hypotheses from this mixed-record analysis, not article findings or evidence of services, transactions, or market prevalence.

## Executive Summary

The rule-based analysis identifies a range of content signals around bank logs, bank drops, identity packages, cash-out services, crypto conversion, Telegram/private-channel references, and criminal-market trust terms. These lexical patterns motivate hypotheses about account access and conversion, but they do not establish genuine services or movement of value.

This report is based on deterministic Phase 3 coding over Markdown notes plus OCR text. A separate July human validation exercise covered the historical mixed-record sample; it does not validate a revised source-evidence corpus. The text below is a computational audit record, not a final qualitative conclusion.

## Data And Method Boundary

Phase 3 coded 980 notes using 12 substantive typologies and 1 collection-quality flag, alongside 6 AML indicator candidates. Evidence snippets available for audit: 2707.

The pipeline is deterministic: Phase 1 indexed Markdown, Phase 2 OCR'd screenshots, Phase 3 applied a deterministic codebook, and Phase 4 synthesises those outputs. No external LLM or external API was used in Phase 4.

## Historical Typology Rule Counts

| Rank | Typology | Notes | Hits |
| --- | --- | --- | --- |
| 1 | Compromised bank log sale or discussion | 178 | 1090 |
| 2 | Cryptocurrency payment or conversion reference | 126 | 594 |
| 3 | Fullz or identity package | 124 | 485 |
| 4 | Escrow, trust, reputation, or scam-risk discourse | 121 | 640 |
| 5 | Cash-out or laundering service | 118 | 418 |
| 6 | Jurisdiction-specific bank or account reference | 117 | 693 |
| 7 | Bank drop sale or bank-drop infrastructure | 116 | 719 |
| 8 | Tutorial, guide, or training content | 104 | 484 |
| 9 | Telegram or private-channel coordination reference | 82 | 243 |
| 10 | Email-access-enabled account takeover | 62 | 218 |
| 11 | Mule recruitment or account-holder solicitation | 9 | 14 |
| 12 | Vulnerable group or migrant/student exploitation | 0 | 0 |

## Criminal Objectives

| Rank | Criminal objective | Notes | Hits |
| --- | --- | --- | --- |
| 1 | Reference bank-log or associated account-access material | 178 | 1090 |
| 2 | Reference cryptocurrency payment, conversion, or obfuscation contexts | 126 | 594 |
| 3 | Reference identity packages or credentials relevant to KYC or account access | 124 | 485 |
| 4 | Reference escrow, trust, reputation, or scam-risk discourse | 121 | 640 |
| 5 | Reference cash-out, laundering, or conversion services | 118 | 418 |
| 6 | Reference jurisdiction-specific banks, accounts, drops, or logs | 117 | 693 |
| 7 | Reference bank-drop or receiving-account material | 116 | 719 |
| 8 | Reference tutorial, guide, method, or training content | 104 | 484 |
| 9 | Reference Telegram or private channels in market-related content | 82 | 243 |
| 10 | Reference email, recovery, or session access alongside account access | 62 | 218 |
| 11 | Reference mule or account-holder recruitment and solicitation | 9 | 14 |
| 12 | Reference possible exploitation of financially or migration-vulnerable people | 0 | 0 |

## Interpretation Hold

The historical rule counts below are retained for audit. Typology narratives and detection advice are withheld from this report until the authors review attributable source passages, OCR quality and target-specific validation on the revised frame.

## AML Indicator Candidates

| Rank | Indicator | Sources | Notes | Interpretation |
| --- | --- | --- | --- | --- |
| 1 | Jurisdiction-specific bank or account reference | 11 | 117 | Rule match for jurisdiction terms near bank, account, drop, or log terms; it does not establish preference or evasion intent. |
| 2 | Escrow or exit-scam discourse | 11 | 101 | Rule match for escrow, exit-scam, finalise-early, or multisig terms; it does not establish listing reliability or transaction behaviour. |
| 3 | Crypto-to-bank or crypto-to-cash conversion | 10 | 34 | Rule match for cryptocurrency near bank, cash, wire, or conversion terms; it does not establish conversion or money movement. |
| 4 | Telegram used for vendor proof, negotiation, or sales | 4 | 21 | Rule match for Telegram near vendor, proof, contact, or direct-message terms; it does not establish negotiation or a transaction. |
| 5 | Bank log packaged with email/cookie access | 6 | 15 | Rule match for bank-log terms near email or cookie-access terms; expert review must determine account-takeover relevance. |
| 6 | Mule or account-holder recruitment | 3 | 8 | Rule match for explicit mule, recruitment, or account-holder language; human review must confirm recruitment context. |

## Source Profiles

| Source | Dominant typology | Notes | Top typologies |
| --- | --- | --- | --- |
| 1. Dread | escrow_trust_reputation | 22 | escrow_trust_reputation (22 notes); bank_drop_sale (19 notes); jurisdiction_localisation (17 notes); tutorial_training_recruitment (17 notes); bank_log_sale (15 notes) |
| 10. Tor Shop | bank_drop_sale | 32 | bank_drop_sale (32 notes); bank_log_sale (29 notes); fullz_identity_package (24 notes); crypto_payment_or_conversion (14 notes); jurisdiction_localisation (13 notes) |
| 11. Legit Market | escrow_trust_reputation | 20 | escrow_trust_reputation (20 notes); bank_log_sale (15 notes); jurisdiction_localisation (12 notes); bank_drop_sale (11 notes); crypto_payment_or_conversion (6 notes) |
| 12. TORCH Tor Search | bank_drop_sale | 2 | bank_drop_sale (2 notes); bank_log_sale (2 notes) |
| 13. Bank Logs | none | 0 | no rule-positive typology matches |
| 14. Lonely Road | crypto_payment_or_conversion | 3 | crypto_payment_or_conversion (3 notes); bank_log_sale (1 notes); jurisdiction_localisation (1 notes) |
| 15. Tenebris | crypto_payment_or_conversion | 4 | crypto_payment_or_conversion (4 notes); telegram_off_platform (4 notes); bank_log_sale (3 notes); cashout_laundering_service (3 notes); escrow_trust_reputation (3 notes) |
| 17. XmrBazaar | crypto_payment_or_conversion | 2 | crypto_payment_or_conversion (2 notes); bank_drop_sale (1 notes); escrow_trust_reputation (1 notes); tutorial_training_recruitment (1 notes) |
| 2. Altenen | fullz_identity_package | 19 | fullz_identity_package (19 notes); tutorial_training_recruitment (19 notes); telegram_off_platform (18 notes); bank_log_sale (15 notes); crypto_payment_or_conversion (13 notes) |
| 3. Pitch | telegram_off_platform | 20 | telegram_off_platform (20 notes); tutorial_training_recruitment (20 notes); escrow_trust_reputation (18 notes); crypto_payment_or_conversion (16 notes); bank_log_sale (15 notes) |
| 4. Caders Heven | bank_log_sale | 28 | bank_log_sale (28 notes); crypto_payment_or_conversion (24 notes); cashout_laundering_service (22 notes); fullz_identity_package (12 notes); bank_drop_sale (6 notes) |
| 5. CardPro | cashout_laundering_service | 32 | cashout_laundering_service (32 notes); telegram_off_platform (22 notes); jurisdiction_localisation (11 notes); crypto_payment_or_conversion (7 notes); bank_drop_sale (6 notes) |
| 6. The X Wave Market | escrow_trust_reputation | 41 | escrow_trust_reputation (41 notes); fullz_identity_package (20 notes); cashout_laundering_service (10 notes); crypto_payment_or_conversion (10 notes); tutorial_training_recruitment (10 notes) |
| 7. Meta Banklogs | jurisdiction_localisation | 36 | jurisdiction_localisation (36 notes); bank_log_sale (29 notes); email_access_takeover (21 notes); bank_drop_sale (14 notes); fullz_identity_package (12 notes) |
| 8. Secure ccSeller | fullz_identity_package | 6 | fullz_identity_package (6 notes); jurisdiction_localisation (5 notes); bank_log_sale (4 notes); email_access_takeover (4 notes); tutorial_training_recruitment (4 notes) |
| 9. Deep Shop | bank_log_sale | 15 | bank_log_sale (15 notes); crypto_payment_or_conversion (10 notes); escrow_trust_reputation (7 notes); cashout_laundering_service (4 notes); tutorial_training_recruitment (4 notes) |

## Evidence Boundaries

The present tables count lexical signals in a mixed-record archive. They do not establish services, transactions, unique posts, source coverage, or market prevalence. The zero match for a target is not evidence of absence.

## Limitations

- OCR is noisy and may include navigation, URLs, repeated page furniture, and interface text.
- Regex coding can create false positives and false negatives.
- Marketplace listings may be fraudulent, copied, repeated, exaggerated, or scams against other offenders.
- Counts indicate signal concentration, not true market prevalence.
- The dataset is evidence of observed online content, not proof that advertised goods or services were delivered.

## Recommended Next Step

Before journal submission, reconcile every proposed claim with a new source-evidence human-validation performance table, target-level uncertainty, duplicate and source-sensitivity outputs, and controlled contextual review. Obtain the separate AML-domain review and do not make an absence or rarity claim for vulnerable-group exploitation from the zero deterministic match.
