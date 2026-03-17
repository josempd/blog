---
title: "Upgrading ArgoCD Across Three Major Versions Without Breaking Every Deployment"
slug: upgrading-argocd-across-three-major-versions
date: 2026-03-17
tags: [Kubernetes, ArgoCD, Infrastructure]
excerpt: ArgoCD was 16 months behind — spanning chart versions 7 through 9 and six ArgoCD releases. Here's how I stepped through three major upgrades on a system that manages every deployment in the cluster.
published: true
---

ArgoCD on our shared cluster was running Helm chart **7.6.8** (ArgoCD v2.12.4). The latest was **9.4.1** (ArgoCD v3.3.0). That's 16 months of drift, three chart major versions, and six ArgoCD releases. ArgoCD manages every infrastructure component and application deployment across dev and production — a failed upgrade doesn't just break ArgoCD, it breaks everything.

Jumping straight to the latest was out of the question. This is how I planned the upgrade path, what broke along the way, and the one silent default change that would have bricked all our ApplicationSets if I hadn't caught it.

## Why not just bump the version?

Each chart major version (7 → 8 → 9) includes breaking changes that compound if you skip them. Chart 8.0.0 shipped ArgoCD 3.0 — the biggest breaking release in the project's history. Chart 9.0.0 restructured all default values. Trying to jump from 7.6.8 to 9.4.1 in one step would have meant debugging failures from three different migration guides simultaneously, with no way to isolate which change caused what.

The safer approach: step through each major boundary, verify everything is healthy, then proceed to the next. Each step is a single `terraform apply` with an `atomic: true` Helm release that auto-rolls back on failure.

## The upgrade path

| Step | Chart | ArgoCD | Risk | Key change |
|---|---|---|---|---|
| 1 | 7.6.8 → 7.9.1 | v2.12.4 → v2.14.11 | Low | Redis downgrade (licensing) |
| 2 | 7.9.1 → 8.0.0 | v2.14.11 → v3.0.0 | **High** | ArgoCD 3.0 — tracking method, metrics, RBAC |
| 3 | 8.0.0 → 8.6.4 | v3.0.0 → v3.1.8 | Low | Minor bumps |
| 4 | 8.6.4 → 9.4.1 | v3.1.8 → v3.3.0 | Medium | All `configs.params` defaults removed |

Steps could be done on separate days. There was no requirement to do all four in one session — in fact, waiting a few hours between steps to confirm stability was part of the plan.

## Step 1: 7.6.8 → 7.9.1

The warm-up. Minor chart bumps with no breaking value changes. The only notable change was a Redis downgrade from 7.4 to 7.2 due to a licensing dispute — transparent to ArgoCD.

One version bump in `shared.auto.tfvars`, one `terraform apply`. All pods running, all apps synced and healthy.

## Step 2: 7.9.1 → 8.0.0 — the big one

Chart 8.0.0 ships ArgoCD 3.0, which changes how applications are tracked. Previous versions used **labels** on Kubernetes resources to track ownership. ArgoCD 3.0 switches to **annotations**. This means every application needs to be in-sync before the upgrade — if an app is out-of-sync during the tracking method transition, ArgoCD might lose track of resources it manages.

I synced all applications before applying, then bumped the chart version. Two things needed attention:

**RBAC for logs.** ArgoCD 3.0 added a new `logs` permission. Without explicitly granting it, users lost the ability to view pod logs from the UI. One line added to the RBAC policy:

```
p, role:readonly, logs, get, */*, allow
```

**Deprecated Prometheus metrics.** ArgoCD 3.0 renamed several metrics (`argocd_app_sync_status`, `argocd_app_health_status`, `argocd_app_created_time`). If you have Grafana dashboards tracking these, they'll go blank after the upgrade. Worth checking before or right after applying.

The upgrade itself went cleanly — Cognito OIDC login worked, most apps showed Synced/Healthy. One didn't.

## The ALB controller drift problem

After Step 2, `pro-aws-load-balancer-controller` showed persistent OutOfSync. Manual syncs didn't fix it — the app would immediately drift back.

The root cause: the AWS Load Balancer Controller auto-generates TLS certificates and injects `caBundle` values into webhook configurations at runtime. Every time ArgoCD synced the app to match the git state, the controller immediately overwrote three resources with its own generated values:

- `Secret/aws-load-balancer-tls` — TLS certificate data
- `MutatingWebhookConfiguration` — caBundle field
- `ValidatingWebhookConfiguration` — caBundle field

This wasn't new behavior — the controller was always doing this. But the tracking method change in ArgoCD 3.0 made it more visible, and the drift detection became more aggressive.

The fix was telling ArgoCD to ignore these specific fields using `ignoreDifferences` on the Application spec:

```yaml
ignoreDifferences:
  - group: admissionregistration.k8s.io
    kind: MutatingWebhookConfiguration
    jsonPointers:
      - /webhooks/0/clientConfig/caBundle
  - group: admissionregistration.k8s.io
    kind: ValidatingWebhookConfiguration
    jsonPointers:
      - /webhooks/0/clientConfig/caBundle
  - kind: Secret
    name: aws-load-balancer-tls
    jsonPointers:
      - /data
```

I added this to both the dev and production ApplicationSet templates. Dev picked it up automatically through auto-sync. Production needed one manual sync to apply the updated Application spec — after that, the drift disappeared.

## Step 3: 8.0.0 → 8.6.4

Back to low risk. Minor bumps within chart 8.x. ArgoCD went from v3.0.0 to v3.1.8. There was a PKCE handling change for OIDC, but it was transparent with our Cognito setup.

Applied cleanly, all apps healthy.

## Step 4: 8.6.4 → 9.4.1 — the silent default

This is the step that would have caused an outage if I hadn't read the migration guide carefully.

Chart 9.0.0 restructured how default values work. Instead of shipping sensible defaults for `configs.params.*`, the chart now ships **empty defaults** for everything. Most of these are fine — the ArgoCD binary has its own internal defaults. But one parameter's behavior changes dramatically when it goes from its previous default to empty:

**`applicationsetcontroller.policy`** previously defaulted to `sync`, which means ApplicationSets can **create, update, and delete** Applications. With an empty string, the policy drops to **create only**. ApplicationSets would stop updating existing apps when their configuration changed, and would stop deleting apps when they were removed from the generator.

In our setup — where ApplicationSets manage all infrastructure components across dev and production — this would have silently broken the entire deployment pipeline. New apps would be created, but changes to existing apps would never propagate, and removed apps would never be cleaned up.

The fix was one line in the values file:

```yaml
configs:
  params:
    applicationsetcontroller.policy: 'sync'
```

With that in place, the upgrade applied cleanly. ArgoCD v3.3.0 running, all 6 ApplicationSets present, 35 of 36 apps Synced/Healthy (the one remaining was the ALB controller on production, pending a manual sync for the `ignoreDifferences` fix from Step 2).

## Lessons learned

### 1. Step through major versions — don't skip

Each major boundary has its own set of breaking changes. Stepping through them one at a time means you can isolate failures to a specific migration guide. If I'd jumped from 7.6.8 to 9.4.1 directly, the `applicationsetcontroller.policy` issue would have been one of a dozen things to debug simultaneously.

### 2. Read the migration guide for default removals

Breaking changes that **add** requirements are easy to catch — your deployment fails with an error. Breaking changes that **remove** defaults are dangerous because nothing fails immediately. The ApplicationSet policy change wouldn't have caused an error at deploy time. It would have silently degraded over the following days as ApplicationSets stopped propagating changes.

### 3. `atomic: true` is a safety net, not a strategy

Having `atomic: true` and `cleanup_on_fail: true` on the Terraform Helm release meant that any failed upgrade would auto-rollback. This was reassuring, but it doesn't help with silent behavior changes that don't cause pod failures. You still need to read the changelogs.

### 4. Controller-managed fields need `ignoreDifferences`

Any Kubernetes controller that writes back to its own resources (webhook caBundles, generated TLS certs, status fields) will cause permanent drift in ArgoCD. The fix is always `ignoreDifferences` with `jsonPointers` targeting the specific fields. This isn't a bug — it's a fundamental tension between GitOps and controllers that manage their own state.

### 5. Sync everything before a tracking method change

ArgoCD 3.0's shift from label-based to annotation-based tracking is a one-way migration. Any app that's out-of-sync during the transition risks losing its resource tracking. Pre-syncing all apps before the upgrade is not optional — it's a prerequisite.

## The full timeline

The four upgrade steps plus the ALB controller hotfix spread across a few days. Each step was a short `terraform plan` → `terraform apply` → verify cycle. Total hands-on time was a few hours, but I deliberately waited between steps to let things run and confirm stability.

If you're facing a similar multi-major ArgoCD upgrade, the approach is the same as any high-stakes infrastructure change: break it into reversible steps, verify at each boundary, and read the changelogs for silent default changes — those are the ones that'll get you.
