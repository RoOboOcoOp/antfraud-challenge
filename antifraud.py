import time
from collections import defaultdict, deque
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuration (adjust as needed)
MAX_TRANSACTIONS_PER_WINDOW = 5        # number of tx allowed
WINDOW_SECONDS = 300                   # 5 minutes

MAX_AMOUNT_PER_WINDOW = 1000.0         # in USD
AMOUNT_WINDOW_SECONDS = 86400          # 24 hours

# In-memory state
# user_id -> deque of (timestamp, amount) for recent transactions
user_transactions = defaultdict(lambda: deque())

# set of user_id that have had a chargeback (known from /chargeback endpoint)
users_with_chargeback = set()

# Helper: clean old entries from a deque
def clean_old_entries(user_id, window_seconds):
    """Remove transactions older than window_seconds from the user's deque."""
    now = time.time()
    dq = user_transactions[user_id]
    while dq and dq[0][0] < now - window_seconds:
        dq.popleft()

# Rule 1: Velocity (too many transactions in a row)
def check_velocity(user_id, window_seconds=WINDOW_SECONDS, max_tx=MAX_TRANSACTIONS_PER_WINDOW):
    clean_old_entries(user_id, window_seconds)
    return len(user_transactions[user_id]) >= max_tx

# Rule 2: Amount threshold in a period
def check_amount_sum(user_id, amount, window_seconds=AMOUNT_WINDOW_SECONDS, max_amount=MAX_AMOUNT_PER_WINDOW):
    clean_old_entries(user_id, window_seconds)
    current_sum = sum(tx[1] for tx in user_transactions[user_id])
    return (current_sum + amount) > max_amount

# Rule 3: Historical chargeback
def check_chargeback(user_id):
    return user_id in users_with_chargeback

# Main evaluation function
def evaluate_transaction(user_id, amount):
    reasons = []
    if check_chargeback(user_id):
        reasons.append("User had previous chargeback")
    if check_velocity(user_id):
        reasons.append("Too many transactions in a short period")
    if check_amount_sum(user_id, amount):
        reasons.append("Amount limit exceeded for the period")

    if reasons:
        return "deny", ", ".join(reasons)
    else:
        # Store the transaction (only if approved, but we can store all for monitoring)
        # For the purpose of velocity/amount checks, we store after approval.
        # However, we may want to store even denied transactions to prevent abuse?
        # Here we store after a successful evaluation (approval).
        # If we store before, we might count attempts; let's store only if approved.
        # Alternative: store before and still consider for future checks.
        # We'll store after approval, but we could store regardless.
        now = time.time()
        user_transactions[user_id].append((now, amount))
        return "approve", None

# API Endpoints
@app.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    # Required fields
    required = ['transaction_id', 'user_id', 'transaction_amount']
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    tx_id = data['transaction_id']
    user_id = data['user_id']          # assume integer or string, but consistent
    amount = float(data['transaction_amount'])

    # For security, we might also check merchant, device, etc. but not required.

    decision, reason = evaluate_transaction(user_id, amount)

    response = {
        "transaction_id": tx_id,
        "recommendation": decision
    }
    if reason:
        response["reason"] = reason   # optional, for debugging

    return jsonify(response), 200

@app.route('/chargeback', methods=['POST'])
def register_chargeback():
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({"error": "Missing user_id"}), 400

    user_id = data['user_id']
    users_with_chargeback.add(user_id)
    return jsonify({"status": "recorded", "user_id": user_id}), 200

# Health check (optional)
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # For production, use a WSGI server like gunicorn.
    app.run(host='0.0.0.0', port=5000, debug=True)