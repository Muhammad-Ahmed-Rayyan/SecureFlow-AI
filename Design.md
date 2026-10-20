# Design.md — Frontend Specification · SecureFlow AI

> Built from the supplied "Genova" cybersecurity landing template. We copy its **UI components, colors, type and spacing**, not its brain visual. Values are measured from a 844×504 screenshot and scaled to a 1440×900 desktop baseline, so treat them as close approximations and match by eye.
> Stack: Next.js 14 (App Router), TypeScript, Tailwind CSS, Recharts, lucide-react, SWR.

---

## 1. Design intent

A near-black navy canvas, a single electric-blue accent, very large light-weight headlines, and a few precise pill-shaped controls. Quiet and confident. The one memorable element is the **blue arrow orb inside a pill button**; everything else stays restrained.

Judges will view this on a projector, so: high contrast, big numbers, no tiny text on the dashboard, nothing that depends on hover.

Where the template pins the look (bracket labels, pill buttons, floating bottom nav), follow it exactly.

---

## 2. Template anatomy (what we are copying)

| Template element | Spec we extract |
|---|---|
| Page frame | Full-bleed dark panel, large corner radius (about 20px) and a 1px translucent border |
| Logo (top-left) | Small glyph + wordmark, uppercase, wide-ish tracking, "GEN" white and "OVA" slightly dimmer |
| Top-right button | **Ghost pill**: dark fill, 1px translucent border, white label, **blue circular arrow button** at its right end |
| Eyebrow | `[ CYBER SECURITY.. ]` small, brackets, muted blue, letter-spaced |
| Headline | Huge, light weight (300), tight leading (~0.92) and tight tracking, near-white with a faint cool tint. Split into a left block and a right block with the visual in the gap. Final period is **accent blue** |
| Body blurb | Tiny (11–12px), light grey, narrow column (~260px), set beside the right headline block |
| Primary CTA | **White pill**, dark label, **blue circular arrow button** at the right end, subtle glow |
| Scroll hint | Bottom-left, down-arrow icon + "Scroll to explore", 11px, muted |
| Bottom navigation | **Floating dark glass pill**, centered, bottom 24px. Items: active item has a lighter rounded chip and a small blue dot before the label; one item can carry a small blue "+" glyph |
| Decorative | Thin 1px constellation lines linking small icon nodes (lock, node) in blue-grey, faint star dust in the background, soft blue glow |

---

## 3. Design tokens

### 3.1 Colors

| Token | Hex | Use |
|---|---|---|
| `bg-0` | `#04060D` | page background |
| `bg-1` | `#070B18` | panels |
| `bg-2` | `#0B1022` | raised panels, table header |
| `ink` | `#E9EDFF` | headlines, primary text (cool near-white) |
| `ink-muted` | `#9AA3C0` | body text, labels |
| `ink-dim` | `#69718F` | tertiary text, axes |
| `accent` | `#2B59FF` | arrow orb, final period, active dots, primary charts |
| `accent-bright` | `#4C7DFF` | hover, focus ring, links |
| `accent-soft` | `#5B7CFF` | bracket eyebrow text |
| `border` | `rgba(255,255,255,0.10)` | card and pill borders |
| `border-soft` | `rgba(255,255,255,0.06)` | nav pill, table lines |
| `glass` | `rgba(255,255,255,0.04)` | card fill |
| `glass-strong` | `rgba(255,255,255,0.07)` | active nav chip, hover |
| `white-pill` | `#FFFFFF` | primary CTA fill |

Semantic colors (additions the template does not need but a dashboard does):

| Token | Hex | Use |
|---|---|---|
| `sev-critical` | `#FF4D6A` | CRITICAL |
| `sev-high` | `#FF8A3D` | HIGH |
| `sev-medium` | `#F5C451` | MEDIUM |
| `sev-low` | `#4CC38A` | LOW |
| `ok` | `#3DDC97` | pass, merged |
| `warn` | `#F5C451` | retry, warning |
| `bad` | `#FF4D6A` | fail, closed |

Rules: blue is the only brand color. Severity colors appear only on severity badges and the severity chart. Never use gradients as decoration except the single ambient glow behind the hero and page headers.

### 3.2 Typography

| Role | Font | Notes |
|---|---|---|
| Display + UI | **Inter Tight** (Google Fonts via `next/font`) | weights 300, 400, 500 |
| Labels, code, trace, diff | **JetBrains Mono** | weights 400, 500 |

| Style | Size | Weight | Leading | Tracking |
|---|---|---|---|---|
| Hero display | `clamp(56px, 7.2vw, 112px)` | 300 | 0.92 | -0.04em |
| Page title (H1) | 44px | 300 | 1.0 | -0.03em |
| Section title (H2) | 22px | 400 | 1.2 | -0.01em |
| Card title | 14px | 500 | 1.3 | 0 |
| Big number | 56px | 300 | 1 | -0.03em |
| Body | 14px | 400 | 1.55 | 0 |
| Small / blurb | 12px | 400 | 1.55 | 0 |
| Eyebrow | 11px mono, uppercase, tracking 0.12em | 400 | 1 | 0.12em |
| Nav item | 13px | 400 | 1 | 0 |
| Code / trace | 12.5px mono | 400 | 1.6 | 0 |

Line length for paragraphs under 70 characters. Sentence case everywhere except the bracket eyebrow and the wordmark.

### 3.3 Shape, spacing, elevation

- Radius: pill `999px`, card `20px`, chip `10px`, input `12px`.
- Spacing scale: 4, 8, 12, 16, 24, 32, 48, 80.
- Page padding: 32px desktop, 16px mobile. Max content width 1280px (hero is full-bleed).
- Card: `glass` fill, 1px `border`, radius 20, `backdrop-blur-md`, inner top highlight.
- Glow (primary CTA and arrow orb): `0 0 0 1px rgba(76,125,255,.35), 0 8px 40px rgba(43,89,255,.35)`.

### 3.4 Motion

One orchestrated moment: on landing load the headline blocks rise 12px and fade in over 600 ms, staggered by 80 ms. Elsewhere motion answers an action only:
- arrow orb nudges up-right 2px on pill hover;
- KPI numbers count up once when first visible;
- running agent node pulses (blue ring, 1.4 s) while active;
- new trace lines slide in 6px.

Respect `prefers-reduced-motion` (disable all of the above except color changes).

---

## 4. Files to create (complete copy-paste)

### 4.1 `frontend/tailwind.config.ts`

```ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: { 0: "#04060D", 1: "#070B18", 2: "#0B1022" },
        ink: { DEFAULT: "#E9EDFF", muted: "#9AA3C0", dim: "#69718F" },
        accent: { DEFAULT: "#2B59FF", bright: "#4C7DFF", soft: "#5B7CFF" },
        sev: {
          critical: "#FF4D6A",
          high: "#FF8A3D",
          medium: "#F5C451",
          low: "#4CC38A",
        },
        ok: "#3DDC97",
        warn: "#F5C451",
        bad: "#FF4D6A",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: { pill: "999px", card: "20px", chip: "10px" },
      boxShadow: {
        glow: "0 0 0 1px rgba(76,125,255,.35), 0 8px 40px rgba(43,89,255,.35)",
        card: "0 1px 0 rgba(255,255,255,.04) inset, 0 20px 60px rgba(0,0,0,.45)",
      },
      letterSpacing: { display: "-0.04em", title: "-0.03em" },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseRing: {
          "0%": { boxShadow: "0 0 0 0 rgba(76,125,255,.55)" },
          "100%": { boxShadow: "0 0 0 10px rgba(76,125,255,0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        slideIn: {
          "0%": { opacity: "0", transform: "translateX(-6px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
      },
      animation: {
        rise: "rise .6s cubic-bezier(.2,.7,.2,1) both",
        pulseRing: "pulseRing 1.4s ease-out infinite",
        shimmer: "shimmer 1.6s linear infinite",
        slideIn: "slideIn .25s ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
```

### 4.2 `frontend/app/globals.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --bg-0: #04060d;
  --bg-1: #070b18;
  --bg-2: #0b1022;
  --ink: #e9edff;
  --ink-muted: #9aa3c0;
  --ink-dim: #69718f;
  --accent: #2b59ff;
  --accent-bright: #4c7dff;
  --border: rgba(255, 255, 255, 0.1);
  --border-soft: rgba(255, 255, 255, 0.06);
  --glass: rgba(255, 255, 255, 0.04);
  --glass-strong: rgba(255, 255, 255, 0.07);
}

html,
body {
  background: var(--bg-0);
  color: var(--ink);
  font-family: var(--font-sans), system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* Ambient background: deep navy, one soft blue glow top-right, faint star dust */
.bg-space {
  background:
    radial-gradient(60rem 38rem at 72% -12%, rgba(43, 89, 255, 0.28), transparent 62%),
    radial-gradient(38rem 26rem at 8% 108%, rgba(43, 89, 255, 0.12), transparent 60%),
    var(--bg-0);
}

.stars {
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0.55;
  background-image:
    radial-gradient(1px 1px at 20px 30px, rgba(255, 255, 255, 0.7), transparent),
    radial-gradient(1px 1px at 90px 140px, rgba(255, 255, 255, 0.5), transparent),
    radial-gradient(1.5px 1.5px at 160px 60px, rgba(160, 190, 255, 0.7), transparent),
    radial-gradient(1px 1px at 210px 190px, rgba(255, 255, 255, 0.4), transparent),
    radial-gradient(1px 1px at 130px 220px, rgba(255, 255, 255, 0.55), transparent);
  background-size: 240px 240px;
}

/* Glass card */
.glass {
  background: var(--glass);
  border: 1px solid var(--border);
  border-radius: 20px;
  backdrop-filter: blur(12px);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.04) inset, 0 20px 60px rgba(0, 0, 0, 0.45);
}

/* Floating nav pill */
.nav-pill {
  background: rgba(14, 18, 32, 0.72);
  border: 1px solid var(--border-soft);
  border-radius: 16px;
  backdrop-filter: blur(16px);
}

/* Skeleton shimmer */
.skeleton {
  background: linear-gradient(90deg, rgba(255,255,255,.04) 25%, rgba(255,255,255,.09) 50%, rgba(255,255,255,.04) 75%);
  background-size: 200% 100%;
  border-radius: 12px;
}

/* Scrollbars */
* { scrollbar-width: thin; scrollbar-color: rgba(255,255,255,.18) transparent; }

/* Focus ring (visible keyboard focus is required) */
:focus-visible { outline: 2px solid var(--accent-bright); outline-offset: 2px; border-radius: 12px; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
```

### 4.3 `frontend/app/layout.tsx` (fonts and shell)

```tsx
import "./globals.css";
import type { Metadata } from "next";
import { Inter_Tight, JetBrains_Mono } from "next/font/google";
import TopBar from "@/components/layout/TopBar";
import FloatingNav from "@/components/layout/FloatingNav";

const sans = Inter_Tight({ subsets: ["latin"], weight: ["300", "400", "500"], variable: "--font-sans" });
const mono = JetBrains_Mono({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "SecureFlow AI",
  description: "Scanner findings in, validated draft pull requests out.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      <body className="bg-space min-h-screen relative overflow-x-hidden">
        <div className="stars" aria-hidden />
        <TopBar />
        <main className="relative z-10 pb-32">{children}</main>
        <FloatingNav />
      </body>
    </html>
  );
}
```

---

## 5. Component library

All live in `frontend/components/`. Props are typed; no `any`.

### 5.1 `ui/ArrowOrb`
Circle 36px (28px in small pills), fill `accent`, white `ArrowUpRight` icon (lucide, 16px). On parent hover translate icon `(2px, -2px)`. Optional glow.

### 5.2 `ui/PillButton`
Props: `variant: "primary" | "ghost"`, `size: "md" | "sm"`, `href?`, `onClick?`, `loading?`, `disabled?`, `icon?: "arrow" | "none"`.
- **primary**: white fill, `#06080F` text 14px/500, height 44px, padding `0 6px 0 22px`, radius pill, trailing `ArrowOrb`, `shadow-glow` on hover.
- **ghost**: fill `rgba(255,255,255,.04)`, 1px `border`, white text, same geometry, trailing `ArrowOrb`.
- `sm`: height 36px, orb 28px, text 13px.
- Loading: replace arrow with a 16px spinner ring; label becomes the in-progress verb ("Remediating").
- Disabled: 40% opacity, orb turns grey, tooltip explains why.

### 5.3 `ui/BracketLabel`
`[ LABEL.. ]` rendered in mono 11px, uppercase, tracking 0.12em, color `accent-soft`, brackets in `ink-dim`.

### 5.4 `ui/GlassCard`
`.glass` with padding 24px (20px on dense cards). Optional header row: title (14px/500) + right-aligned action slot.

### 5.5 `ui/Badge` family
- `SeverityBadge`: dot 8px + label, text 12px, background `severity color @ 12%`, 1px border `@ 30%`.
- `TierChip`: AUTO_FIX (blue), DEPENDENCY (neutral), ESCALATE (amber), UNSUPPORTED_LANG (neutral dashed border). Text: "Auto-fix", "Dependency", "Escalated", "Adapter not enabled".
- `StatusPill`: NEW, Queued, Running (pulsing blue dot), PR open (blue), Merged (green), Rejected (red), Escalated (amber), Failed (red).
- `FlagIcon`: small icon with tooltip for DQ flags (language mismatch, description mismatch, duplicate, missing time).

### 5.6 `ui/Skeleton`, `ui/Toast`, `ui/EmptyState`
Skeleton uses `.skeleton`. Toast bottom-right above the nav, 4 s. EmptyState: one sentence + one action ("No runs yet. Remediate a finding to see the agents work.").

### 5.7 `layout/TopBar`
Height 72px, padding `0 32px`. Left: **wordmark** (glyph + `SECURE` white + `FLOW` in `ink-muted`, 15px, tracking 0.08em, uppercase). Right: small status chip "API online" (green dot, polls `/api/health` every 30 s) and a **ghost PillButton** "View on GitHub" linking to the main repo.

### 5.8 `layout/FloatingNav`
Fixed, bottom 24px, centered, z-50, `.nav-pill`, padding 6px.
Items: **Home**, **Dashboard**, **Findings**, **Runs**.
- Item: padding `8px 14px`, radius 10px, text 13px `ink-muted`.
- Active: background `glass-strong`, text `ink`, a 5px `accent` dot before the label.
- Hover: text `ink`.
- Findings item shows a tiny blue "+" glyph only when there are fix-ready findings (mirrors the template's decorated item).
- Mobile: same pill, icons only below 480px.

### 5.9 `layout/ScrollHint`
Bottom-left on landing: `ArrowDown` icon 14px in `accent-bright` + "Scroll to explore" 11px `ink-muted`.

### 5.10 `layout/Constellation`
Decorative SVG used on the landing hero and as the background of the run-detail agent graph: 1px lines `rgba(255,255,255,.22)`, small node circles with lucide icons (Shield, Search, Wrench, CheckCircle, GitPullRequest) at 14px, label 10px mono. Static, no animation except the active node's pulse ring on run detail.

---

## 6. Screens

Desktop baseline 1440×900. Every page has `TopBar` and `FloatingNav`.

### 6.1 Landing `/`

```
[TopBar: SECUREFLOW                                   (API online) (View on GitHub ↗)]

[ DEVSECOPS.. ]
Remediating                         ( ambient glow +                in
the Backlog                           constellation of 5 agents )   Minutes.        SecureFlow AI turns scanner
                                                                                    findings into validated,
(Open dashboard ↗)                                                                  review-ready draft pull
                                                                                    requests.
↓ Scroll to explore                    [ Home ][Dashboard][Findings][Runs]
```

- Headline: left block "Remediating / the Backlog", right block "in / Minutes." The final period is `accent`.
- Blurb (12px, 260px wide) sits right of "in", like the template.
- Primary CTA "Open dashboard" below the left block.
- Center visual: a soft blue radial orb (CSS, ~420px) with the **Constellation** of the five agents around it. No brain, no stock imagery.
- Below the fold, **How it works**: five agent cards in a row (Triage, Analyzer, Fixer, Validator, PR) each with one sentence; connectors drawn as thin lines. Then **By the numbers** as three large figures fetched from `/api/metrics/summary`: open findings, estimated engineer-hours, share of backlog without a scanner fix. Finish with a repeat primary CTA.
- Load animation: headline rise stagger.

### 6.2 Dashboard `/dashboard`

Header: `[ OVERVIEW.. ]`, H1 "Security debt, live." Right side: ghost pill "Refresh" (calls `/api/prs/sync`) and last-updated timestamp.

Row 1, four KPI cards (equal width):
1. **Time to review-ready PR**: big value (e.g. "3m 12s"), sub "vs 6.8 h manual effort", delta "-99%" in green. Empty state before any run: "Run a remediation to measure".
2. **Acceptance rate**: big percentage, sub "n merged of n decided". Before any decision: "No decisions yet".
3. **Open backlog**: big number (starts 96), sub "12 critical, 27 high".
4. **Engineer-hours saved**: big number, sub "from merged fixes", with "of 654 h backlog" progress bar.

Row 2:
- (2/3) **Backlog, live**: stacked area/bars from `/api/metrics/backlog` timeline: open (blue), in review (blue-bright), merged (green). Starts at the CSV baseline then moves with real PR events.
- (1/3) **Backlog by age and severity**: grouped bars, age buckets 0–30, 31–90, 90+ with severity colors.

Row 3:
- (1/3) **Remediation funnel**: horizontal bars: Backlog 96 → Auto-fix types 70 → Supported language 21 → Fix-ready 8 → PRs opened → Merged. Each bar has count and a one-line caption.
- (1/3) **MTTR comparison**: two bars, manual (6.8 h) vs SecureFlow (measured, minutes) with the percentage reduction; below it a small table of time-to-draft-PR and time-to-merge.
- (1/3) **Recent runs**: last 6 runs: finding id, type, status pill, elapsed, PR link.

Footer note on the page (12px muted): "Baseline from ps09_vulnerability_scans.csv (synthetic). Agent timings and acceptance are measured from real runs."

Polling: 5 s via SWR. KPI numbers count up once.

### 6.3 Findings `/findings`

Header: `[ BACKLOG.. ]`, H1 "Findings". Actions (right): ghost "Import scan", ghost "Scan repo now", primary "Remediate top 3 criticals" (disabled with tooltip if fewer than one fix-ready critical).

Filter bar (glass strip): search input, severity multi-select chips, type select, repository select, tier select, status select, toggle **"Fix-ready only"**. Default sort: priority desc. Result count on the right.

Table (sticky header, 25 rows per page):

| Column | Content |
|---|---|
| Severity | `SeverityBadge` |
| ID | mono, e.g. VULN-0169 |
| Type | text |
| Repository | text |
| File | mono, truncated middle, tooltip full path + reported line |
| Scanner | text |
| Age | days, color shifts amber over 90 |
| Tier | `TierChip` (tooltip shows rationale) |
| Flags | `FlagIcon`s |
| Status | `StatusPill` |
| Action | small `PillButton` "Remediate" (primary sm) for fix-ready; otherwise a muted label ("Source not connected", "Adapter not enabled", "Needs human") |

Row click opens a right **drawer** (480px): description with a banner if it conflicts with the type, baseline hours (and whether imputed), tier reason, DQ flags explained, run history with links.

Import modal: drag-and-drop for CSV, SARIF or JSON, format auto-detected, shows counts and data-quality summary after import, button "Import".

"Scan repo now" shows a progress toast then adds the new findings (source "sarif") at the top.

### 6.4 Run detail `/runs/[id]`

Top strip: finding id and type, severity badge, status pill, elapsed timer (live), attempt counter "Attempt 1 of 3", **confidence** and **risk** badges once available.

Left column (60%):
- **Agent graph**: five nodes in a row (Triage, Analyzer, Fixer, Validator, PR) on the constellation background. Node states: idle (outline), active (blue fill + pulse ring), done (green check), failed (red cross). When the Validator fails and loops back, show a curved arrow Validator → Fixer labelled "retry 1".
- **Live trace**: mono log, newest at the bottom, auto-scroll with a "Jump to latest" chip if the user scrolls up. Each line: time offset (`+12.4s`), agent chip, message. Levels color the message (info muted, success green, warn amber, error red). New lines slide in.

Right column (40%), tabs **Diff | Evidence | Pull request**:
- **Diff**: unified diff from `run.patch.diff`, added lines green tint, removed red tint, line numbers, plain-English explanation above it, "Reported line 248, found at line 31" callout when drift exists.
- **Evidence**: table with rows Policy gate, Syntax, Functional tests, Exploit tests, Bandit; columns Before and After; pass/fail pills; counts such as "2 failed" → "2 passed". Collapsible raw log tail.
- **Pull request**: title, number, branch, state pill (Draft, Merged, Closed), time-to-draft, "Open on GitHub" primary pill, rendered PR body preview as plain text sections.

Escalated runs show a calm card: tier, reason, "Why SecureFlow did not auto-fix this", and a button "Open in findings".

### 6.5 Runs `/runs`

Header `[ ACTIVITY.. ]`, H1 "Runs". Table: run id, finding, type, status, attempts, time-to-draft, PR, started. Row click opens run detail.

---

## 7. States and copy

Voice: plain, active, sentence case, no apology, say what happened and what to do.

| Moment | Copy |
|---|---|
| Remediate button | "Remediate" → loading "Remediating" → success toast "Remediation started" |
| Validator failure | "Validation failed, sending errors back to the Fixer (retry 1 of 2)" |
| Run failed | "Could not produce a passing fix after 3 attempts. See the log and review manually." |
| Escalated | "Escalated to a human: {reason}" |
| No source | "Source not connected. Connect the repository to enable remediation." |
| Unsupported language | "Adapter not enabled for {language}. Findings are still triaged and tracked." |
| API error toast | "Request failed. Check the API status and try again." |
| Empty runs | "No runs yet. Remediate a finding to see the agents work." |
| Empty dashboard metrics | "Run a remediation to measure time-to-PR." |

Loading: skeleton blocks matching final layout. Never show a blank card.

---

## 8. Data formatting rules

- Durations: under 60 s "42s"; under 1 h "3m 12s"; else "6.8 h".
- Percentages: 0 decimals; acceptance shows `n`.
- Numbers use thousands separators; hours one decimal.
- Dates: relative ("2 min ago") with absolute in tooltip.
- Severity order everywhere: CRITICAL, HIGH, MEDIUM, LOW.

---

## 9. Responsive and accessibility

- Breakpoints: ≥1280 full layout; 768–1279 KPI grid 2×2, charts stack, run detail columns stack; <768 table becomes card list, nav pill shows icons only.
- Contrast: body text on `bg-0` must be ≥ 4.5:1 (`ink-muted` is the minimum for body).
- Keyboard: every control focusable with visible ring; table rows open with Enter; tabs use arrow keys.
- Aria: live trace region `aria-live="polite"`; pills have text labels, not color alone.
- Never rely on hover for essential info (tooltips duplicate visible text).

---

## 10. Implementation notes for Antigravity

- Use `lucide-react` icons only; no icon images.
- Use `next/font/google` for the two fonts (variables `--font-sans`, `--font-mono`).
- Charts: Recharts with transparent backgrounds, axis text `ink-dim` 11px, grid lines `rgba(255,255,255,.06)`, tooltips styled as `.glass`.
- Data fetching: SWR with `refreshInterval` per page (dashboard 5000, run detail 2000 while active, off when finished).
- All calls go to `/api/...` on the same origin (Next.js proxy route). No backend URL in client code.
- Render diff and logs as text nodes. Never `dangerouslySetInnerHTML`.
- Do not hardcode metric values in components; every number comes from the API. The "96", "654 h" in this document are expected values from the dataset, not constants.
- Build order is in `Phase.md` (Phase 4 design system and landing, Phase 6 dashboard, findings, run detail).
