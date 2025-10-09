# API Usage
- Retrieve: `GET /v1/agent/ask?tool=retrieve_docs&q=your+question`
- Prices: `GET /v1/fetch_data/prices?symbol=SPY&freq=D`
- Prices + validation: `GET /v1/fetch_data/prices_with_validation?symbol=macro.cpi&freq=M`
Notes: tools are registered in the agent registry; `retrieve_docs` loads its index from `var/index/<name>/` (default: `default`).
