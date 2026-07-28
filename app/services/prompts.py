from typing import Optional


def build_review_prompt(diff: str, context: Optional[str], language: Optional[str]) -> str:
    parts = ["Review the following code diff and identify issues."]

    if language:
        parts.append(f"Primary language: {language}")
    if context:
        parts.append(f"Additional context:\n{context}")

    parts.append(f"Diff:\n{diff}")
    parts.append(
        "For each issue found, report its severity (critical, high, medium, low, info), "
        "a short title, a description, the affected file and line if identifiable, and a "
        "suggested fix. Also provide a short overall summary and an overall_assessment of "
        "'approve', 'request_changes', or 'comment'."
    )
    return "\n\n".join(parts)
