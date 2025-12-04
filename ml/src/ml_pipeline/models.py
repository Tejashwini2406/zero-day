"""Baseline models: Autoencoder, LSTM-AE, and DeepLog-like predictor."""
import torch
import torch.nn as nn


class Autoencoder(nn.Module):
    def __init__(self, input_dim, hidden_dims=[64, 32]):
        super().__init__()
        layers = []
        prev = input_dim
        for h in hidden_dims:
            layers.append(nn.Linear(prev, h))
            layers.append(nn.ReLU())
            prev = h
        for h in reversed(hidden_dims[:-1]):
            layers.append(nn.Linear(prev, h))
            layers.append(nn.ReLU())
            prev = h
        layers.append(nn.Linear(prev, input_dim))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


class LSTMAE(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, num_layers=1):
        super().__init__()
        self.encoder = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.decoder = nn.LSTM(hidden_dim, input_dim, num_layers, batch_first=True)
        self.hidden_dim = hidden_dim

    def forward(self, x):
        # x: (B, T, F)
        out, (h, c) = self.encoder(x)
        # use last hidden as a repeating input to decoder
        seq_len = x.size(1)
        dec_in = out[:, -1:, :].repeat(1, seq_len, 1)
        dec_out, _ = self.decoder(dec_in)
        return dec_out


class DeepLogPredictor(nn.Module):
    def __init__(self, vocab_size, emb_dim=64, hidden_dim=128, num_layers=1):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb_dim)
        self.lstm = nn.LSTM(emb_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, vocab_size)

    def forward(self, x):
        # x: (B, T) discrete tokens
        e = self.emb(x)
        out, _ = self.lstm(e)
        logits = self.fc(out)
        return logits
