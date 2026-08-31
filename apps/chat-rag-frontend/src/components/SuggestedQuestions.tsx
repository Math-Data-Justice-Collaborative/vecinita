import type { Locale } from "../hooks/useLocale.types";
import { t } from "vecinita-frontend-i18n";

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
    t(locale, "chat.suggestion1"),
    t(locale, "chat.suggestion2"),
    t(locale, "chat.suggestion3"),
  ];

  return (
    <div
      className="suggested-questions"
      data-testid="suggested-questions"
      aria-label={t(locale, "chat.suggestedQuestionsLabel")}
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
