export type ResponseParseCode = 'INVALID_RESPONSE_FORMAT' | 'INVALID_JSON';

type ErrorFactory<E extends Error> = (
  message: string,
  statusCode: number,
  code: ResponseParseCode
) => E;

interface ParseJsonOptions<E extends Error> {
  errorFactory?: ErrorFactory<E>;
  nonJsonHint?: string;
  invalidJsonHint?: string;
}

export async function parseJsonResponseOrThrow<T, E extends Error = Error>(
  response: Response,
  endpointLabel: string,
  options: ParseJsonOptions<E> = {}
): Promise<T> {
  const contentType = response.headers?.get?.('content-type')?.toLowerCase() || '';
  const hasContentType = contentType.length > 0;
  const looksJson = contentType.includes('application/json');

  const buildError = (message: string, code: ResponseParseCode): E => {
    if (options.errorFactory) {
      return options.errorFactory(message, response.status, code);
    }
    return new Error(message) as E;
  };

  if (hasContentType && !looksJson) {
    const message =
      `${endpointLabel} returned non-JSON response (content-type: ${contentType || 'unknown'}). ` +
      (options.nonJsonHint || 'Check gateway URL configuration.');
    throw buildError(message, 'INVALID_RESPONSE_FORMAT');
  }

  try {
    return (await response.json()) as T;
  } catch {
    const message =
      `${endpointLabel} returned malformed JSON. ` +
      (options.invalidJsonHint || 'Check gateway URL configuration.');
    throw buildError(message, 'INVALID_JSON');
  }
}
