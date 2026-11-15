import numpy as np
import pandas as pd

def close_values(close):
    if not isinstance(close,pd.Series) or close.empty or close.index.has_duplicates or not close.index.is_monotonic_increasing:
        raise ValueError('ordered nonempty unique price series required')
    if not np.isfinite(close).all() or (close<=0).any():raise ValueError('prices must be finite and positive')
    return close.astype(float)
