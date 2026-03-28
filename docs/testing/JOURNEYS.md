# User Journey Test Catalogue

This document tracks end-to-end user journeys with stable IDs.

| ID | Name | User Type | Entry URL | Expected Outcome | Spec |
|---|---|---|---|---|---|
| J001 | Load chat home | Anonymous | `/` | Chat heading and input visible | `frontend/e2e/journey-chat.spec.ts` |
| J002 | Send English question | Anonymous | `/` | User message bubble persists | `frontend/e2e/journey-chat.spec.ts` |
| J003 | Receive assistant answer | Anonymous | `/` | Assistant message with content appears | `frontend/e2e/journey-chat.spec.ts` |
| J004 | View sources | Anonymous | `/` | Source cards show external links | `frontend/e2e/journey-chat.spec.ts` |
| J005 | Start new chat | Anonymous | `/` | Prior messages cleared; new thread starts | `frontend/e2e/journey-chat.spec.ts` |
| J006 | Send Spanish question | Anonymous | `/` | Spanish answer or localized output appears | `frontend/e2e/journey-chat.spec.ts` |
| J007 | Retry failed answer | Anonymous | `/` | Retry reissues request and recovers UI | `frontend/e2e/journey-chat.spec.ts` |
| J008 | Observe streaming response | Anonymous | `/` | Partial tokens render before final completion | `frontend/e2e/journey-chat.spec.ts` |
| J009 | Load documents dashboard | Anonymous | `/documents` | Heading, cards, and table visible | `frontend/e2e/journey-documents.spec.ts` |
| J010 | Render topic filters | Anonymous | `/documents` | Topic chips/buttons rendered from API | `frontend/e2e/journey-documents.spec.ts` |
| J011 | Filter by topic | Anonymous | `/documents` | Source table narrows to matching rows | `frontend/e2e/journey-documents.spec.ts` |
| J012 | Clear filters | Anonymous | `/documents` | Full source list restored | `frontend/e2e/journey-documents.spec.ts` |
| J013 | Search documents | Anonymous | `/documents` | Search narrows visible rows | `frontend/e2e/journey-documents.spec.ts` |
| J014 | Open source link | Anonymous | `/documents` | Source link opens in new tab with correct href | `frontend/e2e/journey-documents.spec.ts` |
| J015 | Toggle documents language | Anonymous | `/documents` | Labels switch between English and Spanish | `frontend/e2e/journey-documents.spec.ts` |
| J016 | View empty documents state | Anonymous | `/documents` | Empty state UI shown for no data | `frontend/e2e/journey-documents.spec.ts` |
| J017 | Redirect unauthenticated admin access | Anonymous | `/admin` | Redirected to login with return URL | `frontend/e2e/journey-admin.spec.ts` |
| J018 | Admin login success | Admin | `/login` | Redirects to admin dashboard | `frontend/e2e/journey-admin.spec.ts` |
| J019 | View admin sources list | Admin | `/admin` | Sources table loads current entries | `frontend/e2e/journey-admin.spec.ts` |
| J020 | Add source from admin | Admin | `/admin` | New source appears in list or queue | `frontend/e2e/journey-admin.spec.ts` |
| J021 | Upload document file | Admin | `/admin` | Upload success notification shown | `frontend/e2e/journey-admin.spec.ts` |
| J022 | View processing queue | Admin | `/admin` | Queue rows and statuses visible | `frontend/e2e/journey-admin.spec.ts` |
| J023 | Save model settings | Admin | `/admin` | Save confirmation shown; settings persist | `frontend/e2e/journey-admin.spec.ts` |
| J024 | Admin sign out | Admin | `/admin` | Returns to public home/login state | `frontend/e2e/journey-admin.spec.ts` |
| J025 | Invalid admin login | Anonymous | `/login` | Error shown; no dashboard access | `frontend/e2e/journey-admin.spec.ts` |
| J026 | Reject non-admin dashboard access | Authenticated User | `/admin` | 403 or redirect away from admin | `frontend/e2e/journey-admin.spec.ts` |

## Maintenance

- Keep IDs stable once introduced.
- Every new journey test must add one row here and reference its exact spec file.
- Remove stale rows when journeys are removed or merged.
