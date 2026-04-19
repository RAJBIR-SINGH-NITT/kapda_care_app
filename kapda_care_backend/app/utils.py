# ============================================================
# UTILS.PY — Kapda Care Helper Functions
# This file does not define routes; it handles core calculations
# ============================================================

# Base rate for each clothing item (in Rupees)
RATES = {
    # --- Standard Laundry ---
    'shirt':            {'wash': 20,  'dryclean': 60,  'iron': 10,  'express_add': 30},
    'pant':             {'wash': 25,  'dryclean': 80,  'iron': 15,  'express_add': 30},
    'suit':             {'wash': 0,   'dryclean': 200, 'iron': 50,  'express_add': 100},
    'saree':            {'wash': 50,  'dryclean': 150, 'iron': 30,  'express_add': 50},
    'kurta':            {'wash': 20,  'dryclean': 70,  'iron': 10,  'express_add': 30},
    'jacket':           {'wash': 0,   'dryclean': 180, 'iron': 40,  'express_add': 80},
    'bedsheet':         {'wash': 60,  'dryclean': 0,   'iron': 25,  'express_add': 40},
    'blanket':          {'wash': 120, 'dryclean': 250, 'iron': 0,   'express_add': 80},
    # --- Premium / Specialty ---
    'sneaker':          {'wash': 150, 'dryclean': 0,   'iron': 0,   'express_add': 100},
    'leather_bag':      {'wash': 0,   'dryclean': 300, 'iron': 0,   'express_add': 150},
    'saree_restoration':{'wash': 0,   'dryclean': 500, 'iron': 0,   'express_add': 200},
    'invisible_darning':{'wash': 0,   'dryclean': 400, 'iron': 0,   'express_add': 150},
    # --- Default fallback for unspecified items ---
    'other':            {'wash': 30,  'dryclean': 100, 'iron': 15,  'express_add': 40},
}

# Services categorized under laundry
LAUNDRY_SERVICES = {'wash', 'dryclean', 'iron'}

# Services categorized under tailoring
TAILORING_SERVICES = {'taper', 'hem', 'stitch', 'alteration', 'invisible_darning', 'saree_restoration'}

TAILORING_RATES = {
    'taper':       150,
    'hem':         80,
    'stitch':      300,
    'alteration':  120,
}


def calculate_total_price(items, is_express=False):
    """
    The format of items should be as follows:
    [
      {'type': 'shirt', 'quantity': 2, 'service': 'wash'},
      {'type': 'pant',  'quantity': 1, 'service': 'taper'},
      {'type': 'saree', 'quantity': 1, 'service': 'dryclean'}
    ]
    
    Returns: (total, discount, final_price)
    """
    total = 0
    item_count = 0
    
    for item in items:
        item_type    = item.get('type', 'other').lower()
        service      = item.get('service', 'wash').lower()
        quantity     = item.get('quantity', 1)
        
        # Fetch the rate — use 'other' as fallback if the item type is not found
        item_rates = RATES.get(item_type, RATES['other'])
        
        if service in TAILORING_SERVICES:
            # Tailoring has separate fixed rates
            base_price = TAILORING_RATES.get(service, 150)
        else:
            # Laundry/dryclean/iron rates
            base_price = item_rates.get(service, item_rates.get('wash', 30))
        
        # Additional charge for express service
        if is_express:
            express_extra = item_rates.get('express_add', 40)
            base_price += express_extra
        
        total += base_price * quantity
        item_count += quantity
    
    # --- Discount Logic ---
    discount = 0.0
    
    # 10% discount for 5 or more items
    if item_count >= 5:
        discount += total * 0.10
    
    # Flat ₹50 off for bills above ₹500
    if (total - discount) > 500:
        discount += 50
    
    discount  = round(discount, 2)
    final     = round(total - discount, 2)
    total     = round(total, 2)
    
    return total, discount, final


def split_items_by_service(items):
    """
    Split the items of an order into two distinct groups:
    - laundry_items: wash / dryclean / iron
    - tailoring_items: stitch / alteration / hem / etc.
    
    This powers the SPLIT ROUTING feature of Kapda Care!
    """
    laundry_items   = []
    tailoring_items = []
    
    for item in items:
        service = item.get('service', 'wash').lower()
        if service in TAILORING_SERVICES:
            tailoring_items.append(item)
        else:
            laundry_items.append(item)
    
    return laundry_items, tailoring_items


def add_timeline_entry(order_id, status, message, updated_by=None):
    """
    Add an entry to the order timeline when the status changes.
    This allows the customer to track their order progress.
    """
    from . import db
    from .models import OrderTimeline
    
    entry = OrderTimeline(
        order_id   = order_id,
        status     = status,
        message    = message,
        updated_by = updated_by
    )
    db.session.add(entry)
    # Note: The caller is responsible for executing db.session.commit()
    return entry


# Customer-friendly status messages
STATUS_MESSAGES = {
    'pending':           'Your order has been received! An agent will arrive shortly for pickup.',
    'assigned':          'A Kapda Care agent has been assigned to pick up your order.',
    'picked_up':         'Your clothes have been picked up and are being routed to our partners.',
    'at_partner':        'Your clothes are currently with our washer/tailor. Processing has started!',
    'qc_check':          'Your items are undergoing a quality check at our mini-hub.',
    'out_for_delivery':  'Your clothes are out for delivery! They will reach you shortly.',
    'delivered':         'Delivered! We hope you enjoyed the service. Please leave a review!',
    'cancelled':         'Order cancelled. Please contact support if you face any issues.'
}