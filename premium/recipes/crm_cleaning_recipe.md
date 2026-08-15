# CRM Dataset Cleaning Recipe

## Typical Issues
- Inconsistent phone number formats
- Mixed case email addresses
- Duplicate leads based on email or phone
- Missing first/last name
- Inconsistent date formats (created_at, last_contact)
- Invalid postal codes
- Extra whitespace in address fields

## Recommended Steps
1. **Inspect**: `inspect_file` to see columns and basic stats
2. **Profile**: `profile_dataset` to identify missing values and data types
3. **Normalize**:
   - Column names: snakecase
   - Whitespace: trim all string fields
   - Casing: lowercase email, proper case name fields
   - Dates: standardize to ISO 8601
   - Phone numbers: strip non‑digits, add country code if missing, format as E‑164
4. **Detect Duplicates**:
   - Exact duplicate rows
   - Duplicate emails
   - Duplicate phones
5. **Detect PII**:
   - Emails, phones, addresses
6. **Sanitize** (if sharing externally):
   - Hash email and phone for dedup keys while preserving ability to match
   - Mask address details beyond city level
7. **Validate**:
   - Required columns: first_name, last_name, email, phone, created_at
   - Email format validation
   - Phone format validation (E‑164)
   - Date ranges (created_at not in future)
8. **Clean**:
   - Trim whitespace
   - Standardize empty strings
   - Remove exact duplicate rows (keep first)
9. **Output**: Save cleaned dataset as `crm_leads_cleaned_<timestamp>.csv`
10. **Report**: Generate markdown report with quality score and actions taken

## Example Prompt for Claude
"Clean this CRM export using the DataShield MCP tools: normalize, deduplicate, validate, and create a sanitized copy for sharing with the marketing team."