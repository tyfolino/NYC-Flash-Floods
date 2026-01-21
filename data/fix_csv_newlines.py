#!/usr/bin/env python3
"""
Fix embedded newlines in storm_data_search_results.csv

The early entries (1996 - mid 2006) have a malformed CSV format where:
1. EVENT_NARRATIVE and EPISODE_NARRATIVE fields end with `"","`
2. The actual narrative text follows on subsequent lines WITHOUT proper quoting
3. The record ends with `",<row_number>` on the final line

Later entries (2006+) use '|' as a separator and keep everything on one line.

This script:
1. Parses the malformed CSV by detecting record boundaries using the known
   structure: records end with `,<ABSOLUTE_ROWNUMBER>` pattern
2. Reconstructs proper records with narratives on single lines
3. Writes out a clean single-line-per-record CSV
"""

import re
from pathlib import Path


def parse_malformed_csv(input_path: Path) -> tuple[list[str], list[dict]]:
    """
    Parse the malformed CSV file.

    Returns (fieldnames, list of row dicts).
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Normalize line endings
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    lines = content.split('\n')

    # First line is the header
    header_line = lines[0]
    fieldnames = header_line.split(',')

    # Detect record boundaries:
    # Each record ENDS with `,<ABSOLUTE_ROWNUMBER>` where the number is 1, 2, 3, etc.
    # The ABSOLUTE_ROWNUMBER increments sequentially through the file

    # First pass: find all lines that end with a potential row number
    # Pattern: line ending with `",<digits>` or just `,<digits>`
    record_end_pattern = re.compile(r'[,"](\d+)$')

    # Collect raw records by finding their endings
    raw_records = []
    current_record_lines = []

    expected_row_num = 1  # ABSOLUTE_ROWNUMBER starts at 1

    for line in lines[1:]:  # Skip header
        current_record_lines.append(line)

        # Check if this line ends the current record
        match = record_end_pattern.search(line)
        if match:
            row_num = int(match.group(1))
            if row_num == expected_row_num:
                # This is the end of a record
                raw_records.append('\n'.join(current_record_lines))
                current_record_lines = []
                expected_row_num += 1

    # Handle any remaining lines (shouldn't happen in well-formed data)
    if current_record_lines:
        raw_records.append('\n'.join(current_record_lines))

    # Now parse each record into a dict
    parsed_rows = []
    for raw_record in raw_records:
        parsed = parse_single_record(raw_record, fieldnames)
        if parsed:
            parsed_rows.append(parsed)

    return fieldnames, parsed_rows


def parse_single_record(raw_record: str, fieldnames: list[str]) -> dict | None:
    """
    Parse a single (potentially multi-line) record into a dict.

    The record format is:
    EVENT_ID,CZ_NAME_STR,...,EVENT_NARRATIVE,EPISODE_NARRATIVE,ABSOLUTE_ROWNUMBER

    For old records, it looks like:
    5583680,QUEENS CO.,...,"","
    Narrative text here
    More narrative
    ",1

    For new records, it's all on one line:
    136489,QUEENS CO.,...,"event text","episode text",179
    """
    lines = raw_record.split('\n')

    # Single-line record (newer format)
    if len(lines) == 1:
        return parse_single_line_record(raw_record, fieldnames)

    # Multi-line record (older format with malformed quoting)
    first_line = lines[0]

    # Extract ABSOLUTE_ROWNUMBER from the last line
    last_line = lines[-1]
    match = re.search(r'[,"](\d+)$', last_line)
    if not match:
        return None
    row_number = match.group(1)

    # Find where the narrative section starts in the first line
    # Pattern: `,"","` marks empty EVENT_NARRATIVE followed by start of EPISODE_NARRATIVE
    # Or `,"",` for when EPISODE_NARRATIVE continues on next line

    # The structured data ends just before the narrative fields
    # Look for the pattern that marks the narrative section
    narrative_marker = first_line.rfind(',"","')
    if narrative_marker == -1:
        narrative_marker = first_line.rfind(',""," ')
    if narrative_marker == -1:
        narrative_marker = first_line.rfind(',"",')

    if narrative_marker == -1:
        # Fallback: try standard CSV parsing with newlines converted
        return parse_single_line_record(raw_record.replace('\n', ' | '), fieldnames)

    # Parse the structured part (everything before narratives)
    structured_part = first_line[:narrative_marker]
    structured_fields = parse_csv_fields(structured_part)

    # Extract the narrative text
    # Start after the `,"","` or similar pattern
    narrative_start = first_line[narrative_marker + 1:]  # Skip the leading comma

    # Combine all lines for the narrative
    full_narrative = narrative_start
    for line in lines[1:]:
        full_narrative += '\n' + line

    # Remove the leading `"","` pattern
    full_narrative = re.sub(r'^"","?\s*', '', full_narrative)

    # Remove trailing `",<row_number>` or `",<row_number>`
    full_narrative = re.sub(r'"\s*,\s*\d+$', '', full_narrative)
    full_narrative = re.sub(r',\s*\d+$', '', full_narrative)

    # Clean up the narrative
    episode_narrative = clean_narrative(full_narrative)

    # Build the row dict
    row = {}
    for i, field in enumerate(fieldnames[:-3]):  # All fields except last 3
        if i < len(structured_fields):
            row[field] = structured_fields[i]
        else:
            row[field] = ''

    row['EVENT_NARRATIVE'] = ''  # Usually empty in old records
    row['EPISODE_NARRATIVE'] = episode_narrative
    row['ABSOLUTE_ROWNUMBER'] = row_number

    return row


def parse_single_line_record(line: str, fieldnames: list[str]) -> dict | None:
    """Parse a single-line CSV record using standard CSV parsing."""
    import csv
    import io

    try:
        reader = csv.reader(io.StringIO(line))
        values = next(reader)

        if len(values) != len(fieldnames):
            return None

        row = dict(zip(fieldnames, values))

        # Clean up narratives (replace any embedded newlines with pipes)
        for field in ['EVENT_NARRATIVE', 'EPISODE_NARRATIVE']:
            if field in row and row[field]:
                row[field] = clean_narrative(row[field])

        return row
    except Exception:
        return None


def parse_csv_fields(line: str) -> list[str]:
    """Parse CSV fields from a line, respecting quotes."""
    import csv
    import io

    try:
        reader = csv.reader(io.StringIO(line))
        return next(reader)
    except Exception:
        return line.split(',')


def clean_narrative(text: str) -> str:
    """Clean up narrative text by replacing newlines with pipes."""
    if not text:
        return ''

    # Normalize whitespace
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Replace multiple newlines with single
    while '\n\n' in text:
        text = text.replace('\n\n', '\n')

    # Replace newlines with pipe separator
    text = text.replace('\n', ' | ')

    # Clean up multiple spaces
    while '  ' in text:
        text = text.replace('  ', ' ')

    # Clean up leading/trailing whitespace and pipes
    text = text.strip(' |')

    # Remove any remaining leading/trailing quotes
    text = text.strip('"')

    return text


def fix_csv(input_path: Path, output_path: Path) -> dict:
    """
    Fix the malformed CSV and write a clean version.

    Returns statistics about the fix.
    """
    import csv

    fieldnames, rows = parse_malformed_csv(input_path)

    # Write the fixed CSV
    with open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    stats = {
        "total_rows": len(rows),
        "first_row_number": rows[0]['ABSOLUTE_ROWNUMBER'] if rows else None,
        "last_row_number": rows[-1]['ABSOLUTE_ROWNUMBER'] if rows else None,
    }

    return stats


if __name__ == "__main__":
    data_dir = Path(__file__).parent
    input_file = data_dir / "storm_data_search_results_backup.csv"
    output_file = data_dir / "storm_data_search_results.csv"

    print(f"Reading from: {input_file}")
    print(f"Writing to: {output_file}")
    print()

    stats = fix_csv(input_file, output_file)

    print("Results:")
    print(f"  Total records: {stats['total_rows']}")
    print(f"  First ABSOLUTE_ROWNUMBER: {stats['first_row_number']}")
    print(f"  Last ABSOLUTE_ROWNUMBER: {stats['last_row_number']}")
    print()
    print("Done! The fixed CSV has been written.")
