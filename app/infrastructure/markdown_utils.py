"""
Markdown normalization utilities.

This module provides functions to normalize and fix common Markdown formatting issues
that may occur in LLM-generated output, such as missing line breaks around headers,
tables, lists, and code blocks.
"""

import re


def _repair_compact_markdown(text: str) -> str:
    """
    Repair Markdown that was generated as one compact paragraph.

    The goal is not to invent formatting, but to restore structural separators
    around explicit Markdown markers that are already present in the model
    output, such as `###标题`, `。###下一节`, or `1.列表项 2.列表项`.
    """
    result = text.replace("\r\n", "\n").replace("\r", "\n")

    # `###标题` is not a Markdown heading. CommonMark requires a space.
    result = re.sub(r"(?m)^(#{1,6})(?!#)(?=\S)", r"\1 ", result)

    # When a later heading marker is glued to the previous sentence, put it on
    # a fresh block. Avoid single `#` here because it is too common in prose.
    result = re.sub(r"([。！？!?；;：:])\s*(#{2,6})(?!#)(?=\S)", r"\1\n\n\2 ", result)
    result = re.sub(r"(?m)^(#{1,6})\s*", lambda match: f"{match.group(1)} ", result)

    # Repair numbered lists that were flattened into one paragraph.
    result = re.sub(r"([。！？!?；;：:])\s*(\d+[.)、])(?=\S)", r"\1\n\2 ", result)
    result = re.sub(r"(\S)\s+(\d+[.)、])(?=[^\d\s])", r"\1\n\2 ", result)
    result = re.sub(r"(?m)^(\d+[.)、])(?=\S)", r"\1 ", result)

    # Repair bullet lists without touching emphasis markers in normal prose.
    result = re.sub(r"([。！？!?；;：:])\s*([*+-])(?=\S)", r"\1\n\2 ", result)
    result = re.sub(r"(?m)^([*+-])(?=\S)", r"\1 ", result)

    # Common compact table shape from JSON/string aggregation: `| a | b || -- | -- |`.
    result = re.sub(r"\|\s*\|", "|\n|", result)

    return result


def normalize_markdown(text):
    """
    Normalize Markdown text by fixing common formatting issues.

    Args:
        text: The Markdown text to normalize.

    Returns:
        Normalized Markdown text with proper line breaks.
    """
    if not text:
        return text

    text = _repair_compact_markdown(text)

    lines = text.split('\n')
    normalized_lines = []
    in_code_block = False
    code_block_fence = ''

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Handle code blocks
        if stripped.startswith('```'):
            if not in_code_block:
                # Start of code block - ensure blank line before if not first line
                if normalized_lines and normalized_lines[-1].strip():
                    normalized_lines.append('')
                in_code_block = True
                code_block_fence = stripped
                normalized_lines.append(line)
            else:
                # End of code block - ensure blank line after
                normalized_lines.append(line)
                in_code_block = False
                code_block_fence = ''
                # Add blank line after code block if next line exists and is not blank
                if i + 1 < len(lines) and lines[i + 1].strip():
                    normalized_lines.append('')
            continue

        if in_code_block:
            # Inside code block, preserve as-is
            normalized_lines.append(line)
            continue

        # Handle headers - ensure blank lines before and after
        if stripped.startswith('#'):
            # Add blank line before header if previous line exists and is not blank
            if normalized_lines and normalized_lines[-1].strip():
                normalized_lines.append('')
            normalized_lines.append(line)
            # Add blank line after header if next line exists and is not blank/header
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not next_line.startswith('#'):
                    normalized_lines.append('')
            continue

        # Handle list items - ensure proper line breaks
        if re.match(r'^[-\*\+]|\d+\.', stripped):
            normalized_lines.append(line)
            # If next line is also a list item or content, ensure separation
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not re.match(r'^[-\*\+]|\d+\.', next_line) and not next_line.startswith('#'):
                    # Add blank line after list if next is paragraph
                    pass  # We'll handle in next iteration
            continue

        # Handle table rows - ensure each row is on its own line
        if '|' in stripped and not stripped.startswith('|') and not stripped.endswith('|'):
            # This might be a table row, but we need to check context
            # For simplicity, assume table rows are properly formatted
            normalized_lines.append(line)
            continue

        # Regular content
        normalized_lines.append(line)

    # Join lines back
    result = '\n'.join(normalized_lines)

    # Merge excessive blank lines (more than 2 consecutive)
    result = re.sub(r'\n{3,}', '\n\n', result)

    return result


def looks_like_broken_markdown(text):
    """
    Check if the text appears to have broken Markdown formatting.

    Args:
        text: The text to check.

    Returns:
        True if the text likely has formatting issues.
    """
    if not text:
        return False

    if re.search(r"(^|[。！？!?；;：:\s])#{1,6}\S", text):
        return True
    if re.search(r"[。！？!?；;：:]\s*(#{2,6}|\d+[.)、]|[*+-])\S", text):
        return True

    lines = text.split('\n')

    # Check for headers without proper spacing
    for i, line in enumerate(lines):
        if line.strip().startswith('#'):
            # Check previous line
            if i > 0 and lines[i-1].strip():
                return True
            # Check next line
            if i + 1 < len(lines) and lines[i+1].strip() and not lines[i+1].strip().startswith('#'):
                return True

    # Check for code blocks without proper spacing
    in_code_block = False
    for i, line in enumerate(lines):
        if line.strip().startswith('```'):
            if not in_code_block:
                if i > 0 and lines[i-1].strip():
                    return True
                in_code_block = True
            else:
                if i + 1 < len(lines) and lines[i+1].strip():
                    return True
                in_code_block = False

    # Check for excessive blank lines
    if '\n\n\n' in text:
        return True

    return False


def normalize_markdown_if_needed(text):
    """
    Normalize Markdown text only if it appears to have formatting issues.

    Args:
        text: The Markdown text to potentially normalize.

    Returns:
        Normalized text if issues detected, otherwise original text.
    """
    if looks_like_broken_markdown(text):
        return normalize_markdown(text)
    return text
