# eps_panel_builder.py

- The earliest standalone announcement of each symbol and period is the event. Later rows are re-filings.
- EPS is put on the share basis after every later split and bonus by multiplying by the product of their factors. SUE is scale free, so any common basis works.
- Standalone EPS is the only series complete across 2010-2025, because consolidated quarterly results were optional before April 2019.
- The results API's broadcast time is the time of the structured filing, which can be weeks after the announcement. use_announcement_times replaces it with the announcement feed's time when that is for the same period, not before the period ended, and not more than a day after the structured filing.
