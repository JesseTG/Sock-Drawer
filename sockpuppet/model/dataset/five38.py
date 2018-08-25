import csv
import sys
from typing import Callable, Sequence, Tuple, Union
from numbers import Integral

import numpy
import pandas
import torch
from torch import Tensor
from torch.utils.data.dataset import Dataset

from sockpuppet.model.embedding import WordEmbeddings
from .common import _to_int

TWEET_COLUMN_TYPES = {
    "text": str,
    # "retweet_count": int, TODO: Support
    # "reply_count": int, TODO: Support
    # "favorite_count": int, TODO: Support
    # "num_hashtags": int, TODO: Count on the fly
    # "num_urls": int, TODO: Count on the fly
    # "num_mentions": int, TODO: Count on the fly
}

TWEET_COLUMN_NAMES = tuple(TWEET_COLUMN_TYPES.keys())


class Five38TweetDataset(Dataset):
    def __init__(self, path: str):
        self.data = pandas.read_csv(
            path,
            dtype=TWEET_COLUMN_TYPES,
            engine="c",
            usecols=TWEET_COLUMN_NAMES,
            encoding="utf8",
            header=0,
            memory_map=True,
            na_filter=False,
            doublequote=True
        )

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, index: int):
        if torch.is_tensor(index):
            index = index.item()

        return self.data.loc[index]


class Five38TweetTensorDataset(Dataset):
    pass
