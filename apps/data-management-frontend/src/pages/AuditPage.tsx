import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function AuditPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Audit Log</h2>
        <p className="text-muted-foreground">Event history and document changes.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Events</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">Audit log UI will be implemented in M29.</p>
        </CardContent>
      </Card>
    </div>
  );
}
