import hashlib
import json
from time import time
from typing import Optional
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request


class BlockChainException(Exception):
    pass


class BlockChain(object):
    def __init__(self):
        self.chain = []
        self.nodes = set()
        self.secure = False
        self.current_transactions = []

        # genesis block
        self.new_block(previous_hash='1', proof=100)

    def new_block(
            self,
            proof: int,
            previous_hash: Optional[str] = None
    ) -> dict:
        """
        Create a new block on the Blockchain
        :param proof: The proof given by the Proof of work Algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block dict
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        # reset list the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(
            self,
            sender: str,
            recipient: str,
            amount: int
    ) -> int:
        """
        Creates a new transaction to go into the next mined Block
        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })
        return self.last_block['index'] + 1

    def proof_of_work(self, last_block: dict) -> int:
        """
        Simple Proof of Work Algorithm
        - Find a number p' such that hash(pp') contains leading 4 zeros, where p is the previous p`
        - p is the previous proof, and p' is the new proof
        :param last_block: Previous Block
        :return: proof
        """
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    def register_node(self, address: str) -> None:
        """
        Add a new node to the list of nodes
        :param address: address of the node. 'http://192.168.0.5:5000'
        :return:
        """
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def valid_chain(self, chain: list) -> bool:
        """
        Determine if a given Blockchain is valid
        :param chain: A Blockchain
        :return: True if valid, False if not
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print('{}'.format(last_block))
            print('{}'.format(block))
            print('\n------------\n')

            last_block_hash = self.hash(last_block)

            if block['previous_hash'] != self.hash(last_block_hash):
                return False

            if not self.valid_proof(last_block['proof'], block['proof'], block['previous_hash']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self) -> bool:
        """
        Consensus Algorithm: it resolves conflicts by replacing our chain
        with the longest one in the network
        :return: True if our chain was replaced, False if not
        """

        neighbors = self.nodes
        new_chain = None

        max_length = len(self.chain)
        for node in neighbors:
            try:
                response = requests.get(
                    'http://{node}/chain'.format(node=node))

                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain
            except requests.exceptions.ConnectionError:
                raise BlockChainException(
                    'Node: {node} is not responding'.format(node=node)
                )

        if new_chain:
            self.chain = new_chain
            return True

        return False

    @property
    def last_block(self):
        # returns the last block in the chain
        return self.chain[-1]

    @staticmethod
    def hash(block) -> str:
        """
        Creates a SHA-256 hash of a block
        :param block: Block
        :return: Block hash
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
    def valid_proof(last_proof: int, proof: int, last_hash: str) -> bool:
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeros?
        :param last_proof: Previous Proof
        :param proof: Current Proof
        :param last_hash: Hash of previous block
        :return: True if correct, False if not
        """
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'


# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = BlockChain()


@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    blockchain.new_transaction(
        sender='0',
        recipient=node_identifier,
        amount=1
    )

    # forge new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': 'New Block Forged',
        'Index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json(force=True)

    # check the the required fields are in the POST data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # create a new Transaction
    index = blockchain.new_transaction(
        values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_node():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return 'Error: Please supply a valid node list', 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': len(blockchain.nodes)
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Chain replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Chain authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000,
                        type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)
