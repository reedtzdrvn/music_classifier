# -*- coding: utf-8 -*-
"""Загрузка обученных моделей CNN и AST (один раз при старте сервиса)."""
from __future__ import annotations

import torch

from . import config as C
from .genre_cnn import GenreCNN


class ModelBundle:
    def __init__(self):
        self.cnn = None
        self.cnn_genres = None
        self.ast = None
        self.ast_fe = None
        self.ast_genres = None

    def load(self):
        self._load_cnn()
        self._load_ast()

    def _load_cnn(self):
        state = torch.load(C.CNN_CKPT, map_location="cpu", weights_only=False)
        genres = list(state["genres"])
        model = GenreCNN(n_classes=len(genres))
        model.load_state_dict(state["model"])
        model.eval()
        self.cnn = model
        self.cnn_genres = genres

    def _load_ast(self):
        from transformers import ASTFeatureExtractor, ASTForAudioClassification
        self.ast_fe = ASTFeatureExtractor.from_pretrained(C.AST_DIR)
        model = ASTForAudioClassification.from_pretrained(C.AST_DIR)
        model.eval()
        id2label = model.config.id2label
        self.ast = model
        self.ast_genres = [id2label[i] for i in range(len(id2label))]


BUNDLE = ModelBundle()
