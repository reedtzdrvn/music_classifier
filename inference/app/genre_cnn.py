# -*- coding: utf-8 -*-
"""CNN-архитектура для классификации жанров (соответствует practical/model.py).

4 свёрточных блока (64->128->256->512), BatchNorm + ReLU, асимметричный
max-pooling, GlobalAvgPool, dropout 0.5, полносвязный слой на 8 классов.
"""
import torch
import torch.nn as nn


def conv_block(in_ch: int, out_ch: int, pool: tuple[int, int]) -> nn.Sequential:
    return nn.Sequential(
        nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
        nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1, bias=False),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
        nn.MaxPool2d(kernel_size=pool, stride=pool),
    )


class GenreCNN(nn.Module):
    """Архитектура из 3.2.1 — около 4.69 млн параметров. Вход: (B, 1, 128, 216)."""

    def __init__(self, n_classes: int = 8, dropout: float = 0.5):
        super().__init__()
        self.block1 = conv_block(1, 64, pool=(2, 2))
        self.block2 = conv_block(64, 128, pool=(2, 2))
        self.block3 = conv_block(128, 256, pool=(2, 4))
        self.block4 = conv_block(256, 512, pool=(1, 4))
        self.gap = nn.AdaptiveAvgPool2d(1)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(512, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.block4(x)
        x = self.gap(x).flatten(1)
        x = self.dropout(x)
        return self.fc(x)
