# Premium Privacy Workflows (20 examples)

1. **PII Masking** – Detect emails, phones, SSNs; mask with asterisks; create sanitized copy.
2. **Tokenization** – Replace sensitive values with reversible tokens; store mapping locally.
3. **Hashing for Dedup** – Hash email and phone to generate dedup keys without exposing PII.
4. **Redaction** – Remove PII columns entirely from shared dataset.
5. **Synthetic Generation** – Generate realistic fake data that preserves statistical distribution.
6. **GDPR Right‑to‑Be‑Forgotten** – Locate all records matching an identifier and overwrite with placeholders.
7. **CCPA Opt‑Out Flag** – Add a column indicating whether a record has opted out of sale.
8. **Health Data De‑identification** – Remove HIPAA 18 identifiers; shift dates; adjust ages.
9. **Financial Data Obfuscation** – Mask account numbers; keep last four digits; hash routing numbers.
10. **Location Privacy** – Convert precise GPS coordinates to zip‑code level or add noise.
11. **Identifier Separation** – Split full name into first/last and hash each component separately.
12. **Email Domain Suppression** – Keep only the domain part of email addresses for analytics.
13. **Phone Number Buckets** – Replace full phone numbers with area‑code only for coarse analysis.
14. **ID Tokenization** – Replace customer IDs with UUIDs; maintain lookup table internally.
15. **Audit Log Sanitization** – Remove IP addresses, user agents, and session IDs from logs.
16. **Configuration File Secrets** – Replace API keys, passwords, and tokens with placeholders.
17. **Database Dump Scrubbing** – Mask personally identifiable columns in SQL dumps.
18. **Web Analytics Export** – Hash visitor IDs; remove geolocation precision beyond city.
19. **Marketing List Sharing** – Remove direct mail addresses; keep only hashed email for dedup.
20. **Research Dataset Sharing** – Strip direct identifiers; retain only aggregated or pseudonymized fields.