import pandas as pd

# Load the CSV files into pandas dataframes
staked_events = pd.read_csv('mor_distribution_events/user_staked_events.csv')
withdrawn_events = pd.read_csv('mor_distribution_events/user_withdrawn_events.csv')
claimed_events = pd.read_csv('mor_distribution_events/user_claimed_events.csv')
mor_balances = pd.read_csv('mor_distribution_events/mor_balances.csv')

# Convert timestamp columns to datetime for further analysis
staked_events['Timestamp'] = pd.to_datetime(staked_events['Timestamp'])
withdrawn_events['Timestamp'] = pd.to_datetime(withdrawn_events['Timestamp'])
claimed_events['Timestamp'] = pd.to_datetime(claimed_events['Timestamp'])

# Convert stETH and MOR values by dividing by 10^18
staked_events['amount'] = staked_events['amount'].astype(float) / 10**18
withdrawn_events['amount'] = withdrawn_events['amount'].astype(float) / 10**18
claimed_events['amount'] = claimed_events['amount'].astype(float) / 10**18
mor_balances['mor_balance'] = mor_balances['mor_balance'].astype(float) / 10**18

# Group by user and aggregate their staking, withdrawing, and claiming actions
staked_summary = staked_events.groupby('user').agg(
    total_staked=('amount', 'sum'),
    staked_count=('amount', 'count')
).reset_index()

withdrawn_summary = withdrawn_events.groupby('user').agg(
    total_withdrawn=('amount', 'sum'),
    withdrawn_count=('amount', 'count')
).reset_index()

claimed_summary = claimed_events.groupby('user').agg(
    total_mor_claimed=('amount', 'sum'),
    claim_count=('amount', 'count')
).reset_index()

# Merge all summaries into a single dataframe based on 'user'
user_summary = pd.merge(staked_summary, withdrawn_summary, on='user', how='outer')
user_summary = pd.merge(user_summary, claimed_summary, on='user', how='outer')

# Add MOR balances to the summary
user_summary = pd.merge(user_summary, mor_balances, left_on='user', right_on='address', how='left')

# Fill missing values with 0 for users with no activity in some columns
user_summary.fillna(0, inplace=True)

# Drop the redundant address column
user_summary.drop(columns=['address'], inplace=True)

# Save the summary to a CSV file
user_summary.to_csv('mor_distribution_events/user_activity_summary.csv', index=False)

# Display or print the summary
print(user_summary)
