# table_one_example.py

- Recomputes Table 1 (page 465). The scenario's spot is the mixture mean, and the option price is the weighted price on three lognormal components, because the risk-neutral price is linear in the density.
- The paper's text writes the OTM strike of column 3 as 99 x (1 + 0.3137/52), but its table, and the formula, need the column's own ATM-IV of 0.3178. The test follows the table.
