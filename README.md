# PyChain

Just for fun

### What is blockchain?

A blockchain, originally block chain, is a growing list of records, called blocks, that are linked using cryptography. Each block contains a cryptographic hash of the previous block, a timestamp, and transaction data. By design, a blockchain is resistant to modification of the data.

[Blockchains](https://hackernoon.com/learn-blockchains-by-building-one-117428612f46)

### Docker

1. Build `docker build -t blockchain .`
2. Run `docker run --rm -p 80:5000 blockchain`

- `docker run --rm -p 81:5000 blockchain`
- `docker run --rm -p 82:5000 blockchain`

---

`POST: http://localhost:80/nodes/register`
list of nodes to register

```json
{
  "nodes": ["127.0.0.1:80", "127.0.0.1:81"]
}
```

```json
{
  "message": "New nodes have been added",
  "total_nodes": ["81", "80"]
}
```

`GET: http://localhost:80/mine`

```json
{
  "Index": 5,
  "message": "New Block Forged",
  "previous_hash": "7f15db48b4ea6479706ca61f2637cc3ad7579a473a0e03c1bc4fb18e911234eb",
  "proof": 146502,
  "transactions": [
    {
      "amount": 1,
      "recipient": "481ec20673904d3c80f7aa1b7dcc89f2",
      "sender": "0"
    }
  ]
}
```

`POST: http://localhost:80/transactions/new`

```json
{
  "sender": "43543564536543734563456",
  "recipient": "some-recipient",
  "amount": 120
}
```

## Running Tests

```
$ pytest tests/
```
