"""The numbers printed in the paper, for comparison with the recreation."""


class PaperValues:
    """Holds the paper's SUE columns and Table 5, with their pages.

    Regression entries map a variable to its coefficient and standard error.
    """

    TABLE_5_PAGE = 471
    TABLE_5 = {
        'atm_iv': (0.383, 0.411, 0.372, 0.028, 6.70, 0.038, 10.84),
        'iv_75': (0.397, 0.427, 0.391, 0.030, 6.42, 0.036, 9.13),
        'iv_25': (0.397, 0.422, 0.388, 0.024, 5.59, 0.034, 9.21),
    }
    SAMPLE = {
        'firm_quarters': 2081,
        'firms': 191,
        'sue_observations': 1831,
        'page': 468,
    }
    REGRESSIONS = {
        ('Table 6', '(1)'): {
            'page': 479,
            'RR-IV': (2.168, 0.594),
            'P/C': (-1.078, 0.388),
            'ATM-IV': (0.649, 0.336),
            'beta': (0.144, 0.142),
            'momentum': (-0.140, 0.085),
            'size': (0.305, 0.110),
            'bhar': (1.074, 0.547),
            'observations': 1729,
            'adjusted_r2': 0.028,
        },
        ('Table 6', '(2)'): {
            'page': 479,
            'RR-IV': (2.514, 0.634),
            'P/C': (-1.149, 0.397),
            'ATM-IV': (0.416, 0.362),
            'beta': (0.185, 0.148),
            'momentum': (-0.039, 0.094),
            'size': (0.190, 0.121),
            'bhar': (0.760, 0.552),
            'observations': 1729,
            'adjusted_r2': 0.038,
        },
        ('Table 7', 'n=2'): {
            'page': 480,
            'RR-IV': (0.673, 1.026),
            'P/C': (-0.700, 0.590),
            'ATM-IV': (0.107, 0.464),
            'beta': (0.233, 0.162),
            'momentum': (0.021, 0.103),
            'size': (0.215, 0.135),
            'bhar': (1.257, 0.612),
            'observations': 1474,
            'adjusted_r2': 0.014,
        },
        ('Table 7', 'n=3'): {
            'page': 480,
            'RR-IV': (1.809, 1.240),
            'P/C': (-0.274, 0.669),
            'ATM-IV': (0.575, 0.532),
            'beta': (0.340, 0.175),
            'momentum': (0.044, 0.112),
            'size': (0.270, 0.145),
            'bhar': (1.337, 0.666),
            'observations': 1320,
            'adjusted_r2': 0.014,
        },
        ('Table 8', '(1)'): {
            'page': 481,
            'Alt RR-IV': (1.844, 0.656),
            'P/C': (-0.635, 0.142),
            'Alt ATM-IV': (0.718, 0.337),
            'beta': (0.168, 0.144),
            'momentum': (-0.082, 0.086),
            'size': (0.343, 0.110),
            'bhar': (1.107, 0.548),
            'observations': 1672,
            'adjusted_r2': 0.034,
        },
        ('Table 8', '(2)'): {
            'page': 481,
            'Alt RR-IV': (2.386, 0.699),
            'P/C': (-0.620, 0.145),
            'Alt ATM-IV': (0.432, 0.362),
            'beta': (0.234, 0.150),
            'momentum': (0.035, 0.096),
            'size': (0.229, 0.122),
            'bhar': (0.863, 0.553),
            'observations': 1672,
            'adjusted_r2': 0.043,
        },
        ('Table 9', 'n=2'): {
            'page': 482,
            'Alt RR-IV': (3.010, 1.037),
            'P/C': (-0.204, 0.190),
            'Alt ATM-IV': (0.102, 0.471),
            'beta': (0.344, 0.163),
            'momentum': (0.070, 0.105),
            'size': (0.232, 0.134),
            'bhar': (1.277, 0.607),
            'observations': 1429,
            'adjusted_r2': 0.031,
        },
        ('Table 9', 'n=3'): {
            'page': 482,
            'Alt RR-IV': (2.314, 1.213),
            'P/C': (-0.302, 0.191),
            'Alt ATM-IV': (0.416, 0.531),
            'beta': (0.394, 0.174),
            'momentum': (0.076, 0.113),
            'size': (0.313, 0.143),
            'bhar': (1.565, 0.653),
            'observations': 1273,
            'adjusted_r2': 0.027,
        },
    }
    TABLE_3 = {
        'sue': (1831, 0.052, 1.089),
        'rr_iv_1': (2081, -0.011, 0.060),
        'atm_iv_1': (2081, 0.455, 0.142),
        'pc_contracts_1': (2081, 0.124, 0.184),
        'rr_iv_2': (1768, -0.007, 0.110),
        'atm_iv_2': (1768, 0.448, 0.157),
        'pc_contracts_2': (1768, 0.105, 0.237),
        'rr_iv_3': (1578, -0.006, 0.149),
        'atm_iv_3': (1578, 0.437, 0.160),
        'pc_contracts_3': (1578, 0.099, 0.171),
        'beta': (1971, 1.265, 0.595),
        'momentum': (2080, 0.028, 0.393),
        'size': (2081, 12.493, 1.269),
        'bhar': (2081, -0.003, 0.056),
    }
    TABLE_4_SUE = {
        'rr_iv_1': 0.162,
        'atm_iv_1': -0.061,
        'pc_contracts_1': -0.110,
        'rr_iv_2': 0.091,
        'atm_iv_2': -0.089,
        'pc_contracts_2': -0.082,
        'rr_iv_3': 0.078,
        'atm_iv_3': -0.075,
        'pc_contracts_3': -0.056,
    }
    FIGURE_4 = {
        'os_ratio': {-10: 1.05, -2: 1.22, -1: 1.52, 0: 1.63, 1: 1.46},
        'of_ratio': {-10: 0.46, -2: 0.51, -1: 0.64, 0: 0.71, 1: 0.68},
    }
    FIGURE_3_SUE_LARGE_NEGATIVE = {-2: -0.005, -1: -0.013, 0: -0.0125}
