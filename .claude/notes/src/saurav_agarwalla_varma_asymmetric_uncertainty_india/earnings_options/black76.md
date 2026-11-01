# black76.py

- Prices on the futures price (Black 1976), as the paper does, so no dividend yield or cost of carry is needed.
- The call delta is N(d1) without the discount factor. A put's delta plus one equals the same number, which is how the paper turns put deltas into call deltas (page 463). Discounting would only scale it by exp(-rT), about 0.5 percent for a month.
- Implied volatility is found by 60 bisection steps on all contracts at once. That is slower than Newton's method but cannot fail to converge. Prices outside Black's bounds, or at the edge of the volatility range, give NaN, which is the paper's arbitrage filter.
