import { NavLink, Outlet } from "react-router-dom";
import {
  BarChart3,
  FileText,
  Heart,
  ListChecks,
  ScrollText,
  Menu,
} from "lucide-react";
import { useState } from "react";
import { LanguageToggle, useLocale } from "vecinita-frontend-ui";

import { useAuth } from "@/auth/authContext";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAdminT } from "@/hooks/useAdminT";
import { useMediaQuery } from "@/hooks/useMediaQuery";

function UserMenu() {
  const tr = useAdminT();
  const { user, signOut } = useAuth();

  if (!user?.email) {
    return null;
  }

  return (
    <div className="flex flex-col gap-2" data-testid="admin-user-menu">
      <p className="text-xs text-muted-foreground">
        {tr("admin.auth.currentUser", { email: user.email })}
      </p>
      <Button
        type="button"
        variant="outline"
        size="sm"
        data-testid="admin-sign-out"
        onClick={() => {
          void signOut();
        }}
      >
        {tr("admin.auth.signOut")}
      </Button>
    </div>
  );
}

function ChromeControls() {
  const { locale, setLocale } = useLocale();

  return (
    <div
      className="flex items-center gap-2"
      data-testid="admin-chrome-controls"
    >
      <LanguageToggle locale={locale} onChange={setLocale} />
      <ThemeToggle />
    </div>
  );
}

function NavItems({ onClick }: { onClick?: () => void }) {
  const tr = useAdminT();

  const navItems = [
    {
      to: "/dashboard",
      label: tr("admin.nav.dashboard"),
      icon: BarChart3,
    },
    { to: "/corpus", label: tr("admin.nav.corpus"), icon: FileText },
    { to: "/jobs", label: tr("admin.nav.jobs"), icon: ListChecks },
    { to: "/health", label: tr("admin.nav.health"), icon: Heart },
    {
      to: "/audit",
      label: tr("admin.nav.auditLog"),
      icon: ScrollText,
    },
  ] as const;

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
              isActive
                ? "bg-accent text-accent-foreground"
                : "text-muted-foreground",
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

function DesktopSidebar({ showChrome }: { showChrome: boolean }) {
  const tr = useAdminT();

  return (
    <aside className="hidden md:flex md:h-screen md:w-60 md:flex-col md:border-r md:bg-card">
      <div className="flex h-14 items-center border-b px-4">
        <h1 className="text-lg font-semibold">{tr("admin.appTitle")}</h1>
      </div>
      <div className="flex-1 overflow-auto px-3 py-4">
        <NavItems />
      </div>
      {showChrome ? (
        <div className="space-y-3 border-t px-3 py-3">
          <UserMenu />
          <ChromeControls />
        </div>
      ) : null}
    </aside>
  );
}

function MobileHeader({ showChrome }: { showChrome: boolean }) {
  const [open, setOpen] = useState(false);
  const tr = useAdminT();

  return (
    <header className="flex h-14 items-center gap-4 border-b bg-card px-4 md:hidden">
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            aria-label={tr("admin.nav.openMobile")}
          >
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-60 p-0">
          <SheetHeader className="border-b px-4 py-3">
            <SheetTitle>{tr("admin.appTitle")}</SheetTitle>
            <SheetDescription className="sr-only">
              {tr("admin.nav.mobileMenuDescription")}
            </SheetDescription>
          </SheetHeader>
          <div className="px-3 py-4">
            <NavItems
              onClick={() => {
                setOpen(false);
              }}
            />
          </div>
        </SheetContent>
      </Sheet>
      <h1 className="text-lg font-semibold">{tr("admin.appTitle")}</h1>
      {showChrome ? (
        <div className="ml-auto">
          <ChromeControls />
        </div>
      ) : null}
    </header>
  );
}

export function AdminLayout() {
  const isDesktop = useMediaQuery("(min-width: 768px)");

  return (
    <div className="flex min-h-screen">
      <DesktopSidebar showChrome={isDesktop} />
      <div className="flex flex-1 flex-col">
        <MobileHeader showChrome={!isDesktop} />
        <main className="flex-1 overflow-auto p-4 md:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
