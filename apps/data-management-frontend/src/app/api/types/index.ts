/**
 * Canonical **FR-010** import surface for DM client + tests.
 * Scraper job DTOs are generated from the committed OpenAPI snapshot (`dm-openapi.generated.ts`) and re-exported via `modal-types.ts`.
 * Corpus / dashboard shapes in `dm-api-dtos.ts` stay hand-written until a corpus OpenAPI is pinned the same way.
 */
export type {
  FrontendScrapeJob,
  KnownScrapeJob,
  ModalCreateJobResponse,
  ModalJobStatus,
  ModalJobStatusResponse,
  ModalListJobsResponse,
  ModalScrapeJobRequest,
  ScrapeJobListItem,
} from '../modal-types';

export type { components as DmOpenAPIComponents } from './dm-openapi.generated';

export * from './dm-api-dtos';
