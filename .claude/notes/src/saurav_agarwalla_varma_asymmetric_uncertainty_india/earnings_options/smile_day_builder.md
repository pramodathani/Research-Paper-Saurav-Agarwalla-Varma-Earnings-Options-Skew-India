# smile_day_builder.py

- The five-minute filter needs intraday data, so a contract must instead have traded at least N contracts in the day (5 by default; 1 and 20 are sensitivities).
- At least seven valid contracts with one call and one put, as in the paper (page 463).
- The alternative smile follows Xing, Zhang and Zhao: OTM when K/F (call) or F/K (put) is 1.05 to 1.20, ATM when 0.95 to 1.05, volume-weighted by contracts traded. Alt RR-IV is OTM call IV minus OTM put IV, so it has the same sign as RR-IV.
