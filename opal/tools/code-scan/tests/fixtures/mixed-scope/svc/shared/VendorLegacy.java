package svc.shared;

// fixture: mixed-scope out_of_scope member — matches neither "Order*.java" nor "Ship*.java" include,
// and is intentionally NOT registered in either scope's manifest (order-svc/ship-svc _root.json) — TS-014/TS-035~037.

public class VendorLegacy {
    public void legacyOp() {
    }
}
