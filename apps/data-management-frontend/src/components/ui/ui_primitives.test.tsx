import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";

describe("UI primitives coverage", () => {
  beforeEach(() => {
    Element.prototype.scrollIntoView = vi.fn();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders open select content with grouped items", () => {
    render(
      <Select open onOpenChange={() => undefined}>
        <SelectTrigger aria-label="Language">
          <SelectValue placeholder="Pick language" />
        </SelectTrigger>
        <SelectContent position="popper">
          <SelectGroup>
            <SelectLabel>Languages</SelectLabel>
            <SelectItem value="en">English</SelectItem>
            <SelectItem value="es">Spanish</SelectItem>
            <SelectSeparator />
          </SelectGroup>
        </SelectContent>
      </Select>,
    );

    expect(screen.getByText("English")).toBeInTheDocument();
    expect(screen.getByText("Spanish")).toBeInTheDocument();
  });

  it("renders item-aligned select content", () => {
    render(
      <Select open onOpenChange={() => undefined}>
        <SelectTrigger aria-label="Aligned">
          <SelectValue placeholder="Pick" />
        </SelectTrigger>
        <SelectContent position="item-aligned">
          <SelectItem value="a">Alpha</SelectItem>
        </SelectContent>
      </Select>,
    );

    expect(screen.getByText("Alpha")).toBeInTheDocument();
  });

  it("renders tabs with both panels mounted via values", () => {
    render(
      <>
        <Tabs defaultValue="one">
          <TabsList>
            <TabsTrigger value="one">One</TabsTrigger>
          </TabsList>
          <TabsContent value="one">Panel one</TabsContent>
        </Tabs>
        <Tabs defaultValue="two">
          <TabsList>
            <TabsTrigger value="two">Two</TabsTrigger>
          </TabsList>
          <TabsContent value="two">Panel two</TabsContent>
        </Tabs>
      </>,
    );

    expect(screen.getByText("Panel one")).toBeInTheDocument();
    expect(screen.getByText("Panel two")).toBeInTheDocument();
  });

  it("renders separator", () => {
    render(
      <div>
        <span>Above</span>
        <Separator />
        <span>Below</span>
      </div>,
    );
    expect(screen.getByText("Above")).toBeInTheDocument();
    expect(screen.getByText("Below")).toBeInTheDocument();
  });

  it("renders vertical non-decorative separator", () => {
    render(
      <Separator
        orientation="vertical"
        decorative={false}
        aria-orientation="vertical"
      />,
    );
    expect(screen.getByRole("separator")).toBeInTheDocument();
  });
});
