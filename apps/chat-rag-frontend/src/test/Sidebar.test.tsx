import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Sidebar } from "../components/Sidebar";
import type { TagFacet } from "../api/browse";
import type { Conversation } from "../hooks/useConversationStore";

const housing: TagFacet = {
  slug: "housing",
  label: "Housing",
  language: "en",
  document_count: 2,
};

const conversation: Conversation = {
  id: "c1",
  createdAt: Date.now(),
  messages: [{ id: "m1", role: "user", content: "Where is the food pantry?" }],
};

function renderSidebar(overrides: Partial<Parameters<typeof Sidebar>[0]> = {}) {
  const props = {
    open: true,
    locale: "en" as const,
    theme: "dark" as const,
    onCorpus: false,
    newChatDisabled: false,
    tags: [housing],
    selectedTags: [] as string[],
    previousChats: [conversation],
    onNavigate: vi.fn(),
    onNewChat: vi.fn(),
    onToggleTag: vi.fn(),
    onSelectConversation: vi.fn(),
    onDeleteConversation: vi.fn(),
    onClearAll: vi.fn(),
    onSetLocale: vi.fn(),
    onToggleTheme: vi.fn(),
    ...overrides,
  };
  render(<Sidebar {...props} />);
  return props;
}

describe("Sidebar", () => {
  afterEach(cleanup);

  it("renders new chat, nav, topic tags, language and theme controls", () => {
    renderSidebar();
    expect(
      screen.getByRole("button", { name: /new chat/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^chat$/i })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /^corpus$/i }),
    ).toBeInTheDocument();
    expect(screen.getByTestId("tag-filter-chips")).toBeInTheDocument();
    expect(screen.getByTestId("language-toggle")).toBeInTheDocument();
    expect(screen.getByTestId("theme-toggle")).toBeInTheDocument();
  });

  it("invokes navigation handlers", () => {
    const props = renderSidebar();
    fireEvent.click(screen.getByRole("button", { name: /^corpus$/i }));
    expect(props.onNavigate).toHaveBeenCalledWith("/corpus");
    fireEvent.click(screen.getByRole("button", { name: /^chat$/i }));
    expect(props.onNavigate).toHaveBeenCalledWith("/");
  });

  it("toggles a topic tag", () => {
    const props = renderSidebar();
    fireEvent.click(screen.getByRole("button", { name: "Housing" }));
    expect(props.onToggleTag).toHaveBeenCalledWith("housing");
  });

  it("starts a new chat and toggles the theme", () => {
    const props = renderSidebar();
    fireEvent.click(screen.getByRole("button", { name: /new chat/i }));
    expect(props.onNewChat).toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("theme-toggle"));
    expect(props.onToggleTheme).toHaveBeenCalled();
  });

  it("omits the topics section when there are no tags", () => {
    renderSidebar({ tags: [] });
    expect(screen.queryByTestId("tag-filter-chips")).not.toBeInTheDocument();
  });

  it("lists previous chats through the collapsible control", () => {
    renderSidebar();
    fireEvent.click(screen.getByRole("button", { name: /previous chats/i }));
    const list = screen.getByTestId("previous-chats-list");
    expect(
      within(list).getByText(/where is the food pantry/i),
    ).toBeInTheDocument();
  });
});
