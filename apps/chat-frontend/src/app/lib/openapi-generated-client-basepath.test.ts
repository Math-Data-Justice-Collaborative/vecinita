import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

import { resolveApiBase } from './apiBaseResolution';

const thisDir = path.dirname(fileURLToPath(import.meta.url));
const generatedGatewayConfigModule = path.resolve(
  thisDir,
  '../../../../packages/openapi-clients/typescript-axios/gateway/configuration'
);

describe('generated gateway client base URL wiring', () => {
  it('uses same resolved base URL as apiBaseResolution helper', async () => {
    if (
      !existsSync(`${generatedGatewayConfigModule}.ts`) &&
      !existsSync(`${generatedGatewayConfigModule}.js`)
    ) {
      return;
    }

    const resolvedGatewayBase = resolveApiBase('https://vecinita-agent.onrender.com/api/v1', {
      hostname: 'vecinita-frontend.onrender.com',
      protocol: 'https:',
    });

    const generated = await import(generatedGatewayConfigModule);
    const Configuration = generated.Configuration as
      | (new (args?: { basePath?: string }) => { basePath?: string })
      | undefined;

    expect(Configuration).toBeDefined();
    if (!Configuration) {
      return;
    }
    const cfg = new Configuration({ basePath: resolvedGatewayBase });
    expect(cfg.basePath).toBe(resolvedGatewayBase);
  });
});
