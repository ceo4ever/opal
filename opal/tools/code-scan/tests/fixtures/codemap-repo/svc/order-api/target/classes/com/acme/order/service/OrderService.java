package com.acme.order.service;

// fixture: compiled-output duplicate copy (condition ⑤) — must be excluded via exclude:["target"]
public class OrderService {
    public void createOrder() {
        // duplicate compiled artifact — should NOT be scanned
    }
}
