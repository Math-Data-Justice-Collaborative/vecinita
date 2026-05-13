import { Outlet, Link, useLocation } from "react-router";
import { Database, FileText, Plus, Activity, Settings, Tag, Cog, Shield } from "lucide-react";
import { Button } from "./ui/button";
import { useAuth } from "../auth/AuthContext";
import { useLocale } from "../i18n/LocaleContext";

export function Layout() {
  const location = useLocation();
  const { user, session, signOut } = useAuth();
  const { locale, setLocale, t } = useLocale();

  const isActive = (path: string) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Database className="w-6 h-6 text-blue-600" />
            {t('layout.title')}
          </h1>
          <p className="text-sm text-gray-500 mt-1">{t('layout.subtitle')}</p>
          <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-3">
            <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{t('layout.language')}</p>
            <div className="mt-2 flex gap-2">
              <Button
                type="button"
                size="sm"
                variant={locale === 'en' ? 'default' : 'outline'}
                onClick={() => setLocale('en')}
              >
                EN
              </Button>
              <Button
                type="button"
                size="sm"
                variant={locale === 'es' ? 'default' : 'outline'}
                onClick={() => setLocale('es')}
              >
                ES
              </Button>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            <li>
              <Link to="/">
                <Button
                  variant={isActive('/') && location.pathname === '/' ? "default" : "ghost"}
                  className="w-full justify-start"
                >
                  <Activity className="w-4 h-4 mr-2" />
                  {t('layout.dashboard')}
                </Button>
              </Link>
            </li>
            <li>
              <Link to="/corpus">
                <Button
                  variant={isActive('/corpus') ? "default" : "ghost"}
                  className="w-full justify-start"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  {t('layout.corpus')}
                </Button>
              </Link>
            </li>
            <li>
              <Link to="/tags">
                <Button
                  variant={isActive('/tags') ? "default" : "ghost"}
                  className="w-full justify-start"
                >
                  <Tag className="w-4 h-4 mr-2" />
                  {t('layout.tags')}
                </Button>
              </Link>
            </li>
            <li>
              <Link to="/add">
                <Button
                  variant={isActive('/add') ? "default" : "ghost"}
                  className="w-full justify-start"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  {t('layout.add')}
                </Button>
              </Link>
            </li>
            <li>
              <Link to="/scrape-jobs">
                <Button
                  variant={isActive('/scrape-jobs') ? "default" : "ghost"}
                  className="w-full justify-start"
                >
                  <Settings className="w-4 h-4 mr-2" />
                  {t('layout.jobs')}
                </Button>
              </Link>
            </li>
            <li>
              <Link to="/settings">
                <Button
                  variant={isActive('/settings') ? "default" : "ghost"}
                  className="w-full justify-start"
                >
                  <Cog className="w-4 h-4 mr-2" />
                  {t('layout.configuration')}
                </Button>
              </Link>
            </li>
            <li>
              <Link to="/admin-access">
                <Button
                  variant={isActive('/admin-access') ? "default" : "ghost"}
                  className="w-full justify-start"
                >
                  <Shield className="w-4 h-4 mr-2" />
                  {t('layout.access')}
                </Button>
              </Link>
            </li>
          </ul>
        </nav>

        <div className="p-4 border-t border-gray-200 text-xs text-gray-500">
          <p className="text-gray-700 font-medium">{user?.displayName || 'Authenticated session'}</p>
          <p className="mt-1">Token: {session?.preview || 'Unavailable'}</p>
          <Button
            className="mt-3 w-full"
            size="sm"
            variant="outline"
            onClick={() => {
              signOut().catch((error) => {
                console.error('Sign out failed', error);
              });
            }}
          >
            {t('layout.signOut')}
          </Button>
          <p className="mt-4">{t('layout.runtimeStatus')}</p>
          <div className="flex items-center gap-2 mt-2">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span>Runtime data mode</span>
          </div>
          <p className="mt-2 text-xs">{t('layout.runtimeHint')}</p>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}