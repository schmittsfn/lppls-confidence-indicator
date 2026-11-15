"""Synthetic demonstration, not a market forecast or backtest."""
import json
import numpy as np
import pandas as pd
import lppls_confidence_indicator as models

if __name__ == "__main__":
    rng = np.random.default_rng(137)
    x = np.arange(150)
    d = 180 - x
    prices = np.exp(5 - .1*d**.5 + .003*d**.5*np.cos(8*np.log(d)) + .005*rng.normal(size=len(x)))
    result = {"scope": "one synthetic window, not ensemble confidence", **models.lppls_window(prices)}
    print(json.dumps(result, indent=2, allow_nan=False))
