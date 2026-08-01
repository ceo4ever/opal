// fixture: no inline @-header (no real header block) — path matches BOTH "**/foo/**" and "**/goo/**" layerRules
// with identical specificity score; expected winner = "layer-foo" (alphabetical tie-break),
// regardless of declaration order (H-12).
export const marker = true;
