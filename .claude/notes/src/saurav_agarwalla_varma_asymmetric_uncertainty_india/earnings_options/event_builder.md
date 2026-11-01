# event_builder.py

- Day 0 follows the paper (page 468): an announcement at or after 15:30, or on a day with no trading, belongs to the next trading day.
- Events within three trading days of the near-month expiry are dropped (page 468). The paper says 'less than three days before the expiry day' and the code counts trading days between day 0 and expiry, keeping three.
- An event needs options trading on day 0, which stands in for 'a firm with derivatives'.
