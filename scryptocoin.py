"""
Created on Wed Jul  4 17:20:33 2018

@author: Svanjaarsveld
"""

# Module 2 - Create a crypto currency

import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Part 1 - Build a Blockchain

class Blockchain:
    
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, prev_hash = '0')
        self.nodes = set()
    
    def create_block(self, proof, prev_hash):
        block = {'index' : len(self.chain) + 1,
                 'timestamp' : str(datetime.datetime.now()),
                 'proof' : proof,
                 'prev_hash' : prev_hash,
                 'transactions' : self.transactions
                 }
        
        self.transactions = []        
        self.chain.append(block)
        
        return block
    
    def get_prev_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, prev_proof):
        new_proof = 1
        check_proof = False
        
        while not check_proof:
            hash_operation = hashlib.sha256(str(new_proof**2 - prev_proof**2)\
                                            .encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
                
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        prev_block = chain[0]
        block_index = 1
        
        while block_index < len(chain):
            block = chain[block_index]
            if block['prev_hash'] != self.hash(prev_block):
                return False
            # Get the proof of the previous and current blocks to
            # perform hash operation
            prev_proof = prev_block['proof']
            cur_proof = block['proof']
            hash_operation = hashlib.sha256(str(cur_proof**2 - prev_proof**2)\
                                            .encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            
            prev_block = block
            block_index += 1
            
        return True
    
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender' : sender,
                                  'receiver' : receiver,
                                  'amount' : amount
                                  })
            
        prev_block = self.get_prev_block()
        
        return prev_block['index'] + 1
    
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        
        if longest_chain:
            self.chain = longest_chain
            return True
        
        return False
    

# Part 2 - Mining our Blockchain
        
# Creating a Web App
app = Flask(__name__)

# Creating an address for the node on Port 5000
node_address = str(uuid4()).replace('-', '')
    
# Creating a Blockchain
blockchain = Blockchain()

# Mining a new block
# Update the receiver to the relevant node username
@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_prev_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(node_address, 'Stephan', 10)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congratulations on mining a new block',
                'index' : block['index'],
                'timestamp' : block['timestamp'],
                'proof' : block['proof'],
                'prev_hash' : block['prev_hash'],
                'transactions' : block['transactions']}
    
    return jsonify(response), 200


# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain' : blockchain.chain,
                'length' : len(blockchain.chain)}
    
    return jsonify(response), 200


# Check if the Blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message' : 'All systems go. The Blockchain is valid.'}
    else:
        response = {'message' : 'Houston, we have a problem. The Blockchain is not valid.'}
        
    return jsonify(response), 200

# Adding a new transaction to the Blockchain
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all (key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    
    index = blockchain.add_transaction(json['sender'], json['receiver'],
                                       json['amount'])
    response = {'message': f'This transaction will be added to Block {index}.'}
    
    return jsonify(response), 201

# Part 3 - Decentralizing our Blockchain
    
# Connecting new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'No nodes were found', 400
    
    for node in nodes:
        blockchain.add_node(node)
        
    response = {'message' : 'All the nodes are now connected. The Scrypto Coin Blockchain now contains the following nodes:',
                'node_list' : list(blockchain.nodes)}
    
    return jsonify(response), 201

@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message' : 'The relevant node''s chain was replaced with the longest version of the blockchain',
                    'longest_chain' : blockchain.chain}
    else:
        response = {'message' : 'This chain matches the longest version of the blockchain',
                    'longest_chain' : blockchain.chain}
        
    return jsonify(response), 200

# Running the app
# Update the port address to the relevant node's port number
app.run(host = '0.0.0.0', port = 5001)
