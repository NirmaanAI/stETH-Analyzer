# stETH Analyzer for MOR Contributors

### 1) `user_staked_events.csv`:
- Represents: Users staking stETH in the MOR protocol on Ethereum mainnet.
- Contains: Timestamp, transaction hash, block number, user address, pool ID, and staked amount.
- Significance: Shows who has deposited stETH into the MOR system and when.
  
### 2) `user_withdrawn_events.csv`:
- Represents: Users withdrawing their staked stETH from the MOR protocol on Ethereum mainnet.
- Contains: Timestamp, transaction hash, block number, user address, pool ID, and withdrawn amount.
- Significance: Indicates users who have removed their stETH from the system, potentially reducing their MOR rewards.
  
### 3) `user_claimed_events.csv`:
- Represents: Users claiming their MOR token rewards on Ethereum mainnet.
- Contains: Timestamp, transaction hash, block number, user address, pool ID, claimed amount, and receiver address.
- Significance: Shows when and how much MOR tokens users have claimed as rewards for staking stETH.

### 5) `mor_balances.csv`:
- Represents: Current MOR token balances of users on the Arbitrum network.
- Contains: User address and their MOR token balance.
- Significance: Provides a snapshot of how much MOR each user holds on Arbitrum after claiming and potentially trading.

### NOTE:
A `user_Activity_Summary` spreadsheet displaying key details for each user, including total stETH deposited, withdrawn, MOR claimed, and their current MOR balance. You can now analyze users' behaviors based on these metrics.

Q. How to Interpret? :
- `Frequent Claims + Withdrawals = Farming/Dumping behavior`
- `Frequent Staking + Low Withdrawals + Claiming = DCA behavior`
