# Premium AI Workflow Prompts for DataShield MCP

> 50+ ready‑to‑use prompts to get the most out of DataShield MCP with Claude.

## Data Quality Audits
1. "Audit this dataset and give me the top 5 data‑quality problems ranked by impact."
2. "What percentage of rows have missing values in each column?"
3. "Identify columns that likely contain duplicate data and suggest a deduplication key."
4. "Generate a data‑quality score and explain the factors that reduced it."
5. "Compare the schema of two files and list any mismatched columns or type changes."

## PII & Privacy
6. "Scan this file for personally identifiable information and show masked examples."
7. "Which columns are most likely to contain email addresses or phone numbers?"
8. "Create a sanitized copy of this dataset by hashing all detected PII."
9. "List all detected credit‑card numbers and show only the last four digits."
10. "Check for GDPR‑relevant fields (EU VAT, nationality, ID numbers) and flag them."

## Secret Detection
11. "Search for API keys, tokens, or private keys in this configuration dump."
12. "Mask any discovered AWS access keys while preserving the ability to validate format."
13. "Detect JWT tokens and warn if they appear unsigned or with weak alg."
14. "Create a tokenized version of API secrets for safe sharing with developers."
15. "Audit a log file for embedded passwords and replace them with placeholders."

## Cleaning & Normalization
16. "Normalize column names to snake_case, trim whitespace, and standardize empty values."
17. "Convert all date columns to ISO 8601 format (YYYY‑MM‑DD)."
18. "Standardize phone numbers to E‑164 format and flag invalid numbers."
19. "Lowercase all email addresses and remove display names."
20. "Title‑case proper‑case fields like first name, last name, and street address."

## Validation
21. "Validate that the `user_id` column is unique and contains only positive integers."
22. "Ensure that the `price` column is between 0 and 10000 with two decimal places."
23. "Check that the `status` column only contains values from the allowed list: active, inactive, pending."
24. "Verify that required columns are present and have less than 5% nulls."
25. "Validate date ranges: `start_date` must be before `end_date`."

## File Conversion
26. "Convert this Excel file to CSV for easier processing in Python scripts."
27. "Transform a JSONL log file into a CSV with columns for timestamp, level, and message."
28. "Create a Parquet version of this dataset for efficient analytics workloads."
29. "Export this CSV as a tab‑separated file for legacy system import."
30. "Convert a JSON configuration file to YAML for readability."

## Dataset Comparison
31. "Compare two customer exports and show which rows were added, removed, or changed."
32. "Find records that exist in the new file but not the old one based on email."
33. "Identify rows where the `salary` field changed by more than 10%."
34. "Check for schema drift between two versions of a data feed."
35. "Produce a side‑by‑side view of differing columns for manual review."

## Reporting
36. "Generate a one‑page markdown report suitable for a team stand‑up."
37. "Create an HTML report with charts visualizing missing values and duplicates."
38. "Output a JSON report that can be ingested by a monitoring dashboard."
39. "Include the DataShield Quality Score and a short executive summary."
40. "List recommended actions with estimated effort to improve data quality."

## Privacy‑First Sharing
41. "Create a sanitized copy of this dataset for sharing with an external consultant."
42. "Remove all PII and replace with synthetic but realistic values."
43. "Hash email addresses to preserve dedupability while preventing reversal."
44. "Tokenize phone numbers and keep a secure mapping locally."
45. "Generate a data‑usage‑notice to accompany the shared file."

## Automation & Workflows
46. "Outline a reusable workflow: inspect → profile → detect PII → sanitize → validate → report."
47. "Wrap the above steps into a script that can be run nightly via cron."
48. "Show how to chain MCP tool calls using Claude's agent workflow."
49. "Create a checklist for data‑processing before loading into a data warehouse."
50. "Provide a rollback plan: how to retain the original and verify the sanitized copy."

## Bonus: Industry‑Specific
51. "Clean a clinical trial dataset: de‑identify patient IDs, normalize visit dates, validate consent flags."
52. "Prepare a marketing campaign CSV: deduplicate leads, validate email domains, score lead quality."
53. "Audit a financial transaction file: detect duplicated transactions, validate IBANs, flag round‑amount suspicious entries."
54. "Normalize a survey export: Likert scales to numbers, clean open‑ended responses, compute completion rate."
55. "Clean an e‑commerce order dump: standardize addresses, validate phone numbers, compute order totals."

*Each prompt assumes the user has already pointed the MCP at a file via `inspect_file` or similar.*