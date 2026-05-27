import { NavLink, Outlet } from "react-router-dom";
import { BarChart3, FileText, Heart, ScrollText, Menu } from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { ThemeToggle } from "@/components/ThemeToggle";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { to: "/corpus", label: "Corpus", icon: FileText },
  { to: "/health", label: "Health", icon: Heart },
  { to: "/audit", label: "Audit Log", icon: ScrollText },
] as const;

function NavItems({ onClick }: { onClick?: () => void }) {
  return (
    <nav className="flex flex-col gap-1" data-testid="admin-nav">
      {navItems.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          onClick={onClick}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground",
              isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground",
            )
          }
        >
          <Icon className="h-4 w-4" />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}

function DesktopSidebar() {
  return (
    <aside className="hidden md:flex md:w-60 md:flex-col md:border-r md:bg-card">
      <div className="flex h-14 items-center border-b px-4">
        <h1 className="text-lg font-semibold">Vecinita</h1>
      </div>
      <div className="flex-1 overflow-auto px-3 py-4">
        <NavItems />
      </div>
      <div className="border-t px-3 py-3">
        <ThemeToggle />
      </div>
    </aside>
  );
}

function MobileHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className="flex h-14 items-center gap-4 border-b bg-card px-4 md:hidden">
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" aria-label="Open navigation">
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-60 p-0">
          <SheetHeader className="border-b px-4 py-3">
            <SheetTitle>Vecinita</SheetTitle>
          </SheetHeader>
          <div className="px-3 py-4">
            <NavItems onClick={() => setOpen(false)} />
          </div>
          <Separator />
          <div className="px-3 py-3">
            <ThemeToggle />
          </div>
        </SheetContent>
      </Sheet>
      <h1 className="text-lg font-semibold">Vecinita</h1>
    </header>
  );
}

export function AdminLayout() {
  return (
    <div className="flex min-h-screen">
      <DesktopSidebar />
      <div className="flex flex-1 flex-col">
        <MobileHeader />
        <main className="flex-1 overflow-auto p-4 md:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
