import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns

# 1. LOAD AND PREPARE DATA
file_path = "transactional-sample.csv"
df = pd.read_csv(file_path)

# Convert date column
df['transaction_date'] = pd.to_datetime(df['transaction_date'])

# Robust conversion of has_cbk (strings 'TRUE'/'FALSE' to boolean)
df['has_cbk'] = df['has_cbk'].astype(str).str.upper() == 'TRUE'

# Extract time features
df['hour'] = df['transaction_date'].dt.hour
df['day_of_week'] = df['transaction_date'].dt.day_name()
df['date'] = df['transaction_date'].dt.date

# Flag missing device IDs
df['device_missing'] = df['device_id'].isna() | (df['device_id'] == '')


# 2. INTERACTIVE DASHBOARD WITH PLOTLY
# Create subplots with proper type specification
fig = make_subplots(
    rows=2, cols=2,
    specs=[
        [{'type': 'xy'}, {'type': 'xy'}],
        [{'type': 'xy'}, {'type': 'domain'}]   # <-- allows pie chart
    ],
    subplot_titles=(
        "Transactions by Hour of Day (Fraud vs. Legitimate)",
        "Top 10 Merchants by Chargeback Rate",
        "Transaction Amount Over Time (Fraud Highlighted)",
        "Device ID Presence"
    )
)

# Graph 1: Hourly histogram (Fraud vs Legitimate)
hourly_cbk = df[df['has_cbk'] == True].groupby('hour').size().reset_index(name='count_cbk')
hourly_normal = df[df['has_cbk'] == False].groupby('hour').size().reset_index(name='count_normal')
hourly_merged = pd.merge(hourly_cbk, hourly_normal, on='hour', how='outer').fillna(0)

fig.add_trace(
    go.Bar(
        x=hourly_merged['hour'],
        y=hourly_merged['count_cbk'],
        name='Fraud (has_cbk)',
        marker_color='red'
    ),
    row=1, col=1
)
fig.add_trace(
    go.Bar(
        x=hourly_merged['hour'],
        y=hourly_merged['count_normal'],
        name='Legitimate',
        marker_color='blue',
        opacity=0.6
    ),
    row=1, col=1
)

# Graph 2: Top 10 merchants by chargeback rate (with min volume)
MIN_TRANSACTIONS = 20

merchant_risk = df.groupby('merchant_id').agg(
    total=('transaction_id', 'count'),
    frauds=('has_cbk', 'sum')
).reset_index()

# Filter merchants with minimum volume
merchant_risk = merchant_risk[merchant_risk['total'] >= MIN_TRANSACTIONS]

merchant_risk['fraud_rate'] = (merchant_risk['frauds'] / merchant_risk['total']) * 100
top_merchants = merchant_risk.sort_values('fraud_rate', ascending=False).head(10)

fig.add_trace(
    go.Bar(
        y=top_merchants['merchant_id'].astype(str),
        x=top_merchants['fraud_rate'],
        text=top_merchants['fraud_rate'].round(2),
        textposition='outside',
        marker_color='orange',
        name='Chargeback Rate (%)',
        orientation='h'
    ),
    row=1, col=2
)

fig.update_xaxes(title_text="Fraud Rate (%)", row=1, col=2)
fig.update_yaxes(title_text="Merchant ID", row=1, col=2)

# Graph 3: Scatter plot (Amount vs Time)
fig.add_trace(
    go.Scatter(
        x=df[df['has_cbk'] == True]['transaction_date'],
        y=df[df['has_cbk'] == True]['transaction_amount'],
        mode='markers',
        name='With Chargeback',
        marker=dict(color='red', size=8, opacity=0.7)
    ),
    row=2, col=1
)
fig.add_trace(
    go.Scatter(
        x=df[df['has_cbk'] == False]['transaction_date'],
        y=df[df['has_cbk'] == False]['transaction_amount'],
        mode='markers',
        name='Without Chargeback',
        marker=dict(color='blue', size=5, opacity=0.3)
    ),
    row=2, col=1
)

# Graph 4: Pie chart for device presence
device_counts = df['device_missing'].value_counts().reset_index()
device_counts.columns = ['missing', 'count']
device_counts['label'] = device_counts['missing'].map(
    {True: 'Missing Device ID', False: 'Valid Device ID'}
)

fig.add_trace(
    go.Pie(
        labels=device_counts['label'],
        values=device_counts['count'],
        hole=0.4,
        marker_colors=['#FF6B6B', '#4ECDC4'],
        name='Device'
    ),
    row=2, col=2
)

# Update layout
fig.update_layout(height=800, width=1200, title_text="Fraud Analysis Dashboard")
fig.update_xaxes(title_text="Hour of Day", row=1, col=1)
fig.update_yaxes(title_text="Number of Transactions", row=1, col=1)
fig.update_xaxes(title_text="Merchant ID", row=1, col=2)
fig.update_yaxes(title_text="Fraud Rate (%)", row=1, col=2)
fig.update_xaxes(title_text="Date/Time", row=2, col=1)
fig.update_yaxes(title_text="Transaction Amount ($)", row=2, col=1)

# Save interactive dashboard
fig.write_html("fraud_dashboard.html")
print("Dashboard saved as 'fraud_dashboard.html'")


# 3. STATIC VISUALIZATIONS (MATPLOTLIB + SEABORN)
plt.figure(figsize=(12, 6))

# Boxplot of transaction amounts
plt.subplot(1, 2, 1)
sns.boxplot(x='has_cbk', y='transaction_amount', data=df, hue='has_cbk', palette=['blue', 'red'], legend=False)
plt.title('Distribution of Amounts by Chargeback')
plt.xlabel('Has Chargeback')
plt.ylabel('Amount ($)')
plt.yscale('log')

# Correlation heatmap
plt.subplot(1, 2, 2)
df['device_missing_num'] = df['device_missing'].astype(int)
corr = df[['transaction_amount', 'has_cbk', 'device_missing_num']].corr()
sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f')
plt.title('Correlation Matrix')

plt.tight_layout()
plt.savefig('fraud_static_analysis.png', dpi=300)
plt.show()


# 4. VELOCITY ANALYSIS (RAPID TRANSACTIONS)
df_sorted = df.sort_values(['user_id', 'transaction_date'])
df_sorted['time_diff'] = df_sorted.groupby('user_id')['transaction_date'].diff().dt.total_seconds() / 60  # minutes

# Flag transactions with less than 5 minutes between them (same user)
rapid_users = df_sorted[df_sorted['time_diff'] < 5]
print(f"Suspicious rapid transactions (less than 5 minutes apart): {len(rapid_users)}")

# Export list
rapid_users.to_csv("rapid_transactions_alert.csv", index=False)
print("List of rapid transactions saved to 'rapid_transactions_alert.csv'")