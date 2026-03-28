---
name: playwright-mcp-frontend-debug
description: 'Debug frontend issues with Playwright MCP in a real browser. Use when investigating UI bugs, broken interactions, console errors, layout regressions, hydration/client-side failures, auth flows, or browser-only problems.'
argument-hint: 'Describe the frontend issue, expected behavior, repro steps, and local URL if known'
user-invocable: true
disable-model-invocation: false
---

# Playwright MCP Frontend Debug

Use this skill to debug frontend issues in a real browser with Playwright MCP instead of relying on static code inspection alone.

## When to Use
- The bug only appears in the browser.
- The issue involves rendering, layout, styling, navigation, forms, auth, hydration, or client-side state.
- You need browser console evidence, screenshots, or step-by-step UI reproduction.
- You need to confirm whether a fix works from the user's perspective.

## Inputs to Gather
- Expected behavior
- Actual behavior
- Reproduction steps
- Target URL or route
- Whether the app is already running locally

If any of these are missing, ask for the smallest missing detail before proceeding.

## Procedure
1. Confirm the target surface.
Identify the exact page, component area, viewport, account state, and user action sequence involved in the bug.

2. Use a real browser first.
Start Playwright MCP and load the local app in a browser. Prefer browser automation over raw HTTP requests for frontend debugging because it captures rendering, JavaScript execution, console errors, and interaction failures.

3. Reproduce before editing.
Navigate to the relevant route and perform the user's sequence exactly. Record whether the issue reproduces consistently, intermittently, or not at all.

4. Capture evidence.
Gather the narrowest useful signals:
- Browser console messages for runtime errors and warnings
- Screenshot of the broken state when visual evidence matters
- DOM or page-state checks via browser evaluation when you need computed text, attributes, or state
- Notes on the exact user action that triggered the failure

5. Branch on the failure mode.
- If there is a console error: capture the error text first, then trace the source in the codebase.
- If the UI is visually wrong: capture a screenshot and inspect the affected markup/state before changing styles.
- If an interaction fails silently: verify selectors, disabled state, overlays, focus handling, validation, and network-triggering actions.
- If the issue depends on auth or persisted state: establish the minimum state needed and document it clearly.
- If the bug does not reproduce: vary viewport, route params, seeded state, and timing assumptions before concluding it is blocked.

6. Isolate the root cause.
Search the codebase only after you have browser evidence. Map the observed behavior to the smallest likely code path: component, hook, route guard, form logic, API call, CSS rule, or client-side effect.

7. Implement the smallest safe fix.
Change the minimum code necessary to address the observed root cause. Avoid refactors unless the bug cannot be fixed safely otherwise.

8. Verify in the browser again.
Re-run the same Playwright MCP flow after the fix. Confirm both that the original bug is gone and that the critical nearby interaction still works.

9. Report using evidence.
Summarize reproduction status, root cause, code change, and browser-based verification results. Include any remaining uncertainty.

## Tooling Guidance
- Prefer Playwright MCP browser automation for reproduction and verification.
- Use console capture before changing code when JavaScript errors are present.
- Use screenshots when the problem is visual or stateful.
- Use workspace search and file reads only after browser evidence points to a likely code path.

## Completion Checks
- The issue was reproduced in a browser, or the blockage is explicitly documented.
- Evidence was captured before code changes.
- The fix addresses a root cause rather than masking symptoms.
- The original user flow was re-tested after the change.
- Residual risks or missing environment details are called out explicitly.

## Output Format
When using this skill, report progress in this order:
1. Browser reproduction status
2. Evidence captured
3. Root cause status
4. Fix status
5. Browser verification status
6. Open risks or blockers
