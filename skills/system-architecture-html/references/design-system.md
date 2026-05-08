# Design system

The visual language for system architecture HTML diagrams. Follow these rules to keep diagrams cohesive across projects.

## Aesthetic direction

**"Senior engineer's whiteboard captured in code."** Dark IDE / engineering doc tone. The viewer should feel like they're looking at internal documentation written by someone who actually ships code, not a marketing slide.

What this means concretely:
- Dark charcoal background, not pure black, not navy
- Monospace for meta data (versions, tags, paths) — JetBrains Mono
- Sans-serif for content (titles, descriptions) — Inter Tight
- One accent color carried through eyebrows, MVP badges, hover states
- Hairline borders (0.5px–1px), no thick strokes
- Subtle radial atmospherics in body background, no busy textures

## Color tokens

```css
--bg:#0E1014;          /* page background */
--bg-elev:#15181F;     /* node cards, legend, tracks */
--bg-soft:#1A1E27;     /* hover state */
--line:#2A2F3A;        /* primary borders */
--line-soft:#1F232C;   /* dashed dividers */
--text:#E6E7EA;        /* primary text */
--text-mute:#8A8F99;   /* secondary text, descriptions */
--text-dim:#5A5F69;    /* tertiary text, layer numbers */
--accent:#FF5A1F;      /* coral — the one accent */
--accent-soft:#FF5A1F22; /* MVP badge background */
```

**Layer color palette** — six layers maximum, each gets one ramp:

| Layer | Hex | Use case suggestion |
|-------|-----|---------------------|
| L1 | `#7CA9FF` (blue) | Channel / Entry / Frontend |
| L2 | `#9C8CFF` (purple) | Routing / Orchestration / API |
| L3 | `#FF8FA3` (pink) | Logic / Agents / Services |
| L4 | `#5BD3B0` (teal) | Data / Brain / Storage |
| L5 | `#FFB454` (orange) | External / Infra |
| L6 | `#F7C66B` (gold) | Operations / Monitoring |

Layer colors only appear as a 2px left border on each node card and on the matching tag color inside the card. Never as fills — fills always stay `--bg-elev`. This keeps the diagram readable while allowing instant layer recognition.

**When to deviate:** if the brand has a specific accent (e.g. green for an eco-tech product, purple for a fintech), swap `--accent` only. The 6 layer colors can be kept, or rotated to start with the brand color at L1. Don't introduce a 7th color.

## Typography

**Two font families, no exceptions:**

```css
font-family:'Inter Tight',sans-serif;   /* default body */
font-family:'JetBrains Mono',monospace; /* meta, eyebrows, tags, chips, layer labels */
```

**Size scale:**

| Element | Size | Weight | Family |
|---------|------|--------|--------|
| H1 (title) | 44px (clamp on mobile) | 800 | Inter Tight |
| H1 italic accent | inherits | 500 | Inter Tight italic |
| H2 (section) | 28px | 700 | Inter Tight |
| Subtitle / lede | 15–17px | 400 | Inter Tight |
| Node title | 15px | 600 | Inter Tight |
| Node description | 13px | 400 | Inter Tight |
| Eyebrow / track header | 11px, .12em–.20em letterspacing | 600 | JetBrains Mono |
| Layer number | 10px, .15em letterspacing | 400 | JetBrains Mono |
| Chip / badge | 9.5–10px | 400 | JetBrains Mono |

**Letter-spacing rules:**
- Tight (`-.02em`) on large headings
- Default on body
- Wide (`.12em`–`.20em`) on monospace eyebrows and badges
- Never use letter-spacing on body text

## Components

### Node card

The atomic unit. Every node follows this structure:

```html
<div class="node">
  <div class="node-head">
    <div class="node-title">Service name <span class="badge badge-mvp">MVP</span></div>
    <div class="node-tag">role-tag</div>
  </div>
  <div class="node-desc">One-sentence description of what this does.</div>
  <div class="node-tech">
    <span class="chip">Tech1</span>
    <span class="chip">Tech2</span>
  </div>
</div>
```

- Title is left-aligned, role tag is right-aligned in `.node-head`
- Description is 1–2 sentences, max 140 characters
- Tech chips are 1–4 items, monospace, lowercase or PascalCase as the actual tech is named
- Status badge belongs inside `.node-title`, not as a separate row

### Layer block

```html
<div class="layer layer-l3">
  <div class="layer-label">
    <div class="layer-num">LAYER 03</div>
    <div class="layer-name">Agents</div>
    <div class="layer-tag">Multi-agent — separate responsibilities</div>
  </div>
  <div class="boxes boxes-3">
    <!-- 1 to 4 .node cards -->
  </div>
</div>
```

The `.layer-l3` class on the parent triggers the matching color CSS for all child nodes' left borders and tags. Always use `layer-l1` through `layer-l6`.

### Box grid sizes

Pick the grid based on actual node count, not aesthetic preference:

- `boxes-1` — 1 node (typical for orchestration/router layers)
- `boxes-2` — 2 nodes (typical for ops/console layers)
- `boxes-3` — 3 nodes (most common — agent layers, data layers, channel layers)
- More than 3 nodes — split into 2 rows of `boxes-3` or use `boxes-2` + lower row

Never use a 4-column grid — at 1280px width, cards become too narrow to read descriptions.

### Connectors

Between every adjacent layer pair, insert:

```html
<div class="connector"></div>
```

This renders a centered ↓ glyph with a hairline dashed line extending right. It implies "data flows downward from layer N to layer N+1" without committing to specific arrows between specific nodes (which would be wrong — orchestrators fan out, data layers are queried by multiple agents, etc.).

### Status badges

Three variants:

```html
<span class="badge badge-mvp">MVP</span>     <!-- accent coral -->
<span class="badge badge-later">LATER</span> <!-- muted gray -->
<span class="badge badge-done">DONE</span>   <!-- teal -->
```

Every node should have one. If genuinely unsure, default to MVP for the smallest viable subset and LATER for the rest. The DONE badge is for diagrams documenting an existing system.

## Spacing system

```
4px   — chip padding vertical
8px   — node card internal element gap
14px  — between cards in the same layer
20px  — node card padding
28px  — vertical padding per layer
48px  — header → first layer
60px  — section → section
80px  — page bottom padding
```

Don't deviate. The grid feels right because every spacing value comes from this scale.

## Dark mode by default, print fallback

The default theme is dark. The `@media print` block in the template flips to white background + black text + removed shadows so the diagram prints cleanly on A4. Test by hitting Cmd+P before delivering.

## What NOT to do

- **No gradients on cards.** One subtle radial atmospheric on `body::before` is the only gradient permitted.
- **No drop shadows.** The hover `transform: translateY(-2px)` is the only depth cue.
- **No icons inside node cards.** Tech chips do that job. Adding emoji or SVG icons makes the diagram feel like a marketing slide.
- **No center-aligned text** anywhere except in the legend. Architecture is read top-down, left-right.
- **No purple-on-white** anywhere. That's the AI-generated SaaS tell.
- **No more than 6 layers.** If you have 7+, you're conflating data and process layers. Merge or split into two diagrams.
