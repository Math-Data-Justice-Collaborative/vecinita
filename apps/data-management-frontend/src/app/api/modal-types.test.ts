import { describe, expect, it } from 'vitest';
import { clampNumber, isModalTerminalStatus, mapModalStatusToFrontendStatus } from './modal-types';

describe('modal status helpers', () => {
  it('maps queued-like statuses to queued', () => {
    expect(mapModalStatusToFrontendStatus('pending')).toBe('queued');
    expect(mapModalStatusToFrontendStatus('validating')).toBe('queued');
  });

  it('maps terminal statuses correctly', () => {
    expect(mapModalStatusToFrontendStatus('completed')).toBe('completed');
    expect(mapModalStatusToFrontendStatus('failed')).toBe('failed');
    expect(mapModalStatusToFrontendStatus('cancelled')).toBe('failed');
  });

  it('detects terminal states', () => {
    expect(isModalTerminalStatus('completed')).toBe(true);
    expect(isModalTerminalStatus('failed')).toBe(true);
    expect(isModalTerminalStatus('cancelled')).toBe(true);
    expect(isModalTerminalStatus('processing')).toBe(false);
  });

  it('clamps numbers in range', () => {
    expect(clampNumber(5, 1, 10)).toBe(5);
    expect(clampNumber(-1, 0, 10)).toBe(0);
    expect(clampNumber(100, 0, 10)).toBe(10);
  });
});
