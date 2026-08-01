// fixture: no inline @-header (no real header block), no manifest entry for this dir — path matches layerRule "**/service/**"
// (layer=service via rule tier) but the narrowed admin domain ("web/admin/pages/**") does NOT match
// this path → resolveHeader _source must be "rule" alone (no domain contribution).
export function AdminGuard() {
  return true;
}
