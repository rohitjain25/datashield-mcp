# Premium Validation Workflows (20 examples)

1. **Required Fields Check** – Ensure mandatory columns exist and have <2% nulls.
2. **Uniqueness Constraint** – Verify primary key columns have no duplicates.
3. **Format Validation** – Validate email, phone, URL, ZIP code, SSN patterns.
4. **Range Validation** – Ensure numeric columns fall within expected min/max.
5. **Date Logic** – Confirm start_date ≤ end_date; dates not in future.
6. **Allowed Values** – Check categorical columns against permitted list.
7. **Referential Integrity** – Verify foreign key values exist in reference dataset.
8. **Data Type Consistency** – Ensure columns are of the correct type (int, float, date).
9. **Cross‑Field Validation** – Ensure password_confirm matches password, etc.
10. **Conditional Requirements** – If country=US then state must be present and 2 letters.
11. **Statistical Outliers** – Flag values beyond 3 standard deviations from mean.
12. **Duplicate Detection Across Datasets** – Ensure no overlap between train/test splits.
13. **Checksum Validation** – Validate that a hash column matches computed hash of other fields.
14. **Schema Versioning** – Confirm dataset matches expected version schema.
15. **Mandatory Keywords** – Ensure certain text columns contain required terms.
16. **File‑Level Validation** – Verify file size, row count, and encoding.
17. **Time Series Continuity** – Ensure timestamps are monotonic and gaps are within tolerance.
18. **Multicolumn Uniqueness** – Validate that combination of columns is unique.
19. **Regex Conformance** – Ensure values match a business‑specific regex pattern.
20. **Data Freshness** – Validate that timestamps are within an acceptable window (e.g., last 30 days).