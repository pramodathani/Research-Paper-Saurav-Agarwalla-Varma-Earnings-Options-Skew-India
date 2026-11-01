# smile_fit.py

- The paper says a and c are non-negative and that c is shifted by b^2/4a when the vertex lies in [0, 1], and by min(0, a + b) otherwise. The code reads this as: the raw level is at least zero, and the shift is then added so the smile cannot go below zero anywhere on [0, 1]. The outer-vertex case adds -min(0, a + b), which keeps the IV at delta 1 non-negative.
- Nelder-Mead starts from a weighted least squares fit, clipped to a >= 0 and c >= 0.
- The paper weights by the log of traded value 'recursively', which is not explained. The code uses the log of notional value as a fixed weight. The squared error is in IV by default and in premium as a sensitivity, because the paper says 'between the options market price and the estimated prices'.
