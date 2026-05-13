import { useState } from 'react';
import { ThumbsUp, ThumbsDown, MessageSquare, X } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export type FeedbackRating = 'positive' | 'negative' | null;

export interface Feedback {
  messageId: string;
  rating: FeedbackRating;
  comment?: string;
  timestamp: Date;
}

interface MessageFeedbackProps {
  messageId: string;
  onFeedbackSubmit?: (feedback: Feedback) => void;
  initialFeedback?: Feedback;
}

export function MessageFeedback({
  messageId,
  onFeedbackSubmit,
  initialFeedback,
}: MessageFeedbackProps): JSX.Element {
  const { language } = useLanguage();
  const [rating, setRating] = useState<FeedbackRating>(initialFeedback?.rating || null);
  const [showCommentBox, setShowCommentBox] = useState(false);
  const [comment, setComment] = useState(initialFeedback?.comment || '');
  const [isSubmitted, setIsSubmitted] = useState(!!initialFeedback);

  const handleRatingClick = (newRating: 'positive' | 'negative'): void => {
    const finalRating = rating === newRating ? null : newRating;
    setRating(finalRating);

    if (finalRating) {
      setShowCommentBox(true);
    } else {
      setShowCommentBox(false);
      setComment('');
      setIsSubmitted(false);

      // Submit removal of feedback
      if (onFeedbackSubmit) {
        onFeedbackSubmit({
          messageId,
          rating: null,
          comment: '',
          timestamp: new Date(),
        });
      }
    }
  };

  const handleCommentSubmit = (): void => {
    if (!rating) return;

    const feedback: Feedback = {
      messageId,
      rating,
      comment: comment.trim(),
      timestamp: new Date(),
    };

    setIsSubmitted(true);
    setShowCommentBox(false);

    if (onFeedbackSubmit) {
      onFeedbackSubmit(feedback);
    }
  };

  const handleCommentCancel = (): void => {
    setShowCommentBox(false);
    if (!isSubmitted) {
      setRating(null);
      setComment('');
    }
  };

  return (
    <div className="flex flex-col gap-2">
      {/* Rating Buttons */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">
          {language === 'es' ? '¿Fue útil esta respuesta?' : 'Was this response helpful?'}
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => handleRatingClick('positive')}
            className={`p-1.5 rounded-lg transition-all hover:bg-accent ${
              rating === 'positive'
                ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                : 'text-muted-foreground hover:text-foreground'
            }`}
            aria-label={language === 'es' ? 'Respuesta útil' : 'Helpful response'}
            title={language === 'es' ? 'Respuesta útil' : 'Helpful response'}
          >
            <ThumbsUp className="w-4 h-4" aria-hidden="true" />
          </button>
          <button
            onClick={() => handleRatingClick('negative')}
            className={`p-1.5 rounded-lg transition-all hover:bg-accent ${
              rating === 'negative'
                ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
                : 'text-muted-foreground hover:text-foreground'
            }`}
            aria-label={language === 'es' ? 'Respuesta no útil' : 'Not helpful response'}
            title={language === 'es' ? 'Respuesta no útil' : 'Not helpful response'}
          >
            <ThumbsDown className="w-4 h-4" aria-hidden="true" />
          </button>
          {rating && !showCommentBox && (
            <button
              onClick={() => setShowCommentBox(true)}
              className="p-1.5 rounded-lg transition-all hover:bg-accent text-muted-foreground hover:text-foreground"
              aria-label={language === 'es' ? 'Agregar comentario' : 'Add comment'}
              title={language === 'es' ? 'Agregar comentario' : 'Add comment'}
            >
              <MessageSquare className="w-4 h-4" aria-hidden="true" />
            </button>
          )}
        </div>
        {isSubmitted && (
          <span className="text-xs text-green-600 dark:text-green-400">
            {language === 'es' ? '✓ Comentarios enviados' : '✓ Feedback submitted'}
          </span>
        )}
      </div>

      {/* Comment Box */}
      {showCommentBox && (
        <div className="bg-accent/50 border border-border rounded-lg p-3 space-y-2 animate-in fade-in slide-in-from-top-1 duration-200">
          <div className="flex items-start justify-between gap-2">
            <label
              htmlFor={`feedback-comment-${messageId}`}
              className="text-xs font-medium text-foreground"
            >
              {language === 'es' ? '¿Qué podríamos mejorar?' : 'What could we improve?'}
            </label>
            <button
              onClick={handleCommentCancel}
              className="p-0.5 rounded hover:bg-accent transition-colors text-muted-foreground hover:text-foreground"
              aria-label={language === 'es' ? 'Cerrar' : 'Close'}
            >
              <X className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
          </div>
          <textarea
            id={`feedback-comment-${messageId}`}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder={
              language === 'es'
                ? 'Comparte tus comentarios (opcional)...'
                : 'Share your feedback (optional)...'
            }
            className="w-full min-h-[80px] px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary resize-y"
            maxLength={500}
          />
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs text-muted-foreground">{comment.length}/500</span>
            <div className="flex items-center gap-2">
              <button
                onClick={handleCommentCancel}
                className="px-3 py-1.5 text-xs rounded-lg hover:bg-accent transition-colors text-foreground"
              >
                {language === 'es' ? 'Cancelar' : 'Cancel'}
              </button>
              <button
                onClick={handleCommentSubmit}
                className="px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
              >
                {language === 'es' ? 'Enviar' : 'Submit'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
