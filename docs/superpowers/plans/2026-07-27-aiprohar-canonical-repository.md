# Aiprohar Canonical Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Перенести публичный сайт `aiprohar.ru` в единственный канонический репозиторий `prohar2f-pixel.github.io`, сохранив уникальные старые страницы и не затронув работающие проекты в `my-first-project`.

**Architecture:** `prohar2f-pixel.github.io/main` становится единственным источником GitHub Pages и custom domain. Из `my-first-project` переносится только явно разрешённый набор публичных HTML-страниц и ресурсов; уникальное прежнее содержимое сохраняется в `legacy/`, а монорепозиторий продолжает обслуживать ботов и приложения без публикации Pages.

**Tech Stack:** статический HTML/CSS/JavaScript, GitHub Pages, Git, DNS Beget, HTTPS GitHub Pages.

## Global Constraints

- Не удалять и не архивировать `my-first-project`: его боты и приложения используются.
- Не переносить в публичный Pages-репозиторий серверный код, `.env`, кэши, журналы инструментов или внутренние документы.
- Не переписывать Git-историю и не удалять репозитории.
- До изменений создать резервные теги и записать исходные хэши обеих веток.
- Custom domain `aiprohar.ru` должен существовать только в `prohar2f-pixel.github.io`.
- Публичный сайт после миграции изменяется только в `prohar2f-pixel.github.io/main`.
- Изменения `my-first-project` выполняются только после успешной проверки опубликованного сайта.

---

### Task 1: Зафиксировать исходное состояние и точки отката

**Files:**
- Inspect: all tracked files in `C:\tmp\aiprohar-site`
- Inspect: all tracked files in `C:\tmp\aiprohar-root`
- Create remotely: tags `backup/before-aiprohar-split-2026-07-27` in both repositories

**Interfaces:**
- Consumes: remote branches `prohar2f-pixel/my-first-project:main` and `prohar2f-pixel/prohar2f-pixel.github.io:main`.
- Produces: two immutable rollback references and a clean, current starting point for migration.

- [ ] **Step 1: Fetch both repositories without modifying worktrees**

```powershell
git -C C:\tmp\aiprohar-site fetch --prune origin
git -C C:\tmp\aiprohar-root fetch --prune origin
```

Expected: both commands complete successfully and update only remote references.

- [ ] **Step 2: Verify branch identity and worktree scope**

```powershell
git -C C:\tmp\aiprohar-site status --short --branch
git -C C:\tmp\aiprohar-site rev-parse origin/main
git -C C:\tmp\aiprohar-root status --short --branch
git -C C:\tmp\aiprohar-root rev-parse origin/main
```

Expected: the root repository is clean; the monorepo contains only the two already-reviewed documentation commits beyond `origin/main`. Stop if either remote branch advanced unexpectedly and inspect its new commits before continuing.

- [ ] **Step 3: Create local rollback tags at remote production commits**

```powershell
git -C C:\tmp\aiprohar-site tag backup/before-aiprohar-split-2026-07-27 origin/main
git -C C:\tmp\aiprohar-root tag backup/before-aiprohar-split-2026-07-27 origin/main
```

Expected: `git show-ref --tags` in each repository lists the tag at its recorded `origin/main` hash.

- [ ] **Step 4: Push only the rollback tags**

```powershell
git -C C:\tmp\aiprohar-site push origin refs/tags/backup/before-aiprohar-split-2026-07-27
git -C C:\tmp\aiprohar-root push origin refs/tags/backup/before-aiprohar-split-2026-07-27
```

Expected: both tags appear on GitHub; no branch is changed.

### Task 2: Build the canonical Pages repository

**Files:**
- Modify: `C:\tmp\aiprohar-root\index.html`
- Preserve: `C:\tmp\aiprohar-root\CNAME`
- Create: `C:\tmp\aiprohar-root\assets\5.webp`
- Create: `C:\tmp\aiprohar-root\assets\6.webp`
- Create: `C:\tmp\aiprohar-root\assets\7.webp`
- Create: `C:\tmp\aiprohar-root\assets\8.webp`
- Create: `C:\tmp\aiprohar-root\assets\9.webp`
- Create: `C:\tmp\aiprohar-root\assets\10.webp`
- Create: `C:\tmp\aiprohar-root\assets\11.webp`
- Create: `C:\tmp\aiprohar-root\assets\favicon.svg`
- Create: `C:\tmp\aiprohar-root\assets\logo.webp`
- Create: `C:\tmp\aiprohar-root\assets\photo.jpg`
- Create: `C:\tmp\aiprohar-root\assets\photo_cta.webp`
- Create: `C:\tmp\aiprohar-root\assets\photo_cta_mobile.webp`
- Create: `C:\tmp\aiprohar-root\assets\tzbot_hero.webp`
- Create: `C:\tmp\aiprohar-root\assets\fluid.js`
- Create: `C:\tmp\aiprohar-root\assets\site.css`
- Create: `C:\tmp\aiprohar-root\assets\site.js`
- Create: `C:\tmp\aiprohar-root\aeo\index.html`
- Create: `C:\tmp\aiprohar-root\offer.html`
- Create: `C:\tmp\aiprohar-root\privacy.html`
- Create: `C:\tmp\aiprohar-root\confidentiality.html`
- Modify: `C:\tmp\aiprohar-root\robots.txt`
- Modify: `C:\tmp\aiprohar-root\sitemap.xml`
- Preserve or update from source after comparison: `C:\tmp\aiprohar-root\yandex_7253be1cd5e2aa75.html`
- Update from source: `C:\tmp\aiprohar-root\yandex_7612ab21819be0ce.html`
- Create: `C:\tmp\aiprohar-root\README.md`

**Interfaces:**
- Consumes: only the allowlisted public files from `C:\tmp\aiprohar-site`.
- Produces: a self-contained static site that can be served from `/` without `/my-first-project/`.

- [ ] **Step 1: Create a failing local-resource audit**

Create `C:\tmp\aiprohar-root\tools\check-local-links.ps1` with this content:

```powershell
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$required = @(
  'index.html', 'aeo/index.html', 'offer.html', 'privacy.html',
  'confidentiality.html', 'robots.txt', 'sitemap.xml', 'CNAME'
)
$missing = [System.Collections.Generic.List[string]]::new()

foreach ($relative in $required) {
  if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $relative))) {
    $missing.Add("required: $relative")
  }
}

$htmlFiles = Get-ChildItem -LiteralPath $repoRoot -Filter '*.html' -File -Recurse |
  Where-Object { $_.FullName -notlike "$repoRoot\.git\*" }

foreach ($file in $htmlFiles) {
  $html = Get-Content -Raw -LiteralPath $file.FullName
  $matches = [regex]::Matches($html, '(?:href|src)=["'']([^"'']+)["'']')
  foreach ($match in $matches) {
    $url = $match.Groups[1].Value
    if ($url -match '^(#|https?:|mailto:|tel:|data:|javascript:)') { continue }
    $pathPart = ($url -split '[?#]', 2)[0]
    if ([string]::IsNullOrWhiteSpace($pathPart)) { continue }
    if ($pathPart.StartsWith('/')) {
      $target = Join-Path $repoRoot $pathPart.TrimStart('/')
    } else {
      $target = Join-Path $file.DirectoryName $pathPart
    }
    if ($pathPart.EndsWith('/')) { $target = Join-Path $target 'index.html' }
    if (-not (Test-Path -LiteralPath $target)) {
      $relativeFile = [IO.Path]::GetRelativePath($repoRoot, $file.FullName)
      $missing.Add("$relativeFile -> $url")
    }
  }
}

if ($missing.Count -gt 0) {
  $missing | Sort-Object -Unique | ForEach-Object { Write-Host "MISSING: $_" }
  exit 1
}
Write-Host 'Local link audit passed.'
```

- [ ] **Step 2: Run the audit before migration and verify it fails**

```powershell
powershell -ExecutionPolicy Bypass -File C:\tmp\aiprohar-root\tools\check-local-links.ps1
```

Expected: FAIL because the current root page redirects and required production assets/pages are not present.

- [ ] **Step 3: Copy the exact public allowlist**

Use filesystem copies only for the paths listed in this task. Do not recursively copy the monorepo root. Copy the current `index.html`, the listed assets, `aeo/index.html`, legal pages, `robots.txt`, `sitemap.xml`, and Yandex verification files from `C:\tmp\aiprohar-site` to the corresponding paths in `C:\tmp\aiprohar-root`.

- [ ] **Step 4: Fix the known broken AEO logo reference**

In `C:\tmp\aiprohar-root\aeo\index.html`, replace both the missing `/assets/logo.png` reference and any equivalent relative `assets/logo.png` reference with `/assets/logo.webp`. Do not change other AEO content.

- [ ] **Step 5: Preserve the custom domain**

Verify `C:\tmp\aiprohar-root\CNAME` contains exactly:

```text
aiprohar.ru
```

- [ ] **Step 6: Add canonical repository documentation**

Create `README.md` stating that this repository is the only source for `https://aiprohar.ru`, deployment comes from `main` through GitHub Pages, secrets and server projects are prohibited, and bots/apps belong in `my-first-project`.

- [ ] **Step 7: Run the local-resource audit**

```powershell
powershell -ExecutionPolicy Bypass -File C:\tmp\aiprohar-root\tools\check-local-links.ps1
```

Expected: PASS for the current production pages. Any missing file must be reviewed and added to the explicit allowlist before copying.

- [ ] **Step 8: Serve and inspect the site locally**

```powershell
python -m http.server 4173 --directory C:\tmp\aiprohar-root
```

Expected: `/`, `/aeo/`, `/offer.html`, `/privacy.html`, and `/confidentiality.html` return `200`; the home page renders with all images and no redirect to `/my-first-project/`.

- [ ] **Step 9: Commit the canonical site migration**

```powershell
git -C C:\tmp\aiprohar-root add -- index.html CNAME assets aeo/index.html offer.html privacy.html confidentiality.html robots.txt sitemap.xml yandex_7253be1cd5e2aa75.html yandex_7612ab21819be0ce.html README.md tools/check-local-links.ps1
git -C C:\tmp\aiprohar-root commit -m "feat: make aiprohar root site canonical"
```

Expected: only the listed public-site files are committed.

### Task 3: Preserve legacy public pages without duplicate sources

**Files:**
- Create: `C:\tmp\aiprohar-root\legacy\kp-realty.html`
- Create: `C:\tmp\aiprohar-root\legacy\statera-preview.html`
- Create: `C:\tmp\aiprohar-root\legacy\tutor-4klass.html`
- Create: `C:\tmp\aiprohar-root\legacy\tales\bk_1.html`
- Create: `C:\tmp\aiprohar-root\legacy\tales\bk_3.html`
- Create: `C:\tmp\aiprohar-root\legacy\tales\bk_6.html`
- Modify into compatibility redirects: root copies of the six original paths

**Interfaces:**
- Consumes: unique legacy HTML present at backup tag `backup/before-aiprohar-split-2026-07-27`.
- Produces: one preserved content copy under `legacy/` plus stable redirects from previous URLs.

- [ ] **Step 1: Copy each unique page to its legacy path**

Copy the six files from the backup-tag worktree content into the paths listed above, preserving bytes and relative `tales/` structure.

- [ ] **Step 2: Replace old root paths with explicit redirects**

For each old URL, replace the file with this UTF-8 template, substituting the exact target path and page title:

```html
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url=/legacy/TARGET.html">
  <link rel="canonical" href="https://aiprohar.ru/legacy/TARGET.html">
  <title>Страница перемещена</title>
</head>
<body>
  <p>Страница перемещена: <a href="/legacy/TARGET.html">открыть</a>.</p>
</body>
</html>
```

Use these exact mappings: `kp-realty.html -> /legacy/kp-realty.html`, `statera-preview.html -> /legacy/statera-preview.html`, `tutor-4klass.html -> /legacy/tutor-4klass.html`, and each `tales/bk_N.html -> /legacy/tales/bk_N.html` for `N = 1, 3, 6`.

- [ ] **Step 3: Verify preservation and compatibility**

Run the local-resource audit and request all twelve legacy and compatibility URLs from the local server.

Expected: each legacy content page returns `200`; each old path returns `200` and points only to its matching legacy path.

- [ ] **Step 4: Commit legacy preservation**

```powershell
git -C C:\tmp\aiprohar-root add -- legacy kp-realty.html statera-preview.html tutor-4klass.html tales
git -C C:\tmp\aiprohar-root commit -m "chore: preserve legacy public pages"
```

### Task 4: Publish and verify the canonical repository

**Files:**
- No additional source files expected.
- GitHub setting: Pages source `main` / repository root.

**Interfaces:**
- Consumes: reviewed commits from Tasks 2 and 3.
- Produces: working production site on the apex domain before the monorepo is cleaned.

- [ ] **Step 1: Rebase safely on the latest remote main**

```powershell
git -C C:\tmp\aiprohar-root fetch origin
git -C C:\tmp\aiprohar-root rebase origin/main
```

Expected: fast, conflict-free rebase. Stop and inspect if the remote changed.

- [ ] **Step 2: Run final pre-push checks**

```powershell
powershell -ExecutionPolicy Bypass -File C:\tmp\aiprohar-root\tools\check-local-links.ps1
git -C C:\tmp\aiprohar-root diff --check origin/main...HEAD
git -C C:\tmp\aiprohar-root status --short
```

Expected: link audit passes; diff check is clean; no untracked secret or environment files are present.

- [ ] **Step 3: Push the canonical repository**

```powershell
git -C C:\tmp\aiprohar-root push origin main
```

- [ ] **Step 4: Confirm GitHub Pages configuration**

In repository settings, confirm Pages deploys from `main` and the repository root, custom domain is `aiprohar.ru`, and HTTPS enforcement is enabled when GitHub permits it.

- [ ] **Step 5: Poll the public site until the new commit is live**

Check `https://aiprohar.ru/`, `/aeo/`, the legal pages, Yandex verification files, and selected legacy pages. Confirm the root HTML contains the production title and does not contain `url=/my-first-project/`.

Expected: all required URLs return `200`, assets load, and the certificate is valid.

### Task 5: Correct the www DNS record

**Files:**
- Beget DNS zone: modify only host `www`.

**Interfaces:**
- Consumes: working apex deployment from Task 4.
- Produces: resolvable `www.aiprohar.ru` without a CNAME loop.

- [ ] **Step 1: Record the current DNS evidence**

```powershell
Resolve-DnsName www.aiprohar.ru -Type CNAME -Server ns1.beget.ru
```

Expected before fix: `www.aiprohar.ru CNAME www.aiprohar.ru`.

- [ ] **Step 2: Replace only the www CNAME in Beget**

Delete the self-referencing `www` record and create:

```text
Host: www
Type: CNAME
Value: prohar2f-pixel.github.io.
```

Do not modify the six NS records or the four apex A records.

- [ ] **Step 3: Verify authoritative and public DNS**

```powershell
Resolve-DnsName www.aiprohar.ru -Type CNAME -Server ns1.beget.ru
Resolve-DnsName www.aiprohar.ru -Type CNAME -Server 8.8.8.8
Resolve-DnsName www.aiprohar.ru -Type CNAME -Server 1.1.1.1
```

Expected: the authoritative server changes first; public resolvers converge after TTL expiry.

- [ ] **Step 4: Verify www HTTPS behavior**

```powershell
curl.exe -I -L --max-time 20 https://www.aiprohar.ru/
```

Expected: successful TLS and a GitHub Pages response or redirect to `https://aiprohar.ru/`, with no DNS timeout.

### Task 6: Remove the duplicate website role from my-first-project

**Files:**
- Modify: `C:\tmp\aiprohar-site\README.md`
- Delete only after comparison: `index.html`, `aeo/index.html`, `offer.html`, `privacy.html`, `confidentiality.html`, `robots.txt`, `sitemap.xml`, `yandex_7253be1cd5e2aa75.html`, `yandex_7612ab21819be0ce.html`, and the exact migrated assets listed in Task 2
- Preserve: every bot/app directory and every root deployment file used by those projects
- GitHub setting: disable Pages for `my-first-project`

**Interfaces:**
- Consumes: verified production deployment and backup tag.
- Produces: active monorepo with no competing public-site source.

- [ ] **Step 1: Build an exact deletion candidate list**

Compare these exact candidates byte-for-byte against the published canonical repository: `index.html`, `aeo/index.html`, `offer.html`, `privacy.html`, `confidentiality.html`, `robots.txt`, `sitemap.xml`, both listed Yandex files, and `assets/{5.webp,6.webp,7.webp,8.webp,9.webp,10.webp,11.webp,favicon.svg,logo.webp,photo.jpg,photo_cta.webp,photo_cta_mobile.webp,tzbot_hero.webp,fluid.js,site.css,site.js}`. Search `Procfile`, `requirements.txt`, `runtime.txt`, every bot/app README and deployment configuration for each candidate path. Remove a candidate from the deletion set if it is referenced outside the public-site files.

- [ ] **Step 2: Add the source-of-truth notice**

At the beginning of `README.md`, state that `aiprohar.ru` is maintained only in `https://github.com/prohar2f-pixel/prohar2f-pixel.github.io`; this repository contains bots and applications and must not be configured as a GitHub Pages source.

- [ ] **Step 3: Remove only verified duplicate site files**

Use `git rm` with explicit literal paths from the reviewed candidate list. Do not use recursive globs. Remove only `aeo/index.html`; retain the other plans, proposals, specifications and project files under `aeo/`.

- [ ] **Step 4: Verify active projects are unchanged**

```powershell
git -C C:\tmp\aiprohar-site diff --stat
git -C C:\tmp\aiprohar-site diff --name-status
```

Expected: changes are limited to the README and explicitly approved duplicate public-site files. No bot or application source path appears.

- [ ] **Step 5: Commit the monorepo boundary**

```powershell
git -C C:\tmp\aiprohar-site add -- README.md
git -C C:\tmp\aiprohar-site commit -m "chore: move aiprohar site to canonical repository"
```

Include explicit removed paths in `git add`/`git rm`; inspect `git status --short` before committing.

- [ ] **Step 6: Push without overwriting remote work**

```powershell
git -C C:\tmp\aiprohar-site fetch origin
git -C C:\tmp\aiprohar-site rebase origin/main
git -C C:\tmp\aiprohar-site push origin main
```

Expected: normal fast-forward push. Never use `--force`.

- [ ] **Step 7: Disable GitHub Pages for my-first-project**

In repository settings, set Pages source to disabled. Confirm `aiprohar.ru` remains configured only in `prohar2f-pixel.github.io`.

### Task 7: Final production and rollback verification

**Files:**
- No source changes expected.

**Interfaces:**
- Consumes: final GitHub and DNS state.
- Produces: evidence that one canonical repository serves the domain and other projects remain intact.

- [ ] **Step 1: Verify production routes and DNS**

Request the apex, `www`, `/aeo/`, legal pages, search-verification files, and all legacy/compatibility URLs. Record HTTP status, final URL, and TLS result.

- [ ] **Step 2: Verify repository roles**

Confirm `prohar2f-pixel.github.io/main` contains `CNAME` and production site files. Confirm `my-first-project` has Pages disabled and its README points to the canonical site repository.

- [ ] **Step 3: Verify rollback references**

```powershell
git -C C:\tmp\aiprohar-root ls-remote --tags origin backup/before-aiprohar-split-2026-07-27
git -C C:\tmp\aiprohar-site ls-remote --tags origin backup/before-aiprohar-split-2026-07-27
```

Expected: both remote tags resolve to the recorded pre-migration commits.

- [ ] **Step 4: Document completion**

Update the canonical README with the verified deployment URL, DNS ownership (Beget), Pages source (`main` / root), and rollback tag name. Commit and push this documentation-only update after re-running the link audit.
