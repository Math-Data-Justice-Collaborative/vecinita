# Feature Specification: Chat Message Presentation

**Feature Branch**: `007-chat-message-presentation`  
**Created**: 2026-04-22  
**Status**: Draft  
**Input**: User description: "On the frontend, improve the visual presentation of the chat interface, specifically agent-returned chat messages that are currently shown as raw structured response payloads."

## Clarifications

### Session 2026-04-22

- Q: What rendering mode should assistant replies use? → A: Rich text with markdown + tables + images embedded inline.
- Q: How should remote images be handled in assistant messages? → A: Convert remote images to clickable links (no inline loading).
- Q: How should wide markdown tables be displayed in chat bubbles? → A: Keep table layout and enable horizontal scroll within the message.
- Q: How should raw HTML inside markdown replies be handled? → A: Strip/escape raw HTML and render markdown-only elements.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Readable Agent Replies (Priority: P1)

As a resident using the chat interface, I want agent replies to appear as clean, readable chat messages so I can quickly understand the answer without seeing technical response metadata.

**Why this priority**: The core value of chat is comprehension; raw payloads reduce usability and trust immediately.

**Independent Test**: Can be fully tested by submitting a query and confirming only human-readable reply text is shown in the assistant message bubble while technical fields are not shown as message body content.

**Acceptance Scenarios**:

1. **Given** a successful agent response containing metadata and reply text, **When** the assistant message is rendered, **Then** the UI displays only the reply text content in the main chat body.
2. **Given** an agent response containing long multi-paragraph content, **When** the message is rendered, **Then** line breaks and list-style formatting remain readable in the chat bubble.
3. **Given** an agent response containing markdown tables or safe inline images (same-origin static assets or data URLs), **When** the message is rendered, **Then** those elements appear inline and remain readable within the conversation layout.
4. **Given** an agent response containing remote image URLs, **When** the message is rendered, **Then** each remote image is shown as a clickable link instead of loading inline media.
5. **Given** an assistant response with a table wider than the message container, **When** the table is rendered, **Then** the table remains intact and is horizontally scrollable inside the message boundary.

---

### User Story 2 - Clear Visual Hierarchy in Conversation (Priority: P2)

As a resident reviewing a conversation, I want user and assistant messages to be visually distinct and consistently styled so I can scan the thread quickly.

**Why this priority**: Visual hierarchy improves task completion speed and reduces confusion during back-and-forth exchanges.

**Independent Test**: Can be tested by rendering a mixed thread and verifying sender-specific styling, spacing, and alignment are consistent for each message type.

**Acceptance Scenarios**:

1. **Given** a thread with alternating user and assistant messages, **When** the chat is displayed, **Then** each sender type has consistent styling that makes authorship obvious at a glance.
2. **Given** multiple assistant responses in sequence, **When** they are rendered, **Then** spacing and typography remain consistent without overlapping or visual clipping.

---

### User Story 3 - Graceful Handling of Missing or Irregular Content (Priority: P3)

As a resident, I want the chat UI to handle partial or irregular responses gracefully so I still receive a clear message experience even when the response shape varies.

**Why this priority**: Irregular responses are less common but can create broken-looking UI if not handled.

**Independent Test**: Can be tested by simulating responses with missing message text and verifying fallback behavior keeps the chat readable and non-technical.

**Acceptance Scenarios**:

1. **Given** an agent response where reply text is empty or missing, **When** the message is rendered, **Then** the UI shows a clear fallback assistant message instead of raw object output.
2. **Given** an agent response that includes extra metadata fields, **When** the message is rendered, **Then** unknown technical fields are ignored in visual chat content.

---

### Edge Cases

- What happens when the assistant reply includes markdown-like bullets, numbered lists, tables, embedded images, remote image URLs, or extra whitespace?
- What happens when table width exceeds the chat bubble width on smaller screens?
- How does the interface behave when a response arrives with metadata but no displayable text?
- What happens when a single assistant message is significantly longer than typical viewport height?
- How does rendering behave when special characters, quoted JSON fragments, or escaped newline sequences appear in the assistant text?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST render assistant chat messages from the semantic reply text field rather than displaying the full structured response payload.
- **FR-002**: The system MUST keep technical metadata (for example model, timing, token counts, or internal fields) out of the primary chat message body.
- **FR-003**: The system MUST render assistant content as rich markdown output, including headings, lists, emphasis, links, code blocks, tables, and safe inline images when present in the response text; safe inline images are limited to same-origin static assets or data URLs.
- **FR-004**: The system MUST apply consistent visual styling for assistant messages across all turns in a session.
- **FR-005**: The system MUST apply consistent visual distinction between user messages and assistant messages so sender identity is immediately clear.
- **FR-006**: The system MUST handle missing or empty assistant text with a user-friendly fallback message instead of exposing raw response objects.
- **FR-007**: Users MUST be able to continue sending and receiving messages without layout breakage when assistant responses are very long.
- **FR-008**: The system MUST keep existing chat interaction behavior unchanged aside from message presentation improvements.
- **FR-009**: The system MUST keep rich markdown elements visually contained within the chat timeline so tables and images do not break message boundaries or overlap other interface elements.
- **FR-010**: The system MUST render remote image references as clickable links rather than loading them inline in chat messages.
- **FR-011**: The system MUST preserve table structure and provide horizontal scrolling within the message container when table content exceeds available width.
- **FR-012**: The system MUST strip or escape raw HTML embedded in assistant reply content and render only supported markdown-derived elements in the message body.

### Key Entities *(include if feature involves data)*

- **Assistant Response Payload**: Structured response returned by the agent that may include metadata, status fields, and nested reply content.
- **Display Message**: Sanitized, user-facing text representation rendered in the chat timeline.
- **Message Role**: Sender classification for each turn (user or assistant) used to determine visual treatment.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance testing, 100% of assistant messages display human-readable reply text and do not display raw response-object syntax in the chat body.
- **SC-002**: At least 90% of test participants can correctly identify message sender (user vs assistant) within 2 seconds when viewing a mixed conversation thread.
- **SC-003**: In test scenarios with long assistant replies, 100% of sessions preserve readable layout without overlap, clipping, or blocked follow-up input.
- **SC-004**: At least 90% of test participants rate assistant response readability as improved versus the current interface.
- **SC-005**: In acceptance tests containing markdown tables and inline images, 100% of assistant messages render these elements in-place without raw markdown tokens being shown to users.
- **SC-006**: In acceptance tests containing remote image links, 100% of remote image references are rendered as links and 0% trigger inline remote image loading in the message body.
- **SC-007**: In acceptance tests with oversized tables, 100% of tables remain readable via in-message horizontal scrolling without truncating columns or breaking chat layout.
- **SC-008**: In acceptance tests containing raw HTML in assistant replies, 100% of HTML tags are escaped or removed from rendered output while markdown content remains readable.

## Assumptions

- The frontend already receives a response field that represents the intended assistant reply text, even when additional metadata is present.
- Improving visual presentation for assistant messages in the existing chat interface is in scope; broader chat feature redesign is out of scope.
- Existing message send/receive flow, backend behavior, and access controls remain unchanged.
- This feature targets the current frontend chat experience before considering additional channels (such as mobile-native clients).
