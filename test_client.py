import requests
import pandas as pd
import time

BASE_URL = "http://localhost:5000"

def send_transaction(row):
    payload = {
        "transaction_id": int(row['transaction_id']),
        "merchant_id": int(row['merchant_id']),
        "user_id": int(row['user_id']),
        "card_number": "434505******9116",  # mock
        "transaction_date": row['transaction_date'],
        "transaction_amount": float(row['transaction_amount']),
        "device_id": int(row['device_id']) if pd.notna(row['device_id']) else None
    }
    resp = requests.post(f"{BASE_URL}/evaluate", json=payload)
    return resp.json()

def register_chargeback(user_id):
    requests.post(f"{BASE_URL}/chargeback", json={"user_id": int(user_id)})

if __name__ == "__main__":
    df = pd.read_csv("transactional-sample.csv")
    # Convert date
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])

    # First, register some chargebacks (simulate historical data)
    # For demonstration, we can register all users that have has_cbk==True
    cbk_users = df[df['has_cbk'] == True]['user_id'].unique()
    for uid in cbk_users:
        register_chargeback(uid)

    # Now evaluate all transactions in chronological order (to respect time windows)
    df_sorted = df.sort_values('transaction_date')
    results = []
    for _, row in df_sorted.iterrows():
        decision = send_transaction(row)
        results.append({
            "transaction_id": row['transaction_id'],
            "original_has_cbk": row['has_cbk'],
            "recommendation": decision.get('recommendation'),
            "reason": decision.get('reason', '')
        })

    # Print summary
    df_res = pd.DataFrame(results)
    print(df_res.head(20))
    print(f"\nTotal transactions: {len(df_res)}")
    print(f"Approved: {sum(df_res['recommendation'] == 'approve')}")
    print(f"Denied: {sum(df_res['recommendation'] == 'deny')}")
    # Compare with actual fraud
    denied_fraud = df_res[(df_res['recommendation'] == 'deny') & (df_res['original_has_cbk'] == True)]
    approved_fraud = df_res[(df_res['recommendation'] == 'approve') & (df_res['original_has_cbk'] == True)]
    print(f"Fraudulent transactions denied: {len(denied_fraud)}")
    print(f"Fraudulent transactions approved (missed): {len(approved_fraud)}")