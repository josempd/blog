---
title: "Migrating from ingress-nginx to Traefik with Zero Downtime"
slug: migrating-ingress-nginx-to-traefik
date: 2026-02-20
tags: [Kubernetes, Traefik, Infrastructure]
excerpt: ingress-nginx is retiring in March 2026. Here's how I migrated eight services to Traefik using a parallel deployment strategy — no downtime, no drama.
published: true
---

The ingress-nginx project announced it would stop releasing updates, bugfixes, and security patches in March 2026. That gave me a hard deadline: find a replacement and migrate all production traffic before the clock ran out.

I run about eight services behind a single ingress controller. All of them rely on path rewriting — stripping prefixes, regex replacements, or full path transformations before traffic reaches the pods. Whatever I picked had to handle that without requiring application changes.

This is how I evaluated the options, ran the migration, and what I learned along the way.

## Evaluating the alternatives

I narrowed it down to three candidates:

| | ALB Ingress | Traefik | Gateway API |
|---|---|---|---|
| Path rewriting | No native support — dealbreaker | Yes (StripPrefix, ReplacePathRegex) | Yes (URLRewrite filter) |
| Architecture change | Requires switching from NLB to ALB | None — same NLB-based pattern | Major — Gateway manages its own load balancer |
| Migration risk | High — application changes needed | Low — annotation-only changes | High — new resource types, new mental model |
| Future-proof | Limited | Good (also supports Gateway API) | Best |

**Traefik won** because it required zero architecture changes. The traffic flow stayed the same:

```
Internet -> CDN -> NLB -> Ingress Controller -> Pods
```

The only thing that changed was swapping the ingress controller and translating annotations. No new load balancers, no application code changes, no CDN reconfiguration during the migration itself.

Gateway API was tempting for its long-term potential, but the migration complexity wasn't justified under a deadline. Traefik supports Gateway API as a provider, so I can adopt it incrementally later.

## The strategy: parallel deployment

The key decision was deploying Traefik **alongside** nginx rather than replacing it in place. This gave me:

- **A rollback path** — if Traefik misbehaved, I could point the CDN back to the nginx NLB instantly
- **Independent testing** — I could curl Traefik's NLB directly with Host headers to verify each service before switching any real traffic
- **No coordination pressure** — infrastructure and application changes could land at different times

The migration had five phases:

1. Deploy Traefik in parallel (new NLB, new DaemonSet, same cluster)
2. Migrate Ingress resources (swap annotations, create middleware CRDs)
3. Switch CDN origin on staging
4. Switch CDN origin on production
5. Decommission nginx

## Translating annotations

This was the bulk of the actual work. Every nginx annotation needed a Traefik equivalent, and some required creating Middleware custom resources.

### Simple path stripping

Most of my services used the common nginx pattern of stripping a prefix:

```yaml
# nginx
nginx.ingress.kubernetes.io/rewrite-target: /$1
# with path: /servicename/(.*)

# Traefik — StripPrefix middleware
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: strip-servicename
spec:
  stripPrefix:
    prefixes:
      - /servicename
```

### Regex path rewriting

A few services needed more complex transformations — mapping one path structure to another:

```yaml
# nginx
# path: /prefix/(capture)(.*)
# rewrite-target: /$1$2

# Traefik — ReplacePathRegex middleware
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: rewrite-prefix
spec:
  replacePathRegex:
    regex: "^/prefix/(.*)"
    replacement: "/$1"
```

### Body size limits and timeouts

```yaml
# nginx
nginx.ingress.kubernetes.io/proxy-body-size: "50m"
nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
nginx.ingress.kubernetes.io/proxy-send-timeout: "300"

# Traefik — Buffering middleware
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: large-body
spec:
  buffering:
    maxRequestBodyBytes: 52428800
```

For timeouts, Traefik uses a `ServersTransport` resource with `responseHeaderTimeout` and `dialTimeout` fields.

### Backend HTTPS and host rewriting

One service needed HTTPS to the backend pod with a custom Host header — the trickiest translation:

```yaml
# nginx
nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
nginx.ingress.kubernetes.io/upstream-vhost: "api.example.com"

# Traefik — annotation + Headers middleware
traefik.ingress.kubernetes.io/service.serversscheme: https

apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: custom-host
spec:
  headers:
    customRequestHeaders:
      Host: "api.example.com"
```

### Chaining middleware

Traefik lets you chain multiple middleware on a single Ingress using an annotation:

```yaml
traefik.ingress.kubernetes.io/router.middlewares: >-
  namespace-strip-prefix@kubernetescrd,
  namespace-large-body@kubernetescrd
```

This was cleaner than nginx's annotation-per-concern approach. One service that previously needed six separate Ingress resources in nginx was consolidated down to a single Ingress with chained middleware.

## The migration, phase by phase

### Phase 0: Deploy Traefik in parallel

I added Traefik to my Terraform config as a Helm release, deploying it as a DaemonSet (matching my nginx setup). This created a new NLB alongside the existing one.

At this point both controllers were running, but only nginx was receiving traffic through the CDN.

### Phase 1: Migrate Ingress resources

I updated the Ingress manifests for all eight services:

- Changed `ingressClassName` from `nginx` to `traefik`
- Replaced nginx annotations with Traefik annotations
- Created Middleware CRDs for path rewriting, body size limits, and host headers

The services fell into three categories:

- **Simple strip** (4 services): Single path with prefix stripping. StripPrefix middleware.
- **Regex rewrite** (2 services): Multi-path with capture groups. ReplacePathRegex middleware.
- **Complex** (2 services): Combination of path rewriting, HTTPS backends, custom headers. Multiple chained middleware.

I verified each service by curling the Traefik NLB directly:

```bash
curl -H "Host: app.example.com" https://<traefik-nlb>/servicename/healthcheck
```

### Phase 2-3: Switch CDN origins

Once all services returned 200 through the Traefik NLB, I updated the CDN origin in Terraform — first on staging, then production after verifying no 5xx spikes.

This was a single `terraform apply` per environment. The CDN handled the transition transparently.

### Phase 4: Decommission nginx

After confirming stable traffic through Traefik for 24 hours, I removed the nginx Helm release from Terraform and applied. Clean removal on both clusters.

## Lessons learned

### 1. Deploy infrastructure before merging app changes

I merged the Ingress annotation changes (nginx to Traefik) to `main` before Traefik was deployed on production. This caused every app in ArgoCD to show as out-of-sync, because the manifests referenced an IngressClass that didn't exist yet.

**Fix:** Deploy the prerequisite (Traefik) on all clusters before merging manifest changes.

### 2. Traefik must not use privileged ports

I initially configured Traefik to listen on ports 80 and 443 internally. Since Traefik runs as non-root, this caused crash loops. The fix was to let Traefik use its default internal ports (8000/8443) and only set `exposedPort` on the Service.

### 3. Helm uninstall can timeout on NLB deletion

When Terraform destroyed the nginx Helm release, the NLB deprovisioning was slow enough to cause a timeout. The Helm release was already marked as deleted, but pods and services were orphaned. I cleaned them up manually with `kubectl delete`.

**Tip:** If your Helm timeout is shorter than your cloud provider's LB deletion time, expect orphaned resources.

### 4. Middleware "not found" errors are transient

After creating Traefik Middleware CRDs, I saw errors like `middleware "namespace-strip@kubernetescrd" does not exist`. These resolved on their own within a few minutes as Traefik's CRD provider discovered the new resources. Don't panic and start debugging — wait a moment first.

## Was it worth it?

The entire migration — from first `terraform plan` to nginx decommission — took a weekend. The parallel deployment strategy meant I could test everything thoroughly before switching real traffic, and the CDN origin swap made the cutover instant and reversible.

If you're facing the same ingress-nginx deadline, the approach is straightforward: deploy in parallel, translate annotations, verify independently, switch at the CDN, clean up. No downtime required.
