import fs from 'node:fs';
import path from 'node:path';

const PATTERNS = {
  hexagonal: {
    description: 'Ports & Adapters — domain isolated from all infrastructure',
    dirs: ['domain', 'ports', 'adapters/infra', 'adapters/http'],
    files: (domain) => [
      {
        rel: `domain/${domain}.ts`,
        content: `// Core domain entity — no infrastructure imports allowed here
export interface ${pascal(domain)} {
  id: string;
  // TODO: add domain fields
}
`,
      },
      {
        rel: `ports/${domain}-repository.port.ts`,
        content: `import type { ${pascal(domain)} } from '../domain/${domain}';

// Inbound port — what the domain exposes to the outside world
export interface ${pascal(domain)}Repository {
  findById(id: string): Promise<${pascal(domain)} | null>;
  save(entity: ${pascal(domain)}): Promise<void>;
  delete(id: string): Promise<void>;
}
`,
      },
      {
        rel: `ports/${domain}-service.port.ts`,
        content: `import type { ${pascal(domain)} } from '../domain/${domain}';

// Outbound port — what the application layer calls
export interface ${pascal(domain)}Service {
  get(id: string): Promise<${pascal(domain)} | null>;
  create(data: Omit<${pascal(domain)}, 'id'>): Promise<${pascal(domain)}>;
}
`,
      },
      {
        rel: `adapters/infra/${domain}-repository.adapter.ts`,
        content: `import type { ${pascal(domain)}Repository } from '../../ports/${domain}-repository.port';
import type { ${pascal(domain)} } from '../../domain/${domain}';

// Infrastructure adapter — implements the port using your DB/ORM
// ONLY this file should import Prisma, TypeORM, SQLAlchemy, etc.
export class ${pascal(domain)}RepositoryAdapter implements ${pascal(domain)}Repository {
  async findById(id: string): Promise<${pascal(domain)} | null> {
    throw new Error('Not implemented');
  }

  async save(entity: ${pascal(domain)}): Promise<void> {
    throw new Error('Not implemented');
  }

  async delete(id: string): Promise<void> {
    throw new Error('Not implemented');
  }
}
`,
      },
      {
        rel: `adapters/http/${domain}.controller.ts`,
        content: `import type { ${pascal(domain)}Service } from '../../ports/${domain}-service.port';

// HTTP adapter — translates HTTP request/response into domain calls
// ONLY this file should import Express, Fastify, etc.
export class ${pascal(domain)}Controller {
  constructor(private readonly service: ${pascal(domain)}Service) {}

  // async getById(req, res) { ... }
  // async create(req, res) { ... }
}
`,
      },
    ],
  },

  'vertical-slice': {
    description: 'Vertical Slices — each feature owns its full stack',
    dirs: [''],
    files: (domain) => [
      {
        rel: `${domain}.types.ts`,
        content: `// Types owned exclusively by the ${domain} feature slice
export interface ${pascal(domain)} {
  id: string;
  // TODO: add fields
}
`,
      },
      {
        rel: `${domain}.service.ts`,
        content: `import type { ${pascal(domain)} } from './${domain}.types';

// All ${domain} business logic lives here — no imports from other feature slices
export class ${pascal(domain)}Service {
  async get(id: string): Promise<${pascal(domain)} | null> {
    throw new Error('Not implemented');
  }

  async create(data: Omit<${pascal(domain)}, 'id'>): Promise<${pascal(domain)}> {
    throw new Error('Not implemented');
  }
}
`,
      },
      {
        rel: `${domain}.repository.ts`,
        content: `import type { ${pascal(domain)} } from './${domain}.types';

// Data access for ${domain} — DB/ORM calls stay here
export class ${pascal(domain)}Repository {
  async findById(id: string): Promise<${pascal(domain)} | null> {
    throw new Error('Not implemented');
  }

  async save(entity: ${pascal(domain)}): Promise<void> {
    throw new Error('Not implemented');
  }
}
`,
      },
      {
        rel: `${domain}.controller.ts`,
        content: `import { ${pascal(domain)}Service } from './${domain}.service';

// HTTP entry point for the ${domain} slice
export class ${pascal(domain)}Controller {
  constructor(private readonly service: ${pascal(domain)}Service) {}
  // TODO: add route handlers
}
`,
      },
      {
        rel: `${domain}.test.ts`,
        content: `import { ${pascal(domain)}Service } from './${domain}.service';

describe('${pascal(domain)}Service', () => {
  it('TODO: add tests', () => {
    expect(true).toBe(true);
  });
});
`,
      },
    ],
  },

  layered: {
    description: 'Layered — presentation / application / domain / infrastructure',
    dirs: ['presentation', 'application', 'domain', 'infrastructure'],
    files: (domain) => [
      {
        rel: `domain/${domain}.entity.ts`,
        content: `// Domain entity — pure business object, no framework or DB types
export class ${pascal(domain)} {
  constructor(
    public readonly id: string,
    // TODO: add fields
  ) {}
}
`,
      },
      {
        rel: `domain/${domain}.repository.interface.ts`,
        content: `import type { ${pascal(domain)} } from './${domain}.entity';

export interface I${pascal(domain)}Repository {
  findById(id: string): Promise<${pascal(domain)} | null>;
  save(entity: ${pascal(domain)}): Promise<void>;
}
`,
      },
      {
        rel: `application/${domain}.use-cases.ts`,
        content: `import type { I${pascal(domain)}Repository } from '../domain/${domain}.repository.interface';
import type { ${pascal(domain)} } from '../domain/${domain}.entity';

// Application layer: orchestrates domain objects, calls domain repos
export class ${pascal(domain)}UseCases {
  constructor(private readonly repo: I${pascal(domain)}Repository) {}

  async get(id: string): Promise<${pascal(domain)} | null> {
    return this.repo.findById(id);
  }
}
`,
      },
      {
        rel: `infrastructure/${domain}.repository.ts`,
        content: `import type { I${pascal(domain)}Repository } from '../domain/${domain}.repository.interface';
import type { ${pascal(domain)} } from '../domain/${domain}.entity';

// Infrastructure layer — ONLY file that imports ORM/DB
export class ${pascal(domain)}Repository implements I${pascal(domain)}Repository {
  async findById(id: string): Promise<${pascal(domain)} | null> {
    throw new Error('Not implemented');
  }

  async save(entity: ${pascal(domain)}): Promise<void> {
    throw new Error('Not implemented');
  }
}
`,
      },
      {
        rel: `presentation/${domain}.controller.ts`,
        content: `import { ${pascal(domain)}UseCases } from '../application/${domain}.use-cases';

// Presentation layer — HTTP/CLI/GraphQL adapter
export class ${pascal(domain)}Controller {
  constructor(private readonly useCases: ${pascal(domain)}UseCases) {}
}
`,
      },
    ],
  },
};

function pascal(str) {
  return str
    .split(/[-_\s]+/)
    .filter(Boolean) // drop empties from leading/trailing/doubled separators
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join('');
}

function scaffold(domain, pattern, outputDir) {
  const def = PATTERNS[pattern];
  if (!def) {
    console.error(`Unknown pattern: ${pattern}. Available: ${Object.keys(PATTERNS).join(', ')}`);
    process.exit(1);
  }

  const baseDir = path.resolve(outputDir, domain);
  console.log(`\nScaffolding "${pattern}" boundary for domain "${domain}"`);
  console.log(`Output: ${baseDir}\n`);

  // Create directories
  for (const dir of def.dirs) {
    const d = dir ? path.join(baseDir, dir) : baseDir;
    fs.mkdirSync(d, { recursive: true });
  }

  // Write files
  for (const { rel, content } of def.files(domain)) {
    const filePath = path.join(baseDir, rel);
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`  created  ${path.relative(process.cwd(), filePath)}`);
  }

  console.log(`\nDone. Pattern: ${def.description}`);
  console.log('Next steps:');
  console.log('  1. Fill in the TODO fields in the domain entity.');
  console.log('  2. Implement the repository adapter with your ORM/DB.');
  console.log('  3. Wire up the controller in your framework router.');
  console.log(
    '  4. Run the Swap Test: could you replace the DB adapter without touching domain files?',
  );
}

// CLI entry point
if (
  process.argv[1] &&
  (process.argv[1] === new URL(import.meta.url).pathname ||
    process.argv[1].endsWith('scaffold-boundary.mjs'))
) {
  const domain = process.argv[2];
  const pattern = process.argv[3] || 'hexagonal';
  const outputDir = process.argv[4] || 'src';

  if (!domain) {
    console.error('Usage: node scaffold-boundary.mjs <domain> [pattern] [output-dir]');
    console.error(`Patterns: ${Object.keys(PATTERNS).join(', ')}`);
    process.exit(1);
  }

  scaffold(domain, pattern, path.resolve(process.cwd(), outputDir));
}
