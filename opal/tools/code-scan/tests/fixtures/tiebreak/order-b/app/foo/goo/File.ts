// fixture: identical to order-a/app/foo/goo/File.ts — same path, same content.
// no inline @-header (no real header block) — path matches BOTH "**/foo/**" and "**/goo/**" layerRules
// with identical specificity score; expected winner = "layer-foo" (alphabetical tie-break).
export const marker = true;
