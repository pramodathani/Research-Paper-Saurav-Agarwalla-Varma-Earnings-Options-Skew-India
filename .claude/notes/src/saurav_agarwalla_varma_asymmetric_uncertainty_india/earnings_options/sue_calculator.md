# sue_calculator.py

- Equations 2 to 4: expected EPS is the EPS four quarters ago plus the mean of the last eight year-on-year changes. The standard deviation is the sample standard deviation (n - 1) of the previous eight quarters' surprises. The paper does not say n or n - 1.
- A quarter needs 20 quarters of history: eight surprises, each of which needs eight changes, each of which needs a quarter four back. A gap gives NaN and is not filled.
- sue_alternative divides by the standard deviation of the previous eight year-on-year changes, which needs only 12 quarters, and is a sensitivity for firms with gaps.
