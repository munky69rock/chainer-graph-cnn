#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tempfile

import six
import unittest

import numpy as np
import scipy.sparse

import chainer
from chainer import optimizers
from chainer.training import extensions
from chainer.training.updater import ParallelUpdater

from lib.datasets import mnist
from lib.models import graph_cnn

from sklearn.datasets import make_classification

class EasyDataset(chainer.dataset.DatasetMixin):
    def __init__(self, train, with_gt=True, n_classes=2):

        X, y = make_classification(n_samples=1000, n_features=4, n_classes=n_classes)
        self.X = X[:,None,:].astype(np.float32)
        self.y = y.astype(np.int32)
        print("X:",self.X.shape)
        print("y:",self.y.shape)

        self.with_gt = with_gt

    def __len__(self):
        return len(self.X)

    def get_example(self, i):
        x = self.X[i]
        if not self.with_gt:
            return x
        label = self.y[i]
        return x, label

class TestGraphCNN(unittest.TestCase):

    def test_train(self):
        outdir = tempfile.mkdtemp()
        print("outdir: {}".format(outdir))

        n_classes = 2
        batch_size = 32

        A = np.array([
            [0, 1, 1, 0],
            [1, 0, 0, 1],
            [1, 0, 0, 0],
            [0, 1, 0, 0],
                ]).astype(np.float32)
        model = graph_cnn.GraphCNN(A, n_out=n_classes)

        optimizer = optimizers.Adam()
        optimizer.setup(model)
        train_dataset = EasyDataset(train=True, n_classes=n_classes)
        train_iter = chainer.iterators.MultiprocessIterator(train_dataset, batch_size)
        devices = {'main': -1}
        updater = ParallelUpdater(train_iter, optimizer, devices=devices)
        trainer = chainer.training.Trainer(updater, (100, 'epoch'), out=outdir)
        trainer.extend(extensions.LogReport(trigger=(1, 'epoch')))
        trainer.extend(extensions.PrintReport(['epoch', 'iteration', 'main/loss', 'main/accuracy']))
        trainer.extend(extensions.ProgressBar())
        trainer.run()

if __name__ == '__main__':
    unittest.main()