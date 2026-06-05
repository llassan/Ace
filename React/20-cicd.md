# CI/CD for Frontend Engineers

Shipping code is a first-class engineering discipline. Senior frontend engineers are expected to own the full path from a merged PR to production — including the pipeline that validates it, the deployment strategy that makes it safe, and the observability that tells you when something breaks. This guide covers everything an interviewer expects a lead-level React engineer to know about CI/CD, release safety, and delivery infrastructure.

---

## CI vs CD vs Continuous Deployment

### Q: What is the difference between CI, CD, and Continuous Deployment?

These three terms sit on a maturity ladder. Most teams conflate them, but interviewers want precision.

**Continuous Integration (CI):** Every developer merges to a shared branch frequently (ideally daily). An automated pipeline runs on every push — install, typecheck, lint, test, build. The goal is to detect integration failures early, while the context is fresh.

**Continuous Delivery (CD):** The pipeline produces a release artifact that is _ready_ to deploy at any time. Deploying to production still requires a human trigger or approval gate. The promise: the main branch is always shippable.

**Continuous Deployment:** Every commit that passes CI/CD is automatically pushed to production with no human gate. Requires high test confidence, feature flags, and observability. Most teams land somewhere between Delivery and Deployment.

The maturity ladder:
1. Manual builds and deploys
2. Automated builds triggered by commits
3. Automated tests gate merges
4. Automated deploys to staging
5. Automated deploys to production (Continuous Deployment)

> 💡 Senior insight: "We do CD" often means Continuous Delivery, not Deployment. Ask which one during system design. The answer determines how much automation and flag infrastructure you actually need.

⚠️ Gotcha: Many teams say they do CI but their pipelines run only on main, not on every PR branch. That is not CI — it is just automated builds.

---

## The Frontend CI Pipeline

### Q: What gates should a frontend PR pipeline include, and in what order?

Order for fastest feedback (fail fast, parallelize where safe):

```yaml
# Conceptual order — see full GitHub Actions example below
1. install          # deterministic with lockfile + cache
2. typecheck        # ts --noEmit, usually fast
3. lint             # ESLint, Prettier check
4. unit/component   # Vitest / Jest — parallelizable per shard
5. build            # next build / vite build — needed by downstream gates
6. bundle-size      # bundlewatch / size-limit — runs after build
7. a11y check       # axe-core / Playwright + axe (see module 11)
8. e2e tests        # Playwright / Cypress — slowest, run after build (see module 09)
9. preview deploy   # Vercel/Netlify preview URL — notified on PR
```

**Why this order matters:**
- Typecheck and lint are cheap and catch the most common mistakes. Put them before tests.
- E2E tests are the slowest gate — run them only after the build artifact exists so you are testing what users actually see.
- Preview deploy last, because it depends on a successful build and gives reviewers a real URL.

**Parallelism strategy:**
- Unit tests, typecheck, and lint can run in parallel jobs once `install` completes.
- Bundle-size check and e2e must be sequential after `build`.
- Use job dependencies (`needs:`) to express the DAG explicitly.

> 💡 Senior insight: Bundle-size budget checks are often skipped because "it's a pain to set up." That is exactly when bundles silently bloat. Add `size-limit` or `bundlewatch` to CI before the first launch, not after the first incident.

**Follow-ups they'll ask:**
- How do you handle flaky e2e tests in CI? (retry with `--retries`, quarantine flaky tests, track flakiness rate — see module 09)
- How do you cache node_modules correctly? (answer below in GitHub Actions section)
- What does a bundle budget failure look like? (non-zero exit code from `size-limit`, blocks merge)

---

## GitHub Actions In Depth

### Q: Walk me through a production-quality GitHub Actions workflow for a React app.

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:  # manual trigger from UI
  schedule:
    - cron: '0 6 * * 1'  # weekly full regression on Monday 6am UTC

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true   # cancel stale PR runs when new commit pushed

env:
  NODE_VERSION: '20'
  PNPM_VERSION: '9'

jobs:
  install:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: ${{ env.PNPM_VERSION }}

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'  # caches ~/.pnpm-store

      - name: Install dependencies
        run: pnpm install --frozen-lockfile  # fail if lockfile is stale

      - name: Cache node_modules
        uses: actions/cache@v4
        with:
          path: node_modules
          key: nm-${{ runner.os }}-${{ hashFiles('pnpm-lock.yaml') }}

  typecheck:
    needs: install
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: '${{ env.PNPM_VERSION }}' }
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm tsc --noEmit

  lint:
    needs: install
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: '${{ env.PNPM_VERSION }}' }
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint
      - run: pnpm prettier --check .

  unit-tests:
    needs: install
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shard: [1, 2, 3]   # parallel shards
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: '${{ env.PNPM_VERSION }}' }
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm vitest run --shard=${{ matrix.shard }}/3 --coverage
      - uses: actions/upload-artifact@v4
        with:
          name: coverage-shard-${{ matrix.shard }}
          path: coverage/

  build:
    needs: [typecheck, lint, unit-tests]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: '${{ env.PNPM_VERSION }}' }
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm build
        env:
          VITE_API_URL: ${{ vars.API_URL_STAGING }}  # repo variable, not secret
      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/

  bundle-size:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/
      - uses: pnpm/action-setup@v4
        with: { version: '${{ env.PNPM_VERSION }}' }
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm size-limit  # fails build if budget exceeded

  e2e:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: '${{ env.PNPM_VERSION }}' }
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/
      - name: Install Playwright browsers
        run: pnpm playwright install --with-deps chromium
      - run: pnpm playwright test --retries=2
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/

  deploy-preview:
    needs: [bundle-size, e2e]
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    permissions:
      pull-requests: write  # to post PR comment with URL
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/
      # Example: Vercel CLI deploy
      - run: npx vercel deploy --prebuilt --token=${{ secrets.VERCEL_TOKEN }}
```

**Key concepts in this workflow:**

**Triggers:**
- `push` to main runs the full pipeline and deploy.
- `pull_request` runs CI + preview deploy but not production deploy.
- `workflow_dispatch` allows humans to re-run from the UI.
- `schedule` runs a full regression suite on a timer.

**Concurrency groups:** Cancel stale PR runs when a new commit is pushed. Saves runner minutes and avoids confusing results.

**Matrix builds:** Shard unit tests across 3 parallel runners. For large suites, this reduces total CI time from 10 minutes to 3-4.

**Caching strategy:**
- `actions/setup-node` with `cache: 'pnpm'` caches the pnpm store (`~/.pnpm-store`).
- An explicit `actions/cache` step with a hash key caches `node_modules` for reuse across jobs in the same workflow. Cache miss = fresh install. Cache hit = milliseconds.
- Key: `hashFiles('pnpm-lock.yaml')` — lockfile change busts the cache automatically.

**OIDC instead of long-lived secrets:** For AWS/GCP deployments, use OIDC federation so the runner gets short-lived credentials. No `AWS_SECRET_ACCESS_KEY` in secrets.

**Reusable workflows / composite actions:** Extract the install+cache block into a composite action to avoid repeating it across every job.

> 💡 Senior insight: `--frozen-lockfile` (pnpm) / `--ci` (npm) / `--immutable` (yarn) is non-negotiable in CI. It fails the build if anyone forgot to commit their lockfile update, which is the right behavior.

⚠️ Gotcha: `actions/cache` is best-effort — a cache miss does not fail the build. Never rely on the cache for correctness, only for speed.

**Follow-ups they'll ask:**
- What are required status checks? (Branch protection rules that must pass before merge — configured in GitHub repo settings, not YAML)
- How do you handle secrets vs config vars? (Secrets are encrypted, masked in logs, for credentials; vars are plaintext, for non-sensitive config like API URLs)
- How would you handle a monorepo with 10 packages? (Path filters + `dorny/paths-filter` to run only affected jobs)

---

## Other CI Systems

### Q: When would an enterprise choose Jenkins, GitLab CI, or CircleCI over GitHub Actions?

| System | When it fits | Key difference |
|---|---|---|
| **Jenkins** | Self-hosted compliance requirements, existing enterprise investment, complex conditional logic | Groovy pipelines, massive plugin ecosystem, requires its own infra to maintain |
| **GitLab CI** | Teams using GitLab for source control, strong built-in registry/security scanning, EU data residency | YAML-native, built-in container registry, runners are GitLab-managed or self-hosted |
| **CircleCI** | Historically fast orbs ecosystem, Docker-layer caching is first class | Resource classes, `parallelism` key for sharding, orbs = reusable config packages |
| **GitHub Actions** | GitHub source, modern greenfield projects, massive marketplace | Native OIDC, matrix builds, concurrency groups |

For frontend-focused interviews, GitHub Actions is the default. Know Jenkins exists for enterprises (many have it in legacy stacks) and GitLab CI if the job involves a GitLab-native shop.

---

## Docker for Frontend

### Q: When do you containerize a frontend app, and how do you write a multi-stage Dockerfile?

**When to containerize:**
- SSR / Node.js server (Next.js, Remix in server mode) — the server process needs a container.
- Consistent preview environments across teams.
- Kubernetes deployments where every workload is a container.

**When not to:** A pure SPA or statically generated site is better served from a CDN (S3+CloudFront, Vercel, Cloudflare Pages). Containers add operational overhead for no gain when there is no server process.

**Multi-stage Dockerfile for a React SPA (served via nginx):**

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app

# Copy lockfile first for layer caching
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile

COPY . .
RUN pnpm build   # outputs to /app/dist

# Stage 2: Serve
FROM nginx:1.27-alpine AS runtime
# Remove default nginx page
RUN rm -rf /usr/share/nginx/html/*

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

```nginx
# nginx.conf — SPA fallback so React Router works
server {
  listen 80;
  root /usr/share/nginx/html;
  index index.html;

  # Serve hashed assets with long cache
  location ~* \.(js|css|png|jpg|svg|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
  }

  # SPA fallback — all routes serve index.html
  location / {
    try_files $uri $uri/ /index.html;
  }
}
```

**.dockerignore (critical for image size):**

```
node_modules
.git
*.md
.env*
dist
coverage
playwright-report
```

> 💡 Senior insight: Multi-stage builds are the most important Docker optimization for frontend. The `builder` stage includes devDependencies, TypeScript compiler, all source files. The `runtime` stage contains only static files + nginx — often 10-30MB vs 800MB.

⚠️ Gotcha: If you COPY the whole repo before `pnpm install`, every source file change invalidates the package install layer. Always COPY lockfile + package.json first, install, then COPY source.

---

## Deployment Models

### Q: What are the main ways to deploy a React app, and what are the tradeoffs?

**Static hosting / CDN:**
- S3 + CloudFront, Vercel, Netlify, Cloudflare Pages.
- Best for SPA and SSG. Near-zero ops overhead. Global edge delivery.
- Limitations: No server-side runtime, client-side data fetching only, SEO challenges for non-SSG content.

**SSR / Serverless / Edge:**
- Next.js on Vercel (serverless functions), Remix on Cloudflare Workers (edge), Node server in a container.
- See module 08 for rendering strategies. The deployment model follows the rendering model.

**Preview / branch deployments:**
- Every PR gets its own URL (Vercel, Netlify, Cloudflare all do this natively).
- Critical for design review, QA, and stakeholder sign-off without touching production.

**Atomic deploys:**
- The new version replaces the old version instantly as a single operation — no partial state where some files are old and some are new.
- Vercel and Netlify guarantee this. S3 sync does NOT — you need CloudFront invalidation + careful ordering.

**Immutable assets + cache busting:**
- Vite and webpack emit hashed filenames: `main.Xk3jPqZ9.js`. CDN caches these forever (`Cache-Control: public, max-age=31536000, immutable`).
- The `index.html` entry point must NOT be cached (or short TTL), because it references the new hashed filenames.

⚠️ Gotcha: The most common caching incident in frontend deploys — `index.html` is cached at the CDN for 24 hours. Users get the old HTML pointing to old hashed assets. Those old assets may be gone. Result: blank screen. Fix: `Cache-Control: no-cache` on `index.html`, long cache on everything else.

**Rollback:**
- Vercel/Netlify: one-click rollback to any previous deployment via the dashboard or CLI.
- S3+CloudFront: re-upload previous build artifact, invalidate cache.
- Docker/K8s: `kubectl rollout undo deployment/frontend`.

---

## Release Strategies

### Q: What is the difference between blue-green, canary, and rolling deployments?

**Blue-green:**
- Two identical environments. Blue is live. Deploy to green, validate, flip traffic. Green becomes live. Blue becomes standby.
- Instant rollback: flip back to blue.
- Cost: requires double the infrastructure.
- Common for: containerized apps, Lambda function aliases, Kubernetes with two deployments + service switch.

**Canary:**
- Route a small percentage of traffic (1%, 5%, 10%) to the new version. Monitor error rates and latency. Gradually increase until 100%.
- Risk is limited to canary users. Requires traffic splitting infrastructure (ALB weighted target groups, Nginx upstream weights, Cloudflare traffic rules, LaunchDarkly).
- For frontend on Vercel/Cloudflare: use feature flags instead of infra-level traffic splitting.

**Rolling:**
- Replace instances one at a time (or in batches). Both versions run simultaneously during the rollout.
- Lower cost than blue-green. Risk: incompatible API changes between old and new version if they coexist.

**Feature-flag-based progressive delivery:**
- Deploy to production but keep the feature off by default. Enable for internal users, then beta users, then percentage rollout.
- Decouples deploy from release completely (see Feature Flags section).

> 💡 Senior insight: For most frontend teams, feature flags are more practical than infra-level canary. You get the same safety with less infrastructure complexity.

---

## Feature Flags

### Q: How do feature flags work and why are they essential for continuous delivery?

Feature flags decouple **deploy** (code goes to production) from **release** (users see the feature). This is the key insight for safe continuous deployment.

**Use cases:**
- Progressive rollout: enable for 1% of users, then 10%, then 100%.
- Kill switch: instantly disable a broken feature without a deploy.
- A/B testing: 50% see variant A, 50% see variant B, measure conversion.
- Beta program: enable only for specific user IDs or company attributes.
- Trunk-based development: merge incomplete features behind a flag, no long-lived branches.

**Tools:**
- **LaunchDarkly:** Enterprise standard. SDKs for every language, real-time streaming, targeting rules, A/B, integrations.
- **Unleash:** Open source, self-hostable, strong feature toggle pattern library.
- **Flagsmith:** Open source or SaaS, simpler API than LaunchDarkly.
- **Homegrown:** A JSON config in S3 + CloudFront. Sufficient for simple on/off flags. Breaks down quickly when you need targeting or gradual rollouts.

**Client vs server evaluation:**
- **Client-side:** SDK runs in the browser. Flags evaluated after page load. Risk of flag flicker (content flash as flag loads). Better for UI experiments.
- **Server-side (SSR):** Flags evaluated on the server before rendering. No flicker. Better for feature access control and security-sensitive gates.

**Flags + SSR gotcha:** If you evaluate a flag server-side and the client re-evaluates it after hydration, you get a hydration mismatch if the flag value differs. Solution: pass server-evaluated flag values as props or embedded JSON to the client.

**Flag lifecycle (critical for seniors to mention):**
1. Create with a ticket reference.
2. Develop behind the flag.
3. Gradual rollout.
4. Full rollout confirmed.
5. Remove the flag from code — this is the step teams skip.

⚠️ Gotcha: Flag debt is real. A codebase with 200 stale flags is a maintenance nightmare. Treat flag removal as a required ticket in the rollout process. LaunchDarkly has stale flag detection. Set a calendar reminder if your tooling does not.

---

## Environment and Config Management

### Q: How do you manage environment-specific configuration safely in a React app?

**Build-time vs runtime config:**
- **Build-time (VITE_* / NEXT_PUBLIC_*):** Embedded into the JS bundle at build. Changing requires a rebuild. Safe for: API base URLs, feature flag API keys, analytics IDs.
- **Runtime:** Fetched from a server or injected by the container at startup. More flexible but adds latency. Common pattern: a `/config.json` endpoint or environment-specific nginx config that serves a `window.__ENV__` block.

**12-factor for frontend:**
- One build artifact, promoted across environments. Environment-specific values come from the environment, not from separate builds.
- With build-time config this is a tension — you end up with one build per environment. Solution: use runtime config for values that differ per environment; use build-time config only for truly static values.

**.env conventions:**
```
.env                    # defaults, committed, no secrets
.env.local              # local overrides, gitignored
.env.development        # dev-specific, committed, no secrets
.env.production         # prod, committed, no secrets — values are not secret themselves
.env.*.local            # gitignored, for local secrets
```

⚠️ Gotcha: Never put real secrets (API secret keys, OAuth client secrets, database passwords) in the frontend bundle. They are readable by anyone who opens DevTools. Frontend config should contain only public keys (LaunchDarkly client-side ID, Sentry DSN, Stripe publishable key). See module 10 for secrets handling in depth.

**Validation at startup:**
```typescript
// src/config.ts
const requiredVars = ['VITE_API_URL', 'VITE_SENTRY_DSN'] as const;
for (const key of requiredVars) {
  if (!import.meta.env[key]) {
    throw new Error(`Missing required env var: ${key}`);
  }
}
```

Fail loudly at startup rather than silently making requests to undefined URLs.

---

## Quality Gates and DX

### Q: What quality gates belong in CI and what are their traps?

**Code coverage thresholds:**
```json
// vitest.config.ts coverage thresholds
{
  "coverage": {
    "thresholds": {
      "lines": 80,
      "branches": 75,
      "functions": 80
    }
  }
}
```
Traps: 80% coverage does not mean 80% of your important paths are tested. Gaming coverage with trivial tests is easy. Coverage is a floor, not a goal. See module 09 for testing philosophy.

**Required reviews + CODEOWNERS:**
```
# .github/CODEOWNERS
# Any change to CI config requires DevOps review
.github/workflows/   @org/devops-team
# Design system changes require design-systems team
src/components/ds/   @org/design-systems
```

**Semantic-release / Changesets (see module 17):**
- `semantic-release`: Analyzes commit messages (Conventional Commits), bumps version, generates changelog, publishes — fully automated.
- `changesets`: Explicit changeset files per PR, batch release. Better for monorepos and libraries where authors describe their changes explicitly.

**Lighthouse CI:**
```yaml
# .lighthouserc.js
module.exports = {
  assert: {
    assertions: {
      'categories:performance': ['error', { minScore: 0.9 }],
      'categories:accessibility': ['error', { minScore: 1.0 }],
      'first-contentful-paint': ['error', { maxNumericValue: 2000 }],
    },
  },
};
```

**Flaky test handling:**
- Retry in CI (`--retries=2` for Playwright, `jest --testSequencer` with retry wrappers).
- Track flakiness rate. A test that fails 10% of runs is a failed test that is hard to notice.
- Quarantine confirmed-flaky tests to a separate job that does not block merge, fix them within a sprint.

---

## Observability Post-Deploy

### Q: How do you know a deploy succeeded and production is healthy?

**Source map upload:**
```bash
# In CI after deploy step
npx @sentry/cli releases new $VERSION
npx @sentry/cli releases files $VERSION upload-sourcemaps ./dist
npx @sentry/cli releases finalize $VERSION
npx @sentry/cli releases deploys $VERSION new -e production
```
Without this, Sentry stack traces show minified filenames and line 1. With it, you get exact file + line in your source.

**Release tracking:** Mark the deploy in your observability tool (Sentry release, Datadog deployment tracking, New Relic change tracking). This lets you correlate error spikes with specific deploys.

**RUM (Real User Monitoring):** Sentry Performance, Datadog RUM, or web-vitals library reporting to your backend. Tracks Core Web Vitals (LCP, CLS, INP) per release, per region, per device class.

**Smoke tests post-deploy:**
- Automated synthetic checks (Playwright against production, Checkly, Datadog Synthetics) that run immediately after deploy.
- Test the critical path: homepage loads, login works, primary user action completes.

**Automated rollback on error spike:**
- Define an error rate SLO (e.g., < 0.1% JS errors per pageview).
- If the error rate spikes above threshold within 10 minutes of deploy, trigger automated rollback (Vercel CLI, `kubectl rollout undo`, flip blue-green).
- This is the end-state of a mature CD system: deploy without human babysitting, rollback without human action.

> 💡 Senior insight: Observability is part of the delivery pipeline, not an afterthought. Source map upload, release tracking, and smoke tests should be steps in the CI/CD YAML — not manual processes.

---

## Senior Scenario: React Monorepo CI/CD

### Q: Design a CI/CD pipeline for a React monorepo with three apps (marketing site, dashboard, admin).

**Repository structure assumption:**
```
apps/
  marketing/     # Next.js, SSG
  dashboard/     # Vite SPA
  admin/         # Vite SPA
packages/
  ui/            # shared component library
  utils/         # shared utilities
  config/        # ESLint, TypeScript, Tailwind configs
```

**Step 1: Change detection.** Use `dorny/paths-filter` or Turborepo's `--affected` to determine which apps and packages changed. A PR that only touches `apps/marketing` should not run `apps/admin` e2e tests.

**Step 2: Shared pipeline stages.** Install, typecheck, lint, and unit tests run for every change. These are fast and catch cross-cutting regressions.

**Step 3: Per-app build and test.** Build only affected apps. Run e2e for affected apps. Deploy preview for each affected app independently.

```yaml
jobs:
  detect-changes:
    outputs:
      marketing: ${{ steps.filter.outputs.marketing }}
      dashboard: ${{ steps.filter.outputs.dashboard }}
      admin: ${{ steps.filter.outputs.admin }}
    steps:
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            marketing:
              - 'apps/marketing/**'
              - 'packages/**'
            dashboard:
              - 'apps/dashboard/**'
              - 'packages/**'
            admin:
              - 'apps/admin/**'
              - 'packages/**'

  build-marketing:
    needs: detect-changes
    if: needs.detect-changes.outputs.marketing == 'true'
    # ... build + deploy marketing

  build-dashboard:
    needs: detect-changes
    if: needs.detect-changes.outputs.dashboard == 'true'
    # ... build + deploy dashboard
```

**Step 4: Package publishing.** When `packages/ui` changes and tests pass, use Changesets to version and publish to the internal npm registry (GitHub Packages or Verdaccio).

**Step 5: Deployment routing.**
- `marketing` deploys to Cloudflare Pages (SSG, global CDN).
- `dashboard` and `admin` deploy to Vercel (SPA with preview URLs).

**Step 6: Environment promotion.** PRs deploy to preview. Main deploys to staging. Tagged releases deploy to production (with `workflow_dispatch` manual approval gate for production).

**Turborepo as the build orchestrator:**
```json
// turbo.json
{
  "pipeline": {
    "build": { "dependsOn": ["^build"], "outputs": ["dist/**"] },
    "test": { "dependsOn": ["^build"] },
    "lint": {}
  }
}
```
Turborepo caches task outputs by input hash and runs tasks in dependency order. A second run on unchanged code is near-instant.

> 💡 Senior insight: The key decision in a monorepo CI/CD is "how do we avoid running everything on every PR?" The answer is always some form of affected-package detection — either framework-native (Turborepo, Nx) or explicit path filtering. Without it, the pipeline does not scale.

**Follow-ups they'll ask:**
- How do you handle shared package versioning? (Changesets for explicit control, or automated semver from commits)
- How do you prevent a UI package change from breaking an app? (Type-checking at the package boundary, consumer integration tests in CI)
- How do you manage secrets across three apps? (GitHub Environments with environment-specific secrets, OIDC per deploy target)

---

## ⚡ Rapid-Fire

- **What is a lockfile and why must CI use it?** A lockfile pins exact dependency versions. `--frozen-lockfile` / `--ci` fails the build if the lockfile is out of sync with `package.json`, ensuring reproducible installs.
- **What is OIDC in GitHub Actions?** OpenID Connect lets runners assume cloud IAM roles using a short-lived JWT instead of storing long-lived secret keys.
- **What does `cancel-in-progress: true` do?** Cancels the running workflow for the same branch when a new commit is pushed. Saves runner minutes on rapid-fire commits.
- **What is a composite action?** A reusable GitHub Actions unit defined in a repo (action.yml) that bundles multiple steps. Lighter weight than a reusable workflow, no separate runner.
- **What is a required status check?** A CI job that must pass before a PR can be merged, enforced by branch protection rules in GitHub repository settings.
- **Difference between `vars` and `secrets` in GitHub Actions?** `vars` are plaintext config (API URLs, feature flag keys). `secrets` are encrypted and masked in logs (tokens, passwords).
- **What is an atomic deploy?** The transition from old to new version happens as a single swap, never leaving the system in a partial state where some files are old and some are new.
- **Why hash filenames?** Immutable cache forever. Changing content generates a new hash, so the CDN serves the new file automatically without cache invalidation.
- **What is a canary deploy?** Routing a small percentage of traffic to the new version to validate before full rollout.
- **What is flag debt?** Accumulation of stale feature flags that are permanently enabled or disabled but never removed from the codebase.
- **What is Turborepo?** A build system for JavaScript/TypeScript monorepos that caches task outputs by content hash and runs tasks in dependency order, skipping unchanged work.
- **What does `size-limit` do?** Analyzes the build output and fails CI if the JavaScript bundle exceeds a defined budget in bytes.
- **What is a changeset?** A markdown file in a PR that describes the changes and their semver impact (patch/minor/major), consumed by the Changesets tool to automate versioning and changelogs.
- **What is a Sentry release?** A named version in Sentry associated with a source map upload and deploy event, used to scope errors to specific deploys and compare error rates across releases.

---

## 🚩 Red Flags

- **No lockfile or not using `--frozen-lockfile` in CI.** Non-reproducible builds. A `node_modules` that works on CI may differ from local, and different CI runs may produce different results.
- **Secrets in environment variables baked into the frontend bundle.** Visible to anyone in DevTools. This is a security incident waiting to happen.
- **No cache busting strategy — deploying to S3 with fixed filenames.** Users receive cached stale assets after a deploy. Debugging this in production is painful.
- **`index.html` cached at the CDN with a long TTL.** Classic blank-screen incident. Old HTML references assets that no longer exist at those paths.
- **E2E tests with no retry strategy.** Flaky tests that randomly block deployments train engineers to re-run CI without investigating, which erodes trust in the entire pipeline.
- **No preview deploys on PRs.** Reviewers merge code they have not seen in a browser. Design bugs and layout regressions reach production.
- **Skipping CI with `--no-verify` or pushing directly to main.** The pipeline exists to enforce quality. Bypassing it for "just a small change" is how production incidents happen.
- **Feature flags never cleaned up.** Dead code paths, impossible-to-understand conditional logic, runtime overhead from evaluating hundreds of stale flags.
- **No source map upload to error tracker.** Production errors report minified stack traces. Debugging takes hours instead of minutes.
- **Running the full pipeline on every commit regardless of what changed.** A monorepo CI that takes 40 minutes because it builds all 10 apps when only a README changed. Engineers start merging without waiting for CI.
- **No rollback plan.** "We will just deploy a fix" is not a rollback plan. Know your rollback path before you deploy.
- **Coverage thresholds at 100%.** Teams spend time writing trivial tests to hit the number, and write zero meaningful tests. Coverage gates should be a floor (75-80%), not a target.
