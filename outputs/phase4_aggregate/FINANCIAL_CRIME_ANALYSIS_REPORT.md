# Financial Crime Analysis Report

## Executive Summary

The rule-based analysis identifies a range of content signals around bank logs, bank drops, identity packages, cash-out services, crypto conversion, Telegram/private-channel references, and criminal-market trust terms. These lexical patterns motivate hypotheses about account access and conversion, but they do not establish genuine services or movement of value.

This report is based on deterministic Phase 3 coding over Markdown notes plus OCR text. It should be read as a structured first interpretation rather than a final qualitative conclusion. The strongest publication path is to use these findings to guide manual validation and targeted close reading.

## Data And Method Boundary

Phase 3 coded 999 notes using 13 typology codes and 6 AML indicator candidates. Evidence snippets available for audit: 2817.

The method is deliberately conservative: Phase 1 indexed Markdown, Phase 2 OCR'd screenshots, Phase 3 applied a deterministic codebook, and Phase 4 synthesises those outputs. No external LLM or external API was used in Phase 4.

## Ranked Typology Findings

| Rank | Typology | Notes | Hits |
| --- | --- | --- | --- |
| 1 | Compromised bank log sale or discussion | 182 | 1108 |
| 2 | Escrow, trust, reputation, or scam-risk discourse | 134 | 764 |
| 3 | Fullz or identity package | 128 | 499 |
| 4 | Cryptocurrency payment or conversion reference | 127 | 603 |
| 5 | Bank drop sale or bank-drop infrastructure | 121 | 748 |
| 6 | Cash-out or laundering service | 120 | 422 |
| 7 | Jurisdiction-specific bank or account reference | 120 | 701 |
| 8 | Tutorial, guide, or training content | 107 | 493 |
| 9 | Telegram or private-channel coordination reference | 87 | 252 |
| 10 | Email-access-enabled account takeover | 64 | 223 |
| 11 | Mule recruitment or account-holder solicitation | 10 | 16 |
| 12 | Vulnerable group or migrant/student exploitation | 1 | 6 |

## Criminal Objectives

| Rank | Criminal objective | Notes | Hits |
| --- | --- | --- | --- |
| 1 | Reference bank-log or associated account-access material | 182 | 1108 |
| 2 | Reference escrow, trust, reputation, or scam-risk discourse | 134 | 764 |
| 3 | Reference identity packages or credentials relevant to KYC or account access | 128 | 499 |
| 4 | Reference cryptocurrency payment, conversion, or obfuscation contexts | 127 | 603 |
| 5 | Reference bank-drop or receiving-account material | 121 | 748 |
| 6 | Reference cash-out, laundering, or conversion services | 120 | 422 |
| 7 | Reference jurisdiction-specific banks, accounts, drops, or logs | 120 | 701 |
| 8 | Reference tutorial, guide, method, or training content | 107 | 493 |
| 9 | Reference Telegram or private channels in market-related content | 87 | 252 |
| 10 | Reference email, recovery, or session access alongside account access | 64 | 223 |
| 11 | Reference mule or account-holder recruitment and solicitation | 10 | 16 |
| 12 | Reference possible exploitation of financially or migration-vulnerable people | 1 | 6 |

## Interpretation Of Main Typologies

### 1. Bank-log sale or discussion terms are the most frequent provisional typology.

Signal strength: 182 notes; 1108 pattern hits.

Bank-log material indicates demand for access to existing accounts rather than only newly opened accounts. The operational risk is account takeover followed by rapid monetisation, especially where logs are bundled with recovery-channel access.

Likely result that can be drawn: Can support a typology of account-takeover commodity markets.

AML or detection relevance: Prioritise unusual device/session, geolocation, cookie/session reuse, and recovery-channel changes.

Evidence boundary: supporting snippets are retained in the separate Phase 3 `evidence_snippets.csv` audit file and are not reproduced in the narrative report.

### 2. Escrow, trust, reputation, and scam-risk discourse are prominent.

Signal strength: 134 notes; 764 pattern hits.

A large trust-risk signal means the dataset also captures criminal-market governance problems. This is analytically important because some listings may be scams against other offenders, copied listings, or reputation-building content.

Likely result that can be drawn: Can support assessment of marketplace reliability and deception within illicit markets.

AML or detection relevance: Avoid treating all listings as real inventory; code credibility, repetition, escrow claims, and scam warnings separately.

Evidence boundary: supporting snippets are retained in the separate Phase 3 `evidence_snippets.csv` audit file and are not reproduced in the narrative report.

### 3. Fullz and identity-package terms appear frequently in the provisional coding.

Signal strength: 128 notes; 499 pattern hits.

Fullz/identity signals connect bank drops and account takeover to KYC bypass, impersonation, account opening, and recovery-channel control. This is a key bridge between data theft and financial crime.

Likely result that can be drawn: Can support analysis of identity-enabled financial-crime workflows.

AML or detection relevance: Monitor identity-document reuse, abnormal KYC metadata, email/phone changes, and synthetic identity patterns.

Evidence boundary: supporting snippets are retained in the separate Phase 3 `evidence_snippets.csv` audit file and are not reproduced in the narrative report.

### 4. Cryptocurrency payment and conversion terms appear in the provisional coding.

Signal strength: 127 notes; 603 pattern hits.

Crypto references occur alongside cash-out, escrow, and market-payment language. This suggests crypto is not just a payment method or was actually converted, obfuscated, or settled; those are hypotheses for human review.

Likely result that can be drawn: Can support analysis of crypto-to-fiat conversion points and settlement rails.

AML or detection relevance: Focus on fiat off-ramp points, exchange account misuse, rapid movement after crypto conversion, and mule account inflows.

Evidence boundary: supporting snippets are retained in the separate Phase 3 `evidence_snippets.csv` audit file and are not reproduced in the narrative report.

### 5. Bank-drop terms appear frequently in the provisional coding.

Signal strength: 121 notes; 748 pattern hits.

Bank-drop signals indicate demand for accounts that can receive, hold, or move funds. This aligns with mule/drop account misuse and may include both compromised accounts and accounts opened or controlled for criminal use.

Likely result that can be drawn: Can support a bank-drop/mule-account typology.

AML or detection relevance: Look for newly active dormant accounts, inbound third-party funds, rapid onward transfer, and mismatch between customer profile and transaction behaviour.

Evidence boundary: supporting snippets are retained in the separate Phase 3 `evidence_snippets.csv` audit file and are not reproduced in the narrative report.

### 6. Cash-out and laundering-service terms appear in the provisional rule-based coding.

Signal strength: 120 notes; 422 pattern hits.

The rule-based coding identifies terms concerning cash-out, laundering, and conversion services. These lexical matches are consistent with a downstream-monetisation hypothesis, but they do not show that a service was genuine, supplied, or used. The completed ICR supports coder consistency, but direct contextual evidence and close reading remain required before making a substantive movement-of-value claim.

Likely result that can be drawn: Can support a typology of conversion services and post-compromise monetisation.

AML or detection relevance: Monitor abrupt inbound/outbound movement, beneficiary changes, mule-like receiving behaviour, and crypto-to-bank conversion narratives.

Evidence boundary: supporting snippets are retained in the separate Phase 3 `evidence_snippets.csv` audit file and are not reproduced in the narrative report.

### 7. Jurisdiction and domestic-account terms appear across sources.

Signal strength: 120 notes; 701 pattern hits.

The rule-based coding records country and local-bank terms near bank, account, drop, or log terms. It does not establish actor preference, reduced scrutiny, or completed domestic or cross-border money movement.

Likely result that can be drawn: Can support analysis of localised mule/drop demand and geography-specific bank targeting.

AML or detection relevance: Assess domestic receiving-account patterns, especially where victim geography and receiving-account geography align.

Evidence boundary: supporting snippets are retained in the separate Phase 3 `evidence_snippets.csv` audit file and are not reproduced in the narrative report.

### 8. Tutorial/method/training material is substantial.

Signal strength: 107 notes; 493 pattern hits.

The dataset includes content that appears to lower barriers to entry or package criminal knowledge. This supports analysis of capability diffusion, recruitment, and monetisation of know-how, not just commodity sales.

Likely result that can be drawn: Can support a typology of criminal learning and recruitment infrastructure.

AML or detection relevance: Consider education-style material as a risk amplifier that can expand participation and standardise methods.

Evidence boundary: supporting snippets are retained in the separate Phase 3 `evidence_snippets.csv` audit file and are not reproduced in the narrative report.

### 9. Telegram and private-channel references appear in market-related records.

Signal strength: 87 notes; 252 pattern hits.

The rule identifies Telegram or private-channel terms in market-related text. It does not by itself show that negotiation, proof, or transaction coordination moved elsewhere. Human review is required before interpreting off-platform migration; captured forum material may omit context outside the retained record.

Likely result that can be drawn: Can support a validation target concerning private-channel references and possible coordination.

AML or detection relevance: Treat open-forum posts as lead generation; do not assume the whole transaction is visible in the captured page.

Evidence boundary: supporting snippets are retained in the separate Phase 3 `evidence_snippets.csv` audit file and are not reproduced in the narrative report.

### 10. Email access is a recurring enhancer of bank-log/account-takeover risk.

Signal strength: 64 notes; 223 pattern hits.

Email access can strengthen persistence and allow control over password resets, notifications, and recovery paths. Where bank access and email access appear together, the account-takeover risk is materially higher.

Likely result that can be drawn: Can support an enhanced-risk sub-typology of bank log plus recovery-channel compromise.

AML or detection relevance: Treat email-change, inbox-rule, recovery-channel, and MFA-reset events as linked financial-crime risk indicators.

Evidence boundary: supporting snippets are retained in the separate Phase 3 `evidence_snippets.csv` audit file and are not reproduced in the narrative report.

## AML Indicator Candidates

| Rank | Indicator | Sources | Notes | Interpretation |
| --- | --- | --- | --- | --- |
| 1 | Jurisdiction-specific bank or account reference | 12 | 120 | Rule match for jurisdiction terms near bank, account, drop, or log terms; it does not establish preference or evasion intent. |
| 2 | Escrow or exit-scam discourse | 12 | 103 | Rule match for escrow, exit-scam, finalise-early, or multisig terms; it does not establish listing reliability or transaction behaviour. |
| 3 | Crypto-to-bank or crypto-to-cash conversion | 10 | 34 | Rule match for cryptocurrency near bank, cash, wire, or conversion terms; it does not establish conversion or money movement. |
| 4 | Telegram used for vendor proof, negotiation, or sales | 5 | 22 | Rule match for Telegram near vendor, proof, contact, or direct-message terms; it does not establish negotiation or a transaction. |
| 5 | Bank log packaged with email/cookie access | 7 | 16 | Rule match for bank-log terms near email or cookie-access terms; expert review must determine account-takeover relevance. |
| 6 | Mule or account-holder recruitment | 4 | 9 | Rule match for explicit mule, recruitment, or account-holder language; human review must confirm recruitment context. |

## Source Profiles

| Source | Dominant typology | Notes | Top typologies |
| --- | --- | --- | --- |
| (no_source) | bank_drop_sale | 5 | bank_drop_sale (5 notes); telegram_off_platform (5 notes); bank_log_sale (4 notes); fullz_identity_package (4 notes); jurisdiction_localisation (3 notes) |
| 1. Dread | escrow_trust_reputation | 22 | escrow_trust_reputation (22 notes); bank_drop_sale (19 notes); jurisdiction_localisation (17 notes); tutorial_training_recruitment (17 notes); bank_log_sale (15 notes) |
| 10. Tor Shop | bank_drop_sale | 32 | bank_drop_sale (32 notes); bank_log_sale (29 notes); fullz_identity_package (24 notes); crypto_payment_or_conversion (14 notes); jurisdiction_localisation (13 notes) |
| 11. Legit Market | escrow_trust_reputation | 20 | escrow_trust_reputation (20 notes); bank_log_sale (15 notes); jurisdiction_localisation (12 notes); bank_drop_sale (11 notes); crypto_payment_or_conversion (6 notes) |
| 12. TORCH Tor Search | bank_drop_sale | 2 | bank_drop_sale (2 notes); bank_log_sale (2 notes) |
| 14. Lonely Road | crypto_payment_or_conversion | 3 | crypto_payment_or_conversion (3 notes); bank_log_sale (1 notes); jurisdiction_localisation (1 notes) |
| 15. Tenebris | crypto_payment_or_conversion | 4 | crypto_payment_or_conversion (4 notes); telegram_off_platform (4 notes); bank_log_sale (3 notes); cashout_laundering_service (3 notes); escrow_trust_reputation (3 notes) |
| 17.  XmrBazaar | crypto_payment_or_conversion | 2 | crypto_payment_or_conversion (2 notes); bank_drop_sale (1 notes); escrow_trust_reputation (1 notes); tutorial_training_recruitment (1 notes) |
| 2. Altenen | fullz_identity_package | 19 | fullz_identity_package (19 notes); tutorial_training_recruitment (19 notes); telegram_off_platform (18 notes); bank_log_sale (15 notes); crypto_payment_or_conversion (13 notes) |
| 3. Pitch | escrow_trust_reputation | 20 | escrow_trust_reputation (20 notes); telegram_off_platform (20 notes); tutorial_training_recruitment (20 notes); crypto_payment_or_conversion (16 notes); bank_log_sale (15 notes) |
| 4. Caders Heven | bank_log_sale | 28 | bank_log_sale (28 notes); crypto_payment_or_conversion (24 notes); cashout_laundering_service (22 notes); fullz_identity_package (12 notes); bank_drop_sale (6 notes) |
| 5. CardPro | cashout_laundering_service | 32 | cashout_laundering_service (32 notes); telegram_off_platform (22 notes); jurisdiction_localisation (11 notes); crypto_payment_or_conversion (7 notes); bank_drop_sale (6 notes) |
| 6. The X Wave Market | escrow_trust_reputation | 41 | escrow_trust_reputation (41 notes); fullz_identity_package (20 notes); cashout_laundering_service (10 notes); crypto_payment_or_conversion (10 notes); tutorial_training_recruitment (10 notes) |
| 7. Meta Banklogs | jurisdiction_localisation | 36 | jurisdiction_localisation (36 notes); bank_log_sale (29 notes); email_access_takeover (21 notes); bank_drop_sale (14 notes); fullz_identity_package (12 notes) |
| 8. Secure ccSeller | fullz_identity_package | 6 | fullz_identity_package (6 notes); jurisdiction_localisation (5 notes); bank_log_sale (4 notes); email_access_takeover (4 notes); tutorial_training_recruitment (4 notes) |
| 9. Deep Shop | bank_log_sale | 15 | bank_log_sale (15 notes); escrow_trust_reputation (15 notes); crypto_payment_or_conversion (10 notes); cashout_laundering_service (4 notes); tutorial_training_recruitment (4 notes) |

## Journal-Ready Findings To Validate

1. The dataset is strongest for account-access, bank-drop, cash-out, crypto-conversion, and trust/reputation typologies.
2. Forum/market evidence appears to capture both commodity supply and downstream monetisation infrastructure.
3. Telegram/private-channel migration should be treated as a structural feature of the transaction pathway.
4. Explicit migrant/student exploitation is not yet a high-volume coded finding and needs targeted manual sampling before any prevalence claim.
5. Marketplace scam and escrow discourse should be analysed as part of the criminal ecology, not just as noise.

## Limitations

- OCR is noisy and may include navigation, URLs, repeated page furniture, and interface text.
- Regex coding can create false positives and false negatives.
- Marketplace listings may be fraudulent, copied, repeated, exaggerated, or scams against other offenders.
- Counts indicate signal concentration, not true market prevalence.
- The dataset is evidence of observed online content, not proof that advertised goods or services were delivered.

## Recommended Next Step

Before journal submission, draw a stratified validation sample from `evidence_snippets.csv` and the source notes. Prioritise the top typologies and the lower-count but substantively important categories such as mule recruitment and vulnerable-group exploitation.
