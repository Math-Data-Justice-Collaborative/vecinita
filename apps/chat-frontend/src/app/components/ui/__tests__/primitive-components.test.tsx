import { act, fireEvent, render, renderHook, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '../card';
import { Input } from '../input';
import { Label } from '../label';
import { Skeleton } from '../skeleton';
import { Toggle } from '../toggle';
import { useIsMobile } from '../use-mobile';

describe('primitive UI components', () => {
  it('renders card primitives with expected slots and content', () => {
    render(
      <Card data-testid="card">
        <CardHeader>
          <CardTitle>Title</CardTitle>
          <CardDescription>Description</CardDescription>
          <CardAction>Action</CardAction>
        </CardHeader>
        <CardContent>Content</CardContent>
        <CardFooter>Footer</CardFooter>
      </Card>
    );

    expect(screen.getByTestId('card')).toHaveAttribute('data-slot', 'card');
    expect(screen.getByText('Title')).toHaveAttribute('data-slot', 'card-title');
    expect(screen.getByText('Description')).toHaveAttribute('data-slot', 'card-description');
    expect(screen.getByText('Action')).toHaveAttribute('data-slot', 'card-action');
    expect(screen.getByText('Content')).toHaveAttribute('data-slot', 'card-content');
    expect(screen.getByText('Footer')).toHaveAttribute('data-slot', 'card-footer');
  });

  it('renders input, label, and skeleton with passed props', () => {
    render(
      <div>
        <Label htmlFor="name">Name</Label>
        <Input id="name" type="email" disabled placeholder="Email" />
        <Skeleton data-testid="skeleton" className="extra" />
      </div>
    );

    expect(screen.getByText('Name')).toHaveAttribute('data-slot', 'label');
    expect(screen.getByPlaceholderText('Email')).toHaveAttribute('data-slot', 'input');
    expect(screen.getByPlaceholderText('Email')).toBeDisabled();
    expect(screen.getByTestId('skeleton')).toHaveAttribute('data-slot', 'skeleton');
    expect(screen.getByTestId('skeleton')).toHaveClass('extra');
  });

  it('toggles pressed state through the Radix wrapper', () => {
    render(<Toggle aria-label="toggle feature">Toggle me</Toggle>);

    const toggle = screen.getByRole('button', { name: 'toggle feature' });
    expect(toggle).toHaveAttribute('data-slot', 'toggle');
    expect(toggle).toHaveAttribute('data-state', 'off');

    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('data-state', 'on');
  });

  it('reports mobile state from window width and matchMedia changes', () => {
    const listeners: Array<() => void> = [];
    Object.defineProperty(window, 'innerWidth', { configurable: true, value: 500 });
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: query.includes('767px'),
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: (_: string, callback: () => void) => listeners.push(callback),
      removeEventListener: (_: string, callback: () => void) => {
        const index = listeners.indexOf(callback);
        if (index >= 0) listeners.splice(index, 1);
      },
      dispatchEvent: () => true,
    }));

    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(true);

    Object.defineProperty(window, 'innerWidth', { configurable: true, value: 1024 });
    act(() => {
      listeners.forEach((listener) => listener());
    });

    expect(result.current).toBe(false);
  });
});
