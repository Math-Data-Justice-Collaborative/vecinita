# Data Model: Chat Message Presentation

## Entity: AssistantResponsePayload

- **Description**: Raw structured response from agent service, including metadata and nested assistant content.
- **Key Attributes**:
  - `message.role` (expected `assistant`)
  - `message.content` (primary semantic reply text)
  - metadata fields (model, timing, token counts, status fields)
- **Validation Rules**:
  - Missing or empty `message.content` triggers fallback display message.
  - Metadata fields are excluded from user-visible message body rendering.

## Entity: DisplayMessage

- **Description**: Normalized, user-facing message object used by chat UI rendering.
- **Key Attributes**:
  - `role` (`assistant` or `user`)
  - `text` (sanitized markdown source)
  - `renderPolicy` (ruleset for HTML stripping, remote image handling, table overflow)
  - `fallbackUsed` (boolean for missing/empty assistant content)
- **Validation Rules**:
  - `text` must be non-empty after normalization; otherwise fallback text is injected.
  - Raw HTML tags in source are escaped or removed before rendering.
  - Remote image markdown is transformed to link representation.

## Entity: RenderPolicy

- **Description**: Declarative policy controlling supported markdown behavior in chat UI.
- **Key Attributes**:
  - `allowMarkdown`: true
  - `allowRawHtml`: false
  - `remoteImageMode`: `link_only`
  - `tableOverflowMode`: `horizontal_scroll`
- **Validation Rules**:
  - Policy must be consistently applied to all assistant messages in a session.
  - Policy output must remain visually bounded inside message container.

## Lifecycle / State Transitions

1. Receive `AssistantResponsePayload`.
2. Extract semantic assistant content.
3. Normalize into `DisplayMessage` (apply fallback if needed).
4. Apply `RenderPolicy` transformation/sanitization.
5. Render in chat timeline with role-specific visual treatment.

## Scale Assumptions

- Long assistant messages and wide tables are common enough to require explicit overflow handling.
- Rendering must remain responsive for typical multi-turn sessions without blocking next input.
