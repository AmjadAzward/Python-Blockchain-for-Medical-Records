import hashlib
import time
import json
from datetime import datetime


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions  # list of dicts
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_data = {
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }
        block_string = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def __repr__(self):
        return f"Block(index={self.index}, hash={self.hash}, prev_hash={self.previous_hash})"


class Blockchain:
    def __init__(self, difficulty=3, max_tx_per_block=5):
        self.chain = [self.create_genesis_block()]
        self.difficulty = difficulty
        self.pending_transactions = []
        self.balances = {}  # wallet address -> balance
        self.max_tx_per_block = max_tx_per_block

    def create_genesis_block(self):
        return Block(0, [], time.time(), "0")

    def get_latest_block(self):
        return self.chain[-1]

    def get_balance(self, wallet):
        return self.balances.get(wallet, 0)

    def add_transaction(self, sender, receiver, data, amount=0):
        # Check balance if amount > 0 and sender is not "SYSTEM"
        if amount > 0 and sender != "SYSTEM":
            if self.get_balance(sender) < amount:
                print(f"Transaction failed: {sender} has insufficient balance.")
                return False

        tx = {
            "sender": sender,
            "receiver": receiver,
            "data": data,
            "amount": amount,
            "timestamp": time.time()
        }
        self.pending_transactions.append(tx)
        print(f"Transaction added: {tx}")
        return True

    def mine_pending_transactions(self, miner_address):
        if not self.pending_transactions:
            print("No transactions to mine.")
            return

        # Limit transactions per block
        tx_to_mine = self.pending_transactions[:self.max_tx_per_block]
        block = Block(
            index=len(self.chain),
            transactions=tx_to_mine,
            timestamp=time.time(),
            previous_hash=self.get_latest_block().hash
        )

        self.proof_of_work(block)
        self.chain.append(block)
        print(f"Block #{block.index} mined by {miner_address} with {len(tx_to_mine)} txs.")

        # Update balances based on mined transactions
        for tx in tx_to_mine:
            sender = tx["sender"]
            receiver = tx["receiver"]
            amount = tx.get("amount", 0)

            if sender != "SYSTEM":
                self.balances[sender] = self.balances.get(sender, 0) - amount
            self.balances[receiver] = self.balances.get(receiver, 0) + amount

        # Reward miner with fixed amount
        reward_amount = 10
        reward_tx = {
            "sender": "SYSTEM",
            "receiver": miner_address,
            "data": "Mining Reward",
            "amount": reward_amount,
            "timestamp": time.time()
        }
        self.pending_transactions = self.pending_transactions[self.max_tx_per_block:]  # remove mined txs
        self.pending_transactions.append(reward_tx)

        # Update balance for reward immediately
        self.balances[miner_address] = self.balances.get(miner_address, 0) + reward_amount

    def proof_of_work(self, block):
        print("Mining block...")
        while block.hash[:self.difficulty] != "0" * self.difficulty:
            block.nonce += 1
            block.hash = block.calculate_hash()
        print(f"Block mined: {block.hash}")

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i - 1]

            if current.hash != current.calculate_hash():
                print("Hash mismatch!")
                return False
            if current.previous_hash != prev.hash:
                print("Previous hash mismatch!")
                return False
        return True

    def print_chain(self):
        for block in self.chain:
            print(json.dumps({
                "index": block.index,
                "hash": block.hash,
                "prev_hash": block.previous_hash,
                "timestamp": datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                "transactions": block.transactions
            }, indent=4))

    def save_chain(self, filename):
        with open(filename, "w") as f:
            json.dump([block.__dict__ for block in self.chain], f, indent=4)
        print(f"Blockchain saved to {filename}")

    def load_chain(self, filename):
        with open(filename, "r") as f:
            blocks = json.load(f)
        self.chain = []
        for b in blocks:
            block = Block(
                b['index'],
                b['transactions'],
                b['timestamp'],
                b['previous_hash'],
                b['nonce']
            )
            block.hash = b['hash']
            self.chain.append(block)
        print(f"Blockchain loaded from {filename}")


# Example usage with enhanced features
blockchain = Blockchain()

# Initial balances
blockchain.balances["Patient A"] = 100
blockchain.balances["Patient B"] = 50
blockchain.balances["Dr. Brown"] = 0
blockchain.balances["Dr. Green"] = 0
blockchain.balances["Hospital_A"] = 0

# Add transactions with amounts (simulate payment for record storage)
blockchain.add_transaction("Patient A", "Dr. Brown", "Blood Test Results: Normal", amount=10)
blockchain.add_transaction("Patient A", "Dr. Green", "X-Ray Results: No issues", amount=5)

# Mine pending transactions
blockchain.mine_pending_transactions("Hospital_A")

# Add more transactions
blockchain.add_transaction("Patient B", "Dr. Brown", "MRI Result: Normal", amount=15)

# Mine again
blockchain.mine_pending_transactions("Hospital_A")

# Print full chain with readable timestamps
blockchain.print_chain()

# Check balances
print("Balances:", blockchain.balances)

# Verify chain validity
print("Blockchain valid:", blockchain.is_chain_valid())

# Save and load chain (optional)
blockchain.save_chain("medical_chain.json")
blockchain.load_chain("medical_chain.json")
