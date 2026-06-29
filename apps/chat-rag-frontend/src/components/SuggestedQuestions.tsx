import type { Locale } from "../hooks/useLocale.types";
import { t } from "../i18n/messages";

type SuggestedQuestionsProps = {
  locale: Locale;
  onSelect: (question: string) => void;
};

/** Localized sample community questions shown on the empty welcome state (D5/D10).
 *  Clicking one prefills the question input. */
export function SuggestedQuestions({
  locale,
  onSelect,
}: SuggestedQuestionsProps) {
  const questions = [
    t(locale, "suggestion1"),
    t(locale, "suggestion2"),
    t(locale, "suggestion3"),
  ];

  return (
    <div
      className="suggested-questions"
      data-testid="suggested-questions"
      aria-label={t(locale, "suggestedQuestionsLabel")}
    >
      {questions.map((question) => (
        <button
          key={question}
          type="button"
          className="suggested-question"
          onClick={() => {
            onSelect(question);
          }}
        >
          {question}
        </button>
      ))}
    </div>
  );
}
