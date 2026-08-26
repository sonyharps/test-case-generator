# User Stories: E-Commerce Checkout

**Document ID:** US-ECO-2024-001
**Source:** Product Backlog
**Domain:** E-Commerce (matches PRD-ECO-2024-001)

---

## Epic 1: Shopping Cart Experience

### US-001: Add Product to Cart
**As a** registered customer,
**I want to** add a product to my shopping cart from the product detail page,
**so that** I can purchase it later without losing my selection.

**Acceptance Criteria:**
- Given I am on a product detail page, when I click "Add to Cart", then the product is added with quantity 1.
- Given the product is already in my cart, when I add it again, then the quantity increments (not duplicated as new row).
- Given I am a guest (not logged in), when I add a product, then it is added to a session cart and I can still checkout.
- Given the product is out of stock, when I click "Add to Cart", then the button is disabled with tooltip "Stok habis".

---

### US-002: Adjust Cart Quantity
**As a** customer,
**I want to** change the quantity of items in my cart,
**so that** I can buy the right amount.

**Acceptance Criteria:**
- Given I am in my cart, when I increase quantity, then the subtotal updates in real-time.
- Given I set quantity to 0, then the item is removed from the cart (with undo toast for 5 seconds).
- Given I try to set quantity above 99, then the input is capped at 99 and a warning "Maksimum 99 per produk" appears.
- Given the stock is less than requested quantity, then the quantity is capped at available stock with a message.

---

### US-003: Apply Promo Code
**As a** registered customer,
**I want to** enter a promo code at checkout,
**so that** I can get a discount on my order.

**Acceptance Criteria:**
- Given I have a valid promo code, when I enter it and click "Apply", then the discount is reflected in the order summary.
- Given the promo code is expired, when I apply it, then an error "Kode promo sudah berakhir" is shown.
- Given my order total is below the promo's minimum spend, when I apply, then an error specifies the required minimum.
- Given I already applied 2 promo codes (1 product + 1 shipping), when I try a third, then it is rejected with "Maksimum 2 voucher per order".

---

## Epic 2: Checkout Flow

### US-004: Guest Checkout
**As a** guest user,
**I want to** checkout without creating an account,
**so that** I can buy quickly without commitment.

**Acceptance Criteria:**
- Given I am a guest with items in cart, when I click "Checkout", then I can proceed by entering email + phone.
- Given I complete a guest checkout, then an account is NOT auto-created, but I receive order confirmation via email.
- Given I later register with the same email used for guest checkout, then my past orders are linked to my new account.

---

### US-005: Select Payment Method
**As a** customer,
**I want to** choose my preferred payment method,
**so that** I can pay using my available option.

**Acceptance Criteria:**
- Given I am at the payment step, when I select "Virtual Account", then a VA number is generated and displayed with a countdown timer (24 hours).
- Given I select "Credit Card", when I enter card details, then 3D Secure redirects me to my bank's verification page.
- Given I select "COD" but my order exceeds Rp 2.000.000, then COD is disabled with tooltip "COD maksimum Rp 2.000.000".
- Given my payment times out (VA expired / card 3DS failed), then my order is cancelled and cart restored.

---

### US-006: Receive Order Confirmation
**As a** customer,
**I want to** receive confirmation after placing an order,
**so that** I have proof of purchase and tracking info.

**Acceptance Criteria:**
- Given my payment is confirmed, when the order completes, then I receive an email within 1 minute with order ID + receipt.
- Given I opted into WhatsApp notifications, when the order ships, then I receive a WhatsApp message with tracking link.
- Given the email service is down, when order completes, then the system retries 3x and logs the failure for manual resend.

---

## Epic 3: Order Management

### US-007: Track Order Status
**As a** customer,
**I want to** track my order status,
**so that** I know when to expect delivery.

**Acceptance Criteria:**
- Given my order is confirmed, when I view "My Orders", then I see status: Confirmed → Packed → Shipped → Delivered.
- Given my order is shipped, when I click the tracking link, then I am redirected to the courier's tracking page.
- Given my order is delayed (> estimated delivery + 2 days), then the status shows "Terlambat" and a complaint button appears.

---

### US-008: Cancel Pending Order
**As a** customer,
**I want to** cancel an order I just placed,
**so that** I can fix a mistake before it ships.

**Acceptance Criteria:**
- Given my order is in "Confirmed" status (not yet packed), when I click "Cancel Order", then a confirmation dialog appears.
- Given I confirm cancellation, when the order is cancelled, then a full refund is initiated (processed in 3-5 business days).
- Given my order is already "Packed" or "Shipped", when I try to cancel, then the cancel button is disabled with message "Pesanan sudah diproses".

---

*End of User Stories Document*
