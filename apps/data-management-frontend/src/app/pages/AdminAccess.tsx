import { KeyRound, Server, Shield } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { getScraperConfigDiagnostic } from '../api/scraper-config';

export function AdminAccess() {
  const { session, user } = useAuth();
  const scraperDiagnostic = getScraperConfigDiagnostic();

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Shield className="w-8 h-8 text-gray-700" />
          Access & Runtime
        </h1>
        <p className="text-gray-500 mt-2">Inspect the local API-key session and runtime connectivity.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <KeyRound className="w-5 h-5 text-blue-600" />
            Active Session
          </CardTitle>
          <CardDescription>Browser authentication now uses a stored backend API key.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-gray-600">
          <p>Principal: {user?.displayName || 'Unavailable'}</p>
          <p>Token preview: {session?.preview || 'Unavailable'}</p>
          <p>Established: {session ? new Date(session.createdAt).toLocaleString() : 'Unavailable'}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="w-5 h-5 text-emerald-600" />
            Runtime Connectivity
          </CardTitle>
          <CardDescription>Current API target and direct Modal/backend configuration status.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-gray-600">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={scraperDiagnostic.issues.length > 0 ? 'destructive' : 'default'}>
              {scraperDiagnostic.issues.length > 0 ? 'Config Issue' : 'Config OK'}
            </Badge>
            <Badge variant="secondary">Auth Mode: Direct API Key Bearer</Badge>
          </div>
          <p>Configured Base URL: {scraperDiagnostic.apiBaseUrl || 'Not set'}</p>
          {scraperDiagnostic.issues.length > 0 && (
            <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-amber-900">
              {scraperDiagnostic.issues.join(' | ')}
            </div>
          )}
          {scraperDiagnostic.warnings.length > 0 && (
            <div className="rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-blue-900">
              {scraperDiagnostic.warnings.join(' | ')}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Deprecated Flows Removed</CardTitle>
          <CardDescription>Legacy invitation, role assignment, and browser session exchange were removed.</CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-gray-600">
          Access is now controlled by backend API keys and direct service configuration only.
        </CardContent>
      </Card>
    </div>
  );
}