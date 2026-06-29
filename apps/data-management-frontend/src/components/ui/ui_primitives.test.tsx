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
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SheetFooter, SheetHeader } from "@/components/ui/sheet";

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

  it("renders all card subcomponents", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Card title</CardTitle>
          <CardDescription>Card description</CardDescription>
        </CardHeader>
        <CardContent>Card content</CardContent>
        <CardFooter>Card footer</CardFooter>
      </Card>,
    );

    expect(screen.getByText("Card title")).toBeInTheDocument();
    expect(screen.getByText("Card description")).toBeInTheDocument();
    expect(screen.getByText("Card content")).toBeInTheDocument();
    expect(screen.getByText("Card footer")).toBeInTheDocument();
  });

  it("renders a table with footer and caption", () => {
    render(
      <Table>
        <TableCaption>Table caption</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>Head</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>Body cell</TableCell>
          </TableRow>
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell>Footer cell</TableCell>
          </TableRow>
        </TableFooter>
      </Table>,
    );

    expect(screen.getByText("Table caption")).toBeInTheDocument();
    expect(screen.getByText("Footer cell")).toBeInTheDocument();
  });

  it("renders sheet header and footer layout containers", () => {
    render(
      <div>
        <SheetHeader>
          <span>Sheet header</span>
        </SheetHeader>
        <SheetFooter>
          <span>Sheet footer</span>
        </SheetFooter>
      </div>,
    );

    expect(screen.getByText("Sheet header")).toBeInTheDocument();
    expect(screen.getByText("Sheet footer")).toBeInTheDocument();
  });
});
