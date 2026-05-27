import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function HealthPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Health</h2>
        <p className="text-muted-foreground">Service status and connectivity.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Service Status</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">Health monitoring will be implemented in M27.</p>
        </CardContent>
      </Card>
    </div>
  );
}
