"""Minimal type stubs for the untyped `langdetect` package.

Only the surface Vecinita uses is declared: `detect()` and `LangDetectException`
(see packages/rag/.../language.py and packages/tagging/.../vocabulary.py). This
replaces scattered `# pyright: ignore[reportUnknownMemberType]` waivers with a real
typed boundary (docs/typing-policy.md §stubs).
"""

class LangDetectException(Exception):
    def __init__(self, code: object = ..., message: str = ...) -> None: ...

def detect(text: str) -> str: ...
def detect_langs(text: str) -> list[object]: ...
