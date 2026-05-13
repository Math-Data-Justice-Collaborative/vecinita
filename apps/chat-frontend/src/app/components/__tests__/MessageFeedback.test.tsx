import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { LanguageProvider } from '@/app/context/LanguageContext';
import { MessageFeedback, type Feedback } from '../MessageFeedback';

function renderFeedback(props: Partial<React.ComponentProps<typeof MessageFeedback>> = {}) {
  const onFeedbackSubmit = vi.fn();
  render(
    <LanguageProvider>
      <MessageFeedback messageId="msg-1" onFeedbackSubmit={onFeedbackSubmit} {...props} />
    </LanguageProvider>
  );

  return { onFeedbackSubmit };
}

describe('MessageFeedback', () => {
  it('opens the comment box and submits positive feedback', () => {
    const { onFeedbackSubmit } = renderFeedback();

    fireEvent.click(screen.getByRole('button', { name: 'Respuesta útil' }));
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Muy útil' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enviar' }));

    expect(onFeedbackSubmit).toHaveBeenCalledTimes(1);
    expect(onFeedbackSubmit.mock.calls[0][0]).toMatchObject({
      messageId: 'msg-1',
      rating: 'positive',
      comment: 'Muy útil',
    });
    expect(screen.getByText('✓ Comentarios enviados')).toBeInTheDocument();
  });

  it('clears feedback when the selected rating is clicked again', () => {
    const { onFeedbackSubmit } = renderFeedback();

    const negative = screen.getByRole('button', { name: 'Respuesta no útil' });
    fireEvent.click(negative);
    fireEvent.click(negative);

    expect(onFeedbackSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ messageId: 'msg-1', rating: null, comment: '' })
    );
  });

  it('uses initial feedback and allows closing the comment box without resetting submitted feedback', () => {
    const initialFeedback: Feedback = {
      messageId: 'msg-1',
      rating: 'positive',
      comment: 'Gracias',
      timestamp: new Date('2026-03-28T00:00:00Z'),
    };

    renderFeedback({ initialFeedback });

    expect(screen.getByText('✓ Comentarios enviados')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Agregar comentario' }));
    expect(screen.getByRole('textbox')).toHaveValue('Gracias');
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }));
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.getByText('✓ Comentarios enviados')).toBeInTheDocument();
  });

  it('resets unsent feedback when the comment box is cancelled', () => {
    renderFeedback();

    fireEvent.click(screen.getByRole('button', { name: 'Respuesta útil' }));
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Draft comment' } });
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }));

    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.queryByText('✓ Comentarios enviados')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Agregar comentario' })).not.toBeInTheDocument();
  });

  it('renders English labels and submits without a callback', () => {
    localStorage.setItem('vecinita-language', 'en');
    renderFeedback({ onFeedbackSubmit: undefined });

    fireEvent.click(screen.getByRole('button', { name: 'Helpful response' }));
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Helpful' } });
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }));

    expect(screen.getByText('✓ Feedback submitted')).toBeInTheDocument();
    localStorage.removeItem('vecinita-language');
  });

  it('clears selected feedback without a callback', () => {
    renderFeedback({ onFeedbackSubmit: undefined });

    const helpfulButton = screen.getByRole('button', { name: 'Respuesta útil' });
    fireEvent.click(helpfulButton);
    fireEvent.click(helpfulButton);

    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Agregar comentario' })).not.toBeInTheDocument();
  });
});
