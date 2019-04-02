## General machine specifications

The machine __WILL__ have:

- Screen (not touch)
- 8 buttons (4-each side of screen)
- Card reader (magnetic and chip)
- PIN pad
- Cash Dispenser
- Printer

The machine __WILL NOT__ have:

- Touch screen
- QR Code reader
- Cash Acceptor

# Process Flow

## For a machine without a QR Code Scanner:

```mermaid
sequenceDiagram
    participant C as Customer
    participant O as Octagon
    participant P as Processor
    participant A as Athena Bitcoin
    C->>O: Insert Card, Enter PIN
    O->>A: GET /price/USD/*
    A-->>O: Price Response
    O-->>C: Menu of Options
    Note over C: Chooses Bitcoin
    C->>O: Buy Bitcoin
    O->>A: POST /transaction/start
    A-->>O: Transaction Response, w/QR Code
    O-->>C: "Scan This"
    Note over C: Gets out phone and scans QR Code using Athena Bitcoin Mobile App
    C->>A: Athena Bitcoin Mobile App submits Transaction Information

    loop Every 5 Seconds
        O->>A: POST /transaction/status
        A-->>O: Transaction Response
    end

    O-->>C: "Confirm Amount..."
    Note over C: Selects Yes, Cancel
    C->>+O: Yes
    O->>P: Debit Amount
    P-->>O: Done
    O->>A: POST /transaction/purchase
    A-->>O: Transaction Response
    O-->>-C: Print Receipt

```

# For a machine with a QR Code Scanner (ATM reads phone):

```mermaid
sequenceDiagram
    participant C as Customer
    participant O as Octagon
    participant P as Processor
    participant A as Athena Bitcoin
    C->>O: Insert Card, Enter PIN
    O->>A: GET /price/USD/*
    A-->>O: Price Response
    O-->>C: Menu of Options
    Note over C: Chooses Bitcoin
    C->>O: Buy Bitcoin
    O->>A: POST /transaction/start
    A-->>O: Transaction Response
    O-->>C: "Scan address..."
    Note over C: Gets out phone and scans QR Code
    C->>O: Scan of QR Code
    O->>A: POST /transaction/crypto_address
    A-->>O: Transaction Response
    O-->>C: "Enter Amount..."
    Note over C: Types in amount of USD
    C->>+O: Amount
    O->>P: Debit Amount
    P-->>O: Done
    O->>A: POST /transaction/purchase
    A-->>O: Transaction Response
    O-->>-C: Print Receipt
```

## 