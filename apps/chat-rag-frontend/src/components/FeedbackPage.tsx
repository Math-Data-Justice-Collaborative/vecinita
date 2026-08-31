import { useState, type FormEvent } from "react";

import { submitFeedback, type FeedbackCategory } from "../api/feedback";
import type { Locale } from "../hooks/useLocale.types";
import { t, type StringMessageKey } from "vecinita-frontend-i18n";

const CATEGORIES: readonly {
  value: FeedbackCategory;
  labelKey: StringMessageKey;
}[] = [
  { value: "bug", labelKey: "chat.feedbackCategory_bug" },
  { value: "wrong_answer", labelKey: "chat.feedbackCategory_wrong_answer" },
  { value: "suggestion", labelKey: "chat.feedbackCategory_suggestion" },
  { value: "other", labelKey: "chat.feedbackCategory_other" },
];

type FeedbackPageProps = {
  locale: Locale;
  onNavigateHome: () => void;
};

export function FeedbackPage({ locale, onNavigateHome }: FeedbackPageProps) {
  const [category, setCategory] = useState<FeedbackCategory>("suggestion");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) {
      setError(t(locale, "chat.feedbackMessageRequired"));
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await submitFeedback({
        category,
        message: trimmed,
        locale,
      });
      setSuccess(true);
      setMessage("");
    } catch {
      setError(t(locale, "chat.feedbackSubmitFailed"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section
      className="feedback-page"
      data-testid="feedback-page"
      aria-label={t(locale, "chat.feedbackTitle")}
    >
      <button
        type="button"
        className="feedback-back"
        onClick={onNavigateHome}
        data-testid="feedback-back"
      >
        {t(locale, "chat.backToChat")}
      </button>
      <h2>{t(locale, "chat.feedbackTitle")}</h2>
      <p className="feedback-intro" data-testid="feedback-intro">
        {t(locale, "chat.feedbackIntro")}
      </p>
      <aside
        className="feedback-privacy"
        data-testid="feedback-privacy-notice"
        role="note"
      >
        {t(locale, "chat.feedbackPrivacyNote")}
      </aside>
      {success ? (
        <p
          className="feedback-success"
          data-testid="feedback-success"
          role="status"
        >
          {t(locale, "chat.feedbackSuccess")}
        </p>
      ) : null}
      <form
        className="feedback-form"
        data-testid="feedback-form"
        onSubmit={(event) => void onSubmit(event)}
      >
        <label htmlFor="feedback-category">
          {t(locale, "chat.feedbackCategoryLabel")}
        </label>
        <select
          id="feedback-category"
          data-testid="feedback-category"
          value={category}
          onChange={(event) => {
            setCategory(event.target.value as FeedbackCategory);
          }}
        >
          {CATEGORIES.map(({ value, labelKey }) => (
            <option key={value} value={value}>
              {t(locale, labelKey)}
            </option>
          ))}
        </select>
        <label htmlFor="feedback-message">
          {t(locale, "chat.feedbackMessageLabel")}
        </label>
        <textarea
          id="feedback-message"
          data-testid="feedback-message"
          value={message}
          required
          maxLength={4000}
          rows={6}
          onChange={(event) => {
            setMessage(event.target.value);
          }}
        />
        {error ? (
          <p
            className="feedback-error"
            data-testid="feedback-error"
            role="alert"
          >
            {error}
          </p>
        ) : null}
        <button
          type="submit"
          data-testid="feedback-submit"
          disabled={submitting}
        >
          {submitting
            ? t(locale, "chat.feedbackSubmitting")
            : t(locale, "chat.feedbackSubmit")}
        </button>
      </form>
    </section>
  );
}
