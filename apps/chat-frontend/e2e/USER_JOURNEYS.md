# Frontend E2E User Journeys

This project currently defines and automates more than 10 user journeys in Playwright.

## Journey Map

1. `J001` Chat home loads
- Test: `frontend/e2e/journey-chat.spec.ts`

2. `J002` User sends English question
- Test: `frontend/e2e/journey-chat.spec.ts`

3. `J003` Assistant answer appears
- Test: `frontend/e2e/journey-chat.spec.ts`

4. `J004` Source cards open external links
- Test: `frontend/e2e/journey-chat.spec.ts`

5. `J005` New chat clears prior messages
- Test: `frontend/e2e/journey-chat.spec.ts`

6. `J006` Spanish question flow works
- Test: `frontend/e2e/journey-chat.spec.ts`

7. `J007` Retry after failed ask request
- Test: `frontend/e2e/journey-chat.spec.ts`

8. `J008` Streaming progress is shown before completion
- Test: `frontend/e2e/journey-chat.spec.ts`

9. `J009` Documents dashboard loads
- Test: `frontend/e2e/journey-documents.spec.ts`

10. `J010` Topic filters render
- Test: `frontend/e2e/journey-documents.spec.ts`

11. `J011` Topic filter reduces/limits result set
- Test: `frontend/e2e/journey-documents.spec.ts`

12. `J012` Clear filters restores unfiltered view
- Test: `frontend/e2e/journey-documents.spec.ts`

13. `J013` Documents search flow works
- Test: `frontend/e2e/journey-documents.spec.ts`

14. `J014` Source link opens in new tab
- Test: `frontend/e2e/journey-documents.spec.ts`

15. `J015` Language toggle updates labels
- Test: `frontend/e2e/journey-documents.spec.ts`

16. `J016` Empty-state rendering when no sources exist
- Test: `frontend/e2e/journey-documents.spec.ts`

17. `J017` Unauthenticated admin access redirects to login
- Test: `frontend/e2e/journey-admin.spec.ts`

18. `J018` Admin login lands on admin dashboard
- Test: `frontend/e2e/journey-admin.spec.ts`

19. `J019` Admin source list view
- Test: `frontend/e2e/journey-admin.spec.ts`

20. `J020` Admin adds source
- Test: `frontend/e2e/journey-admin.spec.ts`

21. `J021` Admin uploads document
- Test: `frontend/e2e/journey-admin.spec.ts`

22. `J022` Admin queue view
- Test: `frontend/e2e/journey-admin.spec.ts`

23. `J023` Admin model settings save
- Test: `frontend/e2e/journey-admin.spec.ts`

24. `J024` Admin sign-out path
- Test: `frontend/e2e/journey-admin.spec.ts`

25. `J025` Invalid credentials error path
- Test: `frontend/e2e/journey-admin.spec.ts`

26. `J026` Non-admin user denied admin access
- Test: `frontend/e2e/journey-admin.spec.ts`

## Execution

- Install browsers: `npm run test:e2e:install-browsers`
- Run all journeys: `npm run test:e2e`
