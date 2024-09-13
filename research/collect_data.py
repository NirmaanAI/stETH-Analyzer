import os
from web3 import Web3
import csv
from datetime import datetime
import logging
from web3.middleware import geth_poa_middleware
import json

# Configuration
RPC_URL = ""  # Replace with your actual Infura project ID or other Ethereum node URL
# Arbitrum RPC URL - replace with your own if you have one
ARBITRUM_RPC_URL = ""

BATCH_SIZE = 1000000

# Contract Addresses
SUPPLY_PROXY_ADDRESS = "0x6CFe1dDfd88890E08276c7FA9D6DCa1cA4A224a9"
DISTRIBUTION_PROXY_ADDRESS = "0x47176B2Af9885dC6C4575d4eFd63895f7Aaa4790"
MOR_MAINNET_ADDRESS = "0xcbb8f1bda10b9696c57e13bc128fe674769dcec0"
MOR_ARBITRUM_ADDRESS = "0x092bAaDB7DEf4C3981454dD9c0A0D7FF07bCFc86"
STETH_TOKEN_ADDRESS = '0x5300000000000000000000000000000000000004'
UNISWAP_V3_POSITIONS_NFT_ADDRESS = '0xC36442b4a4522E871399CD717aBDD847Ab11FE88'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load ABI
with open('distribution_abi.json', 'r') as abi_file:
    distribution_abi = json.load(abi_file)

class MOREventProcessor:
    def __init__(self, output_dir):
        self.web3 = Web3(Web3.HTTPProvider(RPC_URL))
        self.contract = self.web3.eth.contract(address=DISTRIBUTION_PROXY_ADDRESS, abi=distribution_abi)
        self.output_dir = output_dir
        
        # Store contract addresses for potential future use
        self.addresses = {
            'SUPPLY_PROXY': SUPPLY_PROXY_ADDRESS,
            'DISTRIBUTION_PROXY': DISTRIBUTION_PROXY_ADDRESS,
            'MOR_MAINNET': MOR_MAINNET_ADDRESS,
            'MOR_ARBITRUM': MOR_ARBITRUM_ADDRESS,
            'STETH_TOKEN': STETH_TOKEN_ADDRESS,
            'UNISWAP_V3_POSITIONS_NFT': UNISWAP_V3_POSITIONS_NFT_ADDRESS
        }
        
        # Determine the start block
        self.start_block = self.get_contract_deployment_block()

    def get_contract_deployment_block(self):
        # This is a placeholder. You should replace this with the actual deployment block
        # or the block where events started occurring.
        return 15000000  # Example block number, replace with actual value

    def get_events_in_batches(self, start_block, end_block, event_name):
        current_start = start_block
        while current_start <= end_block:
            current_end = min(current_start + BATCH_SIZE, end_block)
            try:
                yield from self.contract.events[event_name].get_logs(fromBlock=current_start, toBlock=current_end)
            except Exception as e:
                logger.error(f"Error getting events from block {current_start} to {current_end}: {str(e)}")
            current_start = current_end + 1

    def write_to_csv(self, events, filename, headers):
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            for event in events:
                row = {
                    'Timestamp': datetime.fromtimestamp(self.web3.eth.get_block(event['blockNumber'])['timestamp']).isoformat(),
                    'TransactionHash': event['transactionHash'].hex(),
                    'BlockNumber': event['blockNumber']
                }
                row.update(event['args'])
                writer.writerow(row)
        logger.info(f"CSV file {filename} has been created successfully.")

    def get_event_headers(self, event_name):
        event_abi = next((e for e in self.contract.abi if e['type'] == 'event' and e['name'] == event_name), None)
        if not event_abi:
            raise ValueError(f"Event {event_name} not found in ABI")
        return ['Timestamp', 'TransactionHash', 'BlockNumber'] + [input['name'] for input in event_abi['inputs']]

    def process_events(self, event_name, output_filename):
        try:
            latest_block = self.web3.eth.get_block('latest')['number']
            headers = self.get_event_headers(event_name)
            events = list(self.get_events_in_batches(self.start_block, latest_block, event_name))
            logger.info(f"Processing {len(events)} {event_name} events from block {self.start_block} to {latest_block}")

            if events:
                self.write_to_csv(events, output_filename, headers)
            else:
                logger.info(f"No events found for {event_name}.")

        except Exception as e:
            logger.error(f"An error occurred in process_events: {str(e)}")
            logger.exception("Exception details:")

def create_csv_mainnet():
    output_dir = 'mor_distribution_events'
    os.makedirs(output_dir, exist_ok=True)
    
    processor = MOREventProcessor(output_dir)
    
    # Process UserStaked events (stake - stETH)
    processor.process_events("UserStaked", "user_staked_events.csv")
    
    # Process UserWithdrawn events (withdraw - stETH)
    processor.process_events("UserWithdrawn", "user_withdrawn_events.csv")
    
    # Process UserClaimed events (UserClaimed: Mor)
    processor.process_events("UserClaimed", "user_claimed_events.csv")


with open("erc_20_abi.json", 'r') as file:
     erc20_abi = json.load(file)

def setup_web3():
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC_URL))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

def get_mor_balance(w3, contract, address):
    balance = contract.functions.balanceOf(address).call()
    #decimals = contract.functions.decimals().call()
    return balance #/ (10 ** decimals)


def process_csv_mor(input_file, output_file):
    w3 = setup_web3()
    mor_contract = w3.eth.contract(address=MOR_ARBITRUM_ADDRESS, abi=erc20_abi)

    unique_addresses = set()
    balances = {}

    # Read input CSV and collect unique addresses
    with open(input_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            address = row['receiver']
            unique_addresses.add(address)

    # Get MOR balance for each unique address
    print("total address")
    print(len(unique_addresses))
    for address in unique_addresses:
        print(address)
        try:
            balance = get_mor_balance(w3, mor_contract, address)
            balances[address] = balance
        except Exception as e:
            print(f"Error getting balance for {address}: {str(e)}")
            balances[address] = "Error"

    # Write to output CSV
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['address', 'mor_balance']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for address, balance in balances.items():
            writer.writerow({'address': address, 'mor_balance': balance})

    print(f"Processed {len(unique_addresses)} unique addresses. Results written to {output_file}")
    
def create_mor_balance():
    input_file = "mor_distribution_events/user_claimed_events.csv"  # Replace with your input CSV file name
    output_file = "mor_distribution_events/mor_balances.csv"
    process_csv_mor(input_file, output_file)

UNISWAP_V3_MOR_ETH_POOL = "0xE5Cf22EE4988d54141B77050967E1052Bd9c7F7A"  # Replace with actual pool address

with open("pool_uniswap_abi.json", 'r') as file:
    uniswap_pool_abi = json.load(file)

def check_mor_sales_on_uniswap(w3, pool_contract, start_block, end_block, mor_holders):
    swap_event = pool_contract.events.Swap()
    
    sales = []
    for event in swap_event.get_logs(fromBlock=start_block, toBlock=end_block):
        sender = event['args']['sender']
        amount0 = event['args']['amount0']
        amount1 = event['args']['amount1']
        
        # Assuming MOR is token0 in the pool, adjust if it's token1
        if sender in mor_holders and amount0 < 0:
            sales.append({
                'address': sender,
                'amount_sold': abs(amount0) / (10 ** 18),  # Adjust decimals if needed
                'timestamp': datetime.fromtimestamp(w3.eth.get_block(event['blockNumber'])['timestamp']).isoformat(),
                'transaction_hash': event['transactionHash'].hex()
            })
    
    return sales

def process_uniswap_sales(input_file, output_file):
    w3 = setup_web3()
    pool_contract = w3.eth.contract(address=UNISWAP_V3_MOR_ETH_POOL, abi=uniswap_pool_abi)

    # Read MOR holders from input file
    mor_holders = set()
    with open(input_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            mor_holders.add(row['address'])

    # Get the current block number
    latest_block = w3.eth.get_block('latest')['number']
    
    # You might want to adjust the start_block based on when the pool was created
    start_block = latest_block - 1000000  # Example: check last 100000 blocks

    sales = check_mor_sales_on_uniswap(w3, pool_contract, start_block, latest_block, mor_holders)

    # Write sales to output CSV
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['address', 'amount_sold', 'timestamp', 'transaction_hash']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for sale in sales:
            writer.writerow(sale)

    print(f"Processed {len(sales)} MOR sales on Uniswap. Results written to {output_file}")

def uniswap_sales():
    # Check for MOR sales on Uniswap
    input_file = "mor_distribution_events/mor_balances.csv"
    output_file = "mor_distribution_events/mor_uniswap_sales.csv"
    process_uniswap_sales(input_file, output_file)
uniswap_sales()