# Vecinita Architectural Discipline

## 1. Script Documentation Standard
Every script or tool created for this project must lead with a standardized header. This allows students to trace the "Data Morphing" process from input to output.

### Header Template
```python
# ############################################################################
# FILE: [filename.py]
# PATH: [src/path/to/file.py]
# ROLE: [Describe how this script transforms data]
# INPUT: [Source of data] -> OUTPUT: [Destination of data]
# ############################################################################
2. The "Data Morphing" Trace
Developers must include a docstring in primary functions explaining how data is transformed. This is a teaching requirement to show students how a Natural Language question becomes a Machine-Readable vector and finally a Human-Readable answer.

Trace Example:

Input: Raw User String.

Morph 1: String to Embedding (Vectorization).

Morph 2: Vector to Database Matches (Similarity Search).

Morph 3: Context List to Final LLM Prompt (Augmentation).

Output: Structured JSON response.

3. Script Naming & Location
To prevent project abandonment through chaos, maintain strict directory discipline:

Agent Tools: src/agent/tools/ (snake_case, e.g., db_search.py).

Core Engine: src/agent/main.py.

System Rules: src/agent/data/system_rules.md.

Validation: tests/ or scripts/.

4. End of File (EOF) Markers
To ensure code integrity and visibility of the full script, every file must end with a specific marker.

Standard: Append ## end-of-file [filename] on the final line.

Exceptions: For file formats that do not support # comments (like JSON or certain configurations), use the native comment syntax (e.g., // for JS) or omit if no comment syntax exists.

5. Token Management (Pre-LLM Filtering)
To ensure system stability with Groq/LLM providers:

Truncation: Data must be truncated at the Source Tool before reaching the LLM.

Constraint: Context chunks should not exceed 800-1000 characters to prevent 413 "Payload Too Large" errors.


## end-of-file ARCH_DISCIPLINE.md
