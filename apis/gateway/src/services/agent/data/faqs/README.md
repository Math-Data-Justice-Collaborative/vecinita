# Vecinita FAQ System

This directory contains frequently asked questions (FAQs) in markdown format.

## File Structure

- `en.md` - English FAQs
- `es.md` - Spanish FAQs (Preguntas frecuentes en español)

## Format

FAQs are written in simple markdown:

```markdown
## Question text here?

Answer paragraph here. Can be multiple sentences.

## Another question?

Another answer here.
```

### Rules

1. Each question must start with `##` (h2 heading)
2. The answer is the paragraph(s) immediately following the question
3. Questions should be written in natural language as users would ask them
4. One blank line separates each Q&A pair
5. Question matching is case-insensitive and ignores punctuation

## Adding New FAQs

1. Open the appropriate language file (`en.md` or `es.md`)
2. Add your question as an `##` heading
3. Write the answer in the paragraph below
4. Save the file - changes are automatically detected and reloaded

## Question Matching

The system matches user questions using:
1. **Exact match** - Question matches FAQ entry exactly (case-insensitive)
2. **Cleaned match** - After removing punctuation and extra spaces
3. **Partial match** - For queries ≥10 characters, checks if FAQ question contains query or vice versa

## Examples

### Good FAQ Format

```markdown
## What is Vecinita?

Vecinita is a community-based Q&A assistant designed to help people find information about local services, community programs, and resources in Rhode Island.

## How do I contact the watershed council?

You can contact the Woonasquatucket River Watershed Council at:
- Phone: (401) 861-9046
- Email: info@wrwc.org
- Address: 45 Eagle Street, Suite 202, Providence, RI 02909
```

### Bad FAQ Format (Don't do this)

```markdown
What is Vecinita?  <!-- Missing ## heading -->

## How do I contact the watershed council
No answer provided here.  <!-- Need actual answer content -->
```

## Maintenance

- Review FAQs quarterly for accuracy
- Update contact information as needed
- Remove outdated questions
- Monitor logs for frequently asked questions not in the database
