from collections import namedtuple
from typing import Callable, Sequence
import time

import pytest
import torch
import ignite

from torch import Tensor, LongTensor
from torch.utils.data import DataLoader, Dataset, TensorDataset, ConcatDataset, RandomSampler, random_split
from ignite.engine import Events, Engine
from ignite.handlers import EarlyStopping
import ignite.metrics
from sockpuppet.model.nn import ContextualLSTM
from sockpuppet.model.embedding import WordEmbeddings
from sockpuppet.model.dataset.label import LabelDataset, SingleLabelDataset
from sockpuppet.model.dataset.cresci import CresciTensorTweetDataset
from sockpuppet.model.dataset import sentence_collate, sentence_label_collate
from sockpuppet.utils import split_integers
from tests.marks import *

CHECKPOINT_EVERY = 100
MAX_EPOCHS = 5
BATCH_SIZE = 128

NOT_BOT = 0
BOT = 1
TRAINING_SPLIT = 0.4
VALIDATION_SPLIT = 0.1
TESTING_SPLIT = 0.5
TRAINER_PATIENCE = 100


Splits = namedtuple("Splits", ("full", "training", "validation", "testing"))


@pytest.fixture(scope="module")
def cresci_genuine_accounts_split(cresci_genuine_accounts_tweets_tensors: CresciTensorTweetDataset):
    length = len(cresci_genuine_accounts_tweets_tensors)
    split_lengths = split_integers(length, (TRAINING_SPLIT, VALIDATION_SPLIT, TESTING_SPLIT))

    splits = random_split(cresci_genuine_accounts_tweets_tensors, split_lengths)

    return Splits(cresci_genuine_accounts_tweets_tensors, *splits)


@pytest.fixture(scope="module")
def cresci_social_spambots_1_split(cresci_social_spambots_1_tweets_tensors: CresciTensorTweetDataset):
    length = len(cresci_social_spambots_1_tweets_tensors)
    split_lengths = split_integers(length, (TRAINING_SPLIT, VALIDATION_SPLIT, TESTING_SPLIT))

    splits = random_split(cresci_social_spambots_1_tweets_tensors, split_lengths)

    return Splits(cresci_social_spambots_1_tweets_tensors, *splits)


@pytest.fixture(scope="module")
def training_data(
    cresci_genuine_accounts_split: Splits,
    cresci_social_spambots_1_split: Splits
):
    notbot = SingleLabelDataset(cresci_genuine_accounts_split.training, NOT_BOT)
    bot = SingleLabelDataset(cresci_social_spambots_1_split.training, BOT)

    dataset = ConcatDataset([notbot, bot])
    sampler = RandomSampler(dataset)
    return DataLoader(dataset=dataset, sampler=sampler, batch_size=BATCH_SIZE, collate_fn=sentence_label_collate)


@pytest.fixture(scope="module")
def validation_data(
    cresci_genuine_accounts_split: Splits,
    cresci_social_spambots_1_split: Splits
):
    notbot = SingleLabelDataset(cresci_genuine_accounts_split.validation, NOT_BOT)
    bot = SingleLabelDataset(cresci_social_spambots_1_split.validation, BOT)

    dataset = ConcatDataset([notbot, bot])
    sampler = RandomSampler(dataset)
    return DataLoader(dataset=dataset, sampler=sampler, batch_size=BATCH_SIZE, collate_fn=sentence_label_collate)


@pytest.fixture(scope="module")
def testing_data(
    cresci_genuine_accounts_split: Splits,
    cresci_social_spambots_1_split: Splits
):
    notbot = SingleLabelDataset(cresci_genuine_accounts_split.testing, NOT_BOT)
    bot = SingleLabelDataset(cresci_social_spambots_1_split.testing, BOT)

    dataset = ConcatDataset([notbot, bot])
    sampler = RandomSampler(dataset)
    return DataLoader(dataset=dataset, sampler=sampler, batch_size=BATCH_SIZE, collate_fn=sentence_label_collate)


def test_split_ratios_add_to_1():
    # Very specifically want these numbers to *equal* 1.0 here
    assert TRAINING_SPLIT + VALIDATION_SPLIT + TESTING_SPLIT == 1.0


@modes("cuda")
def test_cresci_genuine_accounts_split_add_up(cresci_genuine_accounts_split: Splits):
    total = len(cresci_genuine_accounts_split.full)
    training_split = len(cresci_genuine_accounts_split.training)
    validation_split = len(cresci_genuine_accounts_split.validation)
    testing_split = len(cresci_genuine_accounts_split.testing)

    assert training_split + validation_split + testing_split == total


@modes("cuda")
def test_cresci_social_spambots_1_split_add_up(cresci_social_spambots_1_split: Splits):
    total = len(cresci_social_spambots_1_split.full)
    training_split = len(cresci_social_spambots_1_split.training)
    validation_split = len(cresci_social_spambots_1_split.validation)
    testing_split = len(cresci_social_spambots_1_split.testing)

    assert training_split + validation_split + testing_split == total


@modes("cuda", "dp")
@slow
def test_accuracy(device, trainer: Engine, training_data: DataLoader, validation_data: DataLoader, testing_data: DataLoader):
    def tf(y):
        # TODO: Move to general utility function elsewhere
        return (y[0].reshape(-1, 1), y[1].reshape(-1, 1))

    mapping = torch.tensor([[1, 0], [0, 1]], device=device, dtype=torch.long)

    def tf_2class(output):
        y_pred, y = output

        y_pred = mapping.index_select(0, y_pred.round().to(torch.long))

        # TODO: Recall metric isn't meant to be used for a binary class, so expand 0 to [1, 0] and 1 to [0, 1]
        return (y_pred, y.to(torch.long))

    validator = ignite.engine.create_supervised_evaluator(
        trainer.state.model,
        metrics={
            "loss": ignite.metrics.Loss(trainer.state.criterion, output_transform=tf),
            "accuracy": ignite.metrics.BinaryAccuracy(output_transform=tf),
            "recall": ignite.metrics.Recall(average=True, output_transform=tf_2class),
            "precision": ignite.metrics.Precision(average=True, output_transform=tf_2class),
        }
    )

    @trainer.on(Events.STARTED)
    def init_metrics(trainer: Engine):
        trainer.state.loss = []
        trainer.state.accuracy = []
        trainer.state.recall = []
        trainer.state.precision = []

    @trainer.on(Events.EPOCH_COMPLETED)
    def validate(trainer: Engine):
        validator.run(validation_data)
        trainer.state.loss.append(validator.state.metrics["loss"])
        trainer.state.accuracy.append(validator.state.metrics["accuracy"])
        trainer.state.recall.append(validator.state.metrics["recall"])
        trainer.state.precision.append(validator.state.metrics["precision"])

    def score_function(trainer: Engine) -> float:
        return -trainer.state.metrics["loss"]

    handler = EarlyStopping(patience=TRAINER_PATIENCE, score_function=score_function, trainer=trainer)
    validator.add_event_handler(Events.EPOCH_COMPLETED, handler)

    trainer.run(training_data, max_epochs=MAX_EPOCHS)

    assert trainer.state.accuracy[-1] >= 0.50
    assert trainer.state.accuracy[-1] >= 0.60
    assert trainer.state.accuracy[-1] >= 0.70
    assert trainer.state.accuracy[-1] >= 0.80
    assert trainer.state.accuracy[-1] >= 0.90
    assert trainer.state.accuracy[-1] >= 0.95
