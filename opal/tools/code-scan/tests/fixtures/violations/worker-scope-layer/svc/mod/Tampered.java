package svc.mod;
// fixture: this manifest illegally declares package.layer / package.domain / files.module
// (all tool-only fields). "scan" result's layer must still be derived purely from layerRules
// (rule tier), never from the illegal package.layer value — interpretation-ignore check (TS-034).
public class Tampered {}
