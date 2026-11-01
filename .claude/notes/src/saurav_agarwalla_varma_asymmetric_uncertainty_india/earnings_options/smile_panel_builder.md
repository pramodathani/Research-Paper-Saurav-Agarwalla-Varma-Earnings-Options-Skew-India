# smile_panel_builder.py

- The series used on a day is the nearest expiry strictly after that day for which a stock future traded, and the forward is that expiry's futures price. On an expiry day the next series is used, because T would be zero.
- The panel is built for every stock-day, not only event days, so Table 5 and the pre-event normalisation can use whole months.
- Run in 12 x 12 month tasks in parallel. Each task reads one yearly parquet file.
