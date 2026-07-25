# Phase 3 Typology Codebook

Deterministic regex-based coding. No LLM or external API was used.

## bank_log_sale
- Label: Compromised bank log sale or discussion
- Criminal objective: Reference bank-log or associated account-access material
- Patterns:
  - `\bbank\s+logs?\b`
  - `\baccount\s+logs?\b`
  - `\blogz\b`
  - `\bbank\s+logins?\b`
  - `logs?\s+with\s+(?:email|cookie|cookies|access)`

## bank_drop_sale
- Label: Bank drop sale or bank-drop infrastructure
- Criminal objective: Reference bank-drop or receiving-account material
- Patterns:
  - `\bbank\s+drops?\b`
  - `\bbankdrop\b`
  - `\bdrop\s+account\b`
  - `\bdrop\s+shop\b`
  - `\bfresh\s+bank\s+drop\b`

## fullz_identity_package
- Label: Fullz or identity package
- Criminal objective: Reference identity packages or credentials relevant to KYC or account access
- Patterns:
  - `\bfullz\b`
  - `\bidentity package\b`
  - `\bstolen credentials?\b`
  - `\bsynthetic id\b`
  - `\bpersonal identifiable information\b`
  - `\bPII\b`
  - `\bcredit report\b`

## email_access_takeover
- Label: Email-access-enabled account takeover
- Criminal objective: Reference email, recovery, or session access alongside account access
- Patterns:
  - `\bemail access\b`
  - `\b(?:bank|account)\s+(?:email|mailbox)\b`
  - `\b(?:bank|account|login)\b.{0,120}\b(?:password reset|MFA|OTP|security questions?|session cookies?)\b`
  - `\b(?:password reset|MFA|OTP|security questions?|session cookies?)\b.{0,120}\b(?:bank|account|login)\b`

## mule_recruitment
- Label: Mule recruitment or account-holder solicitation
- Criminal objective: Reference mule or account-holder recruitment and solicitation
- Patterns:
  - `\bmoney mules?\b`
  - `\brecruit(?:ing|ment)?\b.{0,100}\b(?:mules?|account holders?)\b`
  - `\baccount holders?\b.{0,100}\b(?:receive|move|transfer|cash out)\b.{0,80}\b(?:funds?|money|payments?)\b`
  - `\bdirect owners?\b.{0,80}\b(?:bank|account)\b`
  - `\blooking for individuals\b.{0,100}\b(?:bank|account|receive|transfer)\b`
  - `\breal people with real bank accounts\b`
  - `\breceive wires?\b.{0,80}\b(?:fee|commission|percentage|cut)\b`

## cashout_laundering_service
- Label: Cash-out or laundering service
- Criminal objective: Reference cash-out, laundering, or conversion services
- Patterns:
  - `\bcash[\s-]?out(?:s|ing)?\b`
  - `\b(?:launder(?:ing)?|wash(?:ing)?)\b.{0,80}\b(?:money|funds?|crypto|service)\b`
  - `\b(?:dirty crypto|stolen funds?|fraud proceeds?)\b.{0,120}\b(?:clean cash|withdraw|bank transfer|wire|western union|moneygram)\b`
  - `\b(?:western union|moneygram|bank transfer|wire|ACH)\b.{0,100}\b(?:cash[\s-]?out|fee|commission|service)\b`

## crypto_payment_or_conversion
- Label: Cryptocurrency payment or conversion reference
- Criminal objective: Reference cryptocurrency payment, conversion, or obfuscation contexts
- Patterns:
  - `\b(?:bitcoin|BTC|monero|XMR|USDT|cryptocurrency|crypto)\b`
  - `\b(?:bitcoin|BTC|monero|XMR|USDT|cryptocurrency|crypto)\b.{0,100}\b(?:pay|payment|convert|exchange|cash|bank|wire|wallet|mixer|mixing)\b`
  - `\b(?:tornado cash|crypto mixer|coin mixer)\b`

## telegram_off_platform
- Label: Telegram or private-channel coordination reference
- Criminal objective: Reference Telegram or private channels in market-related content
- Patterns:
  - `\btelegram\b`
  - `\bTG\b`
  - `\bDMs?\b`
  - `\bprivate chat\b`
  - `\binvite-only\b`

## escrow_trust_reputation
- Label: Escrow, trust, reputation, or scam-risk discourse
- Criminal objective: Reference escrow, trust, reputation, or scam-risk discourse
- Patterns:
  - `\bescrow\b`
  - `\bmultisig\b`
  - `\bmulti-signature\b`
  - `\bfinali[sz]e early\b`
  - `\bexit scam\b`
  - `\btrusted vendor\b`
  - `\bvouch\b`
  - `\bred flag\b`
  - `\bscam(?:mer|med|s)?\b`

## tutorial_training_recruitment
- Label: Tutorial, guide, or training content
- Criminal objective: Reference tutorial, guide, method, or training content
- Patterns:
  - `\b(?:tutorial|guide|method|training|course)\b`
  - `\bhow[\s-]+to\b`
  - `\bbeginners?\b`

## jurisdiction_localisation
- Label: Jurisdiction-specific bank or account reference
- Criminal objective: Reference jurisdiction-specific banks, accounts, drops, or logs
- Patterns:
  - `\b(?:Australia|Australian|New Zealand|USA|United States|Canada)\b.{0,100}\b(?:bank|account|drop|log)\b`
  - `\b(?:bank|account|drop|log)\b.{0,100}\b(?:Australia|Australian|New Zealand|USA|United States|Canada)\b`
  - `\b(?:domestic bank|local financial systems?|region-specific accounts?)\b`

## vulnerable_group_exploitation
- Label: Vulnerable group or migrant/student exploitation
- Criminal objective: Reference possible exploitation of financially or migration-vulnerable people
- Patterns:
  - `\b(?:international students?|temporary migrants?|migrants?|vulnerable (?:people|persons?|groups?))\b.{0,120}\b(?:recruit|target|exploit|account|identity|data|cash[\s-]?out|mule)\b`
  - `\b(?:recruit|target|exploit|account|identity|data|cash[\s-]?out|mule)\b.{0,120}\b(?:international students?|temporary migrants?|migrants?|vulnerable (?:people|persons?|groups?))\b`

## market_access_limitation
- Label: Market access limitation, outage, login wall, or collection barrier
- Criminal objective: Describe data-access constraints affecting evidence collection
- Patterns:
  - `requires?\s+(?:an?\s+)?account`
  - `requires?\s+login`
  - `unable to connect`
  - `connection was refused`
  - `taken offline`
  - `not responding`
  - `search function`
  - `no longer active`

# AML Indicator Candidates

## bank_log_plus_email_access
- Label: Bank log packaged with email/cookie access
- Patterns:
  - `\bbank\s+logs?\b.{0,120}\bemail access\b`
  - `\bemail access\b.{0,120}\bbank\s+logs?\b`
  - `\bbank\s+logs?\b.{0,80}\b(?:session )?cookies?\b`

## domestic_account_preference
- Label: Jurisdiction-specific bank or account reference
- Patterns:
  - `\b(?:domestic bank|local financial systems?|region-specific accounts?)\b`
  - `\b(?:Australia|Australian|New Zealand|USA|United States|Canada)\b.{0,100}\b(?:bank|account|drop|log)\b`
  - `\b(?:bank|account|drop|log)\b.{0,100}\b(?:Australia|Australian|New Zealand|USA|United States|Canada)\b`

## telegram_sales_or_proof
- Label: Telegram used for vendor proof, negotiation, or sales
- Patterns:
  - `\btelegram\b.{0,120}\b(?:proof|vendor|group|media|contact|DMs?)\b`
  - `\b(?:vendor|proof|contact|DMs?)\b.{0,120}\btelegram\b`

## crypto_to_bank_cashout
- Label: Crypto-to-bank or crypto-to-cash conversion
- Patterns:
  - `\b(?:bitcoin|crypto)\b.{0,120}\b(?:bank|cash|wire|western union)\b`
  - `\bdirty crypto\b.{0,120}\bclean cash\b`

## escrow_or_exit_scam_risk
- Label: Escrow or exit-scam discourse
- Patterns:
  - `\bescrow\b`
  - `\bexit scam\b`
  - `\bfinali[sz]e early\b`
  - `\bmultisig\b`

## mule_or_account_holder_recruitment
- Label: Mule or account-holder recruitment
- Patterns:
  - `\bmoney mules?\b`
  - `\brecruit(?:ing|ment)?\b.{0,100}\b(?:mules?|account holders?)\b`
  - `\blooking for individuals\b.{0,100}\b(?:bank|account|receive|transfer)\b`
  - `\breal people with real bank accounts\b`
