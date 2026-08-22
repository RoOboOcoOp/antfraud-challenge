# Anti‑Fraud Service – Data Analyst Challenge

This repository contains the complete solution for the **Data Analyst I – Case External** challenge. 

It includes:
- An **exploratory data analysis** (EDA) of the provided transactional dataset, with interactive dashboards and statistical insights.
- A **production‑ready anti‑fraud microservice** that evaluates transactions in real time and returns an `approve` or `deny` recommendation.
- A **test client** that replays the entire dataset through the service to measure performance and effectiveness.

---

## Repository Structure

| File | Description |
|------|-------------|
| `antfraud.py` | The Flask‑based anti‑fraud service with all required endpoints. |
| `test_client.py` | Script that reads the CSV, sends each transaction to the anti‑fraud service in chronological order, and prints summary statistics. |
| `process_evaluation.py` | Python script that loads the dataset, performs feature engineering, and generates static and interactive visualisations (dashboard). |
| `transactional-sample.csv` | The provided dataset (required to run the tests). |
| `Dockerfile` | Container definition for easy deployment using Gunicorn as a production WSGI server. |
| `requirements.txt` | Python dependencies for the project. |
| `README.md` | This file. |

---

## Prerequisites

Before you begin, make sure you have the following installed on your machine:
- **Docker** (and optionally **Docker Compose**)
- **Git** (optional, for cloning)

---

## How to Run with Docker

This is the recommended way to run the application. The `Dockerfile` sets up the Python environment, installs dependencies, and runs the Flask server using **Gunicorn** (production-ready WSGI server).

### Step 1: Build the Docker Image

Open your terminal in the root directory of the project (where the `Dockerfile` is located) and run:

```bash
docker build -t antfraud-service .
```

### Step 2: Run the Docker Container

Start the container and map the container port 5000 to your local machine's port 5000:

```bash
docker run -p 5000:5000 antfraud-service

```

### Step 3: Verify the Service is Running

Once the container starts, open a new terminal window and test the health endpoint:

```bash
curl http://localhost:5000/health
```
You should see the response: {"status":"ok"}


## API Usage

### 1.Evaluate a Transaction
Send a POST request to /evaluate with the transaction data. The service will respond with an approve or deny recommendation.
Example Request (using curl):

```bash
curl -X POST http://localhost:5000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": 2342357,
    "merchant_id": 29744,
    "user_id": 97051,
    "card_number": "434505******9116",
    "transaction_date": "2019-11-31T23:16:32.812632",
    "transaction_amount": 373,
    "device_id": 285475
  }'
```
Example Response:
```bash
{
  "transaction_id": 2342357,
  "recommendation": "approve"
}
```
### 2. Register a Chargeback (Historical Data)
The anti-fraud logic considers previous chargebacks. You can simulate these by sending a POST request to /chargeback.

Example Request (using curl):
```bash
curl -X POST http://localhost:5000/chargeback \
  -H "Content-Type: application/json" \
  -d '{"user_id": 97051}'
```
Example Response:
```bash
{
  "status": "recorded",
  "user_id": 97051
}
```
Note: After this call, any future transaction from user 97051 will be denied.

## Running the Test Client
To test the service against the entire dataset (which includes historical chargebacks), run the test_client.py script. This script will sort the CSV chronologically and send each transaction to the running service.

In a new terminal, run:
```bash
python test_client.py
```
You will see a summary of how many transactions were approved/denied and how many fraudulent ones were caught.

## Running the Data Analysis (EDA)
To generate the interactive dashboard and static plots from the dataset, run:
```bash
python process_evaluation.py
```
This will generate two files:

1. fraud_dashboard.html (an interactive Plotly dashboard)

2. fraud_static_analysis.png (a static chart/heatmap)

## Rules Implemented

The anti-fraud service uses a combination of rule-based logic to make decisions:

1. Velocity Rule: Rejects transactions if a user attempts too many transactions within a specific time window (default: 5 transactions per 5 minutes).

2. Amount Limit Rule: Rejects transactions if the sum of transactions within a 24-hour window exceeds a predefined threshold (default: $1000).

3. Chargeback Rule: Rejects any transaction from a user who has previously been registered with a chargeback.

## Customizing the Configuration

You can easily adjust the thresholds and time windows in the antfraud.py file:
```bash
MAX_TRANSACTIONS_PER_WINDOW = 5        # number of tx allowed
WINDOW_SECONDS = 300                   # 5 minutes

MAX_AMOUNT_PER_WINDOW = 1000.0         # in USD
AMOUNT_WINDOW_SECONDS = 86400          # 24 hours
```

## Technologies Used

Python 3.9
Flask 2.3.2 (Web framework for API)
Pandas 2.0.3 (Data analysis)
Plotly 5.15.0 (Interactive dashboards)
Matplotlib 3.7.2 & Seaborn 0.12.2 (Static visualizations)
Requests 2.31.0 (HTTP client for testing)
Gunicorn 20.1.0 (Production WSGI server)
Docker (Containerization)
