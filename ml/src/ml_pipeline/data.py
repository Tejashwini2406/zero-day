"""Synthetic data utilities and PyTorch Dataset wrappers."""
import numpy as np
import pandas as pd
from torch.utils.data import Dataset


def generate_tabular_normal(n_samples=1000, n_features=16):
    """Generate synthetic normal data (multivariate Gaussian)."""
    mu = np.zeros(n_features)
    cov = np.eye(n_features)
    X = np.random.multivariate_normal(mu, cov, size=n_samples)
    return X.astype("float32")


def generate_sequence_data(n_series=200, seq_len=50, n_features=8):
    data = []
    for i in range(n_series):
        base = np.random.randn(n_features) * 0.1
        series = [base + np.random.randn(n_features) * 0.5 * (j/seq_len) for j in range(seq_len)]
        data.append(np.stack(series))
    return np.array(data, dtype="float32")


class SequenceDataset(Dataset):
    def __init__(self, sequences):
        self.sequences = sequences

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return self.sequences[idx]
