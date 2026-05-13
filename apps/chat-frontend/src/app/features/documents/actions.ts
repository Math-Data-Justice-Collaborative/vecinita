import type { Source } from '../../services/documentsService';

export function canPerformDocumentMutation(): boolean {
  return false;
}

export function canDownloadDocumentSource(source: Source): boolean {
  if (source.url.startsWith('http')) {
    return false;
  }
  return Boolean(source.downloadable || source.download_url);
}
