"""Training scripts for baseline models. Simple CLI to train and save models."""
import argparse
import os
import torch
from torch.utils.data import DataLoader
import torch.nn as nn
from ml_pipeline.data import generate_tabular_normal, generate_sequence_data, SequenceDataset
from ml_pipeline.models import Autoencoder, LSTMAE


def train_autoencoder(output_dir, epochs=10, batch_size=32, lr=1e-3):
    X = generate_tabular_normal(2000, 16)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = Autoencoder(input_dim=16, hidden_dims=[64, 32]).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    ds = torch.utils.data.TensorDataset(torch.tensor(X))
    loader = DataLoader(ds, batch_size=batch_size, shuffle=True)
    criterion = nn.MSELoss()
    for ep in range(epochs):
        model.train()
        total = 0.0
        for batch in loader:
            x = batch[0].to(device)
            recon = model(x)
            loss = criterion(recon, x)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += loss.item()
        print(f"Epoch {ep+1}/{epochs} loss={total/len(loader):.6f}")
    os.makedirs(output_dir, exist_ok=True)
    torch.save(model.state_dict(), os.path.join(output_dir, "autoencoder.pt"))


def train_lstm_ae(output_dir, epochs=10, batch_size=16, lr=1e-3):
    seqs = generate_sequence_data(300, seq_len=50, n_features=8)
    ds = SequenceDataset(seqs)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = LSTMAE(input_dim=8, hidden_dim=64).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()
    for ep in range(epochs):
        model.train()
        total = 0.0
        for batch in loader:
            x = batch.float().to(device)
            recon = model(x)
            loss = criterion(recon, x)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += loss.item()
        print(f"Epoch {ep+1}/{epochs} loss={total/len(loader):.6f}")
    os.makedirs(output_dir, exist_ok=True)
    torch.save(model.state_dict(), os.path.join(output_dir, "lstm_ae.pt"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--which", choices=["ae","lstm"], default="ae")
    parser.add_argument("--epochs", type=int, default=10)
    args = parser.parse_args()
    if args.which == "ae":
        train_autoencoder(args.out_dir, epochs=args.epochs)
    else:
        train_lstm_ae(args.out_dir, epochs=args.epochs)


if __name__ == "__main__":
    main()
