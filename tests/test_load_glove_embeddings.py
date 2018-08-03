import pytest
import torch
from torch.nn import Embedding
from sockpuppet.model.embedding import WordEmbeddings

FIRST_ROW_VECTOR = torch.tensor([
    0.62415, 0.62476, -0.082335, 0.20101, -0.13741, -0.11431, 0.77909, 2.6356, -0.46351, 0.57465,
    -0.024888, -0.015466, -2.9696, -0.49876, 0.095034, -0.94879, -0.017336, -0.86349, -1.3348, 0.046811,
    0.36999, -0.57663, -0.48469, 0.40078, 0.75345
])

ZERO_VECTOR = torch.zeros_like(FIRST_ROW_VECTOR)


@pytest.fixture(scope="module")
def embedding_layer(glove_embedding: WordEmbeddings):
    return Embedding.from_pretrained(glove_embedding.vectors)


def test_correct_embedding_words_loaded(glove_embedding: WordEmbeddings):
    assert glove_embedding.words[2] == "<user>"


def test_all_embedding_vectors_loaded(glove_embedding: WordEmbeddings):
    assert len(glove_embedding) == 1193516


def test_pad_is_index_0(glove_embedding: WordEmbeddings):
    assert glove_embedding.words[0] == "<pad>"


def test_unk_is_index_1(glove_embedding: WordEmbeddings):
    assert glove_embedding.words[1] == "<unk>"


def test_first_word_vector_is_all_zeros(glove_embedding: WordEmbeddings):
    assert glove_embedding[0].numpy() == pytest.approx(ZERO_VECTOR.numpy())


def test_correct_embedding_vector_length(glove_embedding: WordEmbeddings):
    assert len(glove_embedding.vectors[0]) == 25


def test_correct_embedding_values_loaded(glove_embedding: WordEmbeddings):
    assert glove_embedding.vectors[2].numpy() == pytest.approx(FIRST_ROW_VECTOR.numpy())


def test_embedding_length_consistent(glove_embedding: WordEmbeddings):
    assert len(glove_embedding.vectors) == len(glove_embedding.words)


def test_get_vector_by_int_index(glove_embedding: WordEmbeddings):
    assert glove_embedding[2].numpy() == pytest.approx(FIRST_ROW_VECTOR.numpy())


def test_get_vector_by_str_index(glove_embedding: WordEmbeddings):
    assert glove_embedding["<user>"].numpy() == pytest.approx(FIRST_ROW_VECTOR.numpy())


def test_encode_returns_tensor(glove_embedding: WordEmbeddings):
    tokens = "<user> it is not in my video".split()
    encoding = glove_embedding.encode(tokens)

    assert torch.is_tensor(encoding)


def test_encode_has_correct_value(glove_embedding: WordEmbeddings):
    tokens = "<user> it is not in my video".split()
    encoding = glove_embedding.encode(tokens)

    assert torch.equal(encoding, torch.LongTensor([2, 35, 34, 80, 37, 31, 288]))


def test_embed_from_encoding_returns_tensor(glove_embedding: WordEmbeddings):
    tokens = "<user> it is not in my video".split()
    encoding = glove_embedding.encode(tokens)
    embedding = glove_embedding.embed(encoding)

    assert torch.is_tensor(embedding)


def test_embed_from_encoding_has_correct_shape(glove_embedding: WordEmbeddings):
    tokens = "<user> it is not in my video".split()
    encoding = glove_embedding.encode(tokens)
    embedding = glove_embedding.embed(encoding)

    assert embedding.shape == torch.Size([len(tokens), len(FIRST_ROW_VECTOR)])


def test_embed_from_encoding_has_correct_value(glove_embedding: WordEmbeddings):
    tokens = "<user> it is not in my video".split()
    encoding = glove_embedding.encode(tokens)
    embedding = glove_embedding.embed(encoding)

    assert embedding[0].numpy() == pytest.approx(FIRST_ROW_VECTOR.numpy())


def test_embed_from_tokens_returns_tensor(glove_embedding: WordEmbeddings):
    tokens = "<user> it is not in my video".split()
    embedding = glove_embedding.embed(tokens)

    assert torch.is_tensor(embedding)


def test_embed_from_tokens_has_correct_shape(glove_embedding: WordEmbeddings):
    tokens = "<user> it is not in my video".split()
    embedding = glove_embedding.embed(tokens)

    assert embedding.shape == torch.Size([len(tokens), len(FIRST_ROW_VECTOR)])


def test_embed_from_tokens_has_correct_value(glove_embedding: WordEmbeddings):
    tokens = "<user> it is not in my video".split()
    embedding = glove_embedding.embed(tokens)

    assert embedding[0].numpy() == pytest.approx(FIRST_ROW_VECTOR.numpy())


def test_unknown_word_embeds_to_zero_vector(glove_embedding: WordEmbeddings):
    embedding = glove_embedding["<france>"]

    assert embedding.numpy() == pytest.approx(ZERO_VECTOR.numpy())


def test_unknown_word_encodes_to_index_1(glove_embedding: WordEmbeddings):
    tokens = "<france> <spain> <china> <user>".split()
    encoding = glove_embedding.encode(tokens)

    assert torch.equal(encoding, torch.LongTensor([1, 1, 1, 2]))


def test_embed_empty_string_to_zero(glove_embedding: WordEmbeddings):
    tokens = "".split()
    embedding = glove_embedding.embed(tokens)

    assert embedding[0].numpy() == pytest.approx(ZERO_VECTOR.numpy())


def test_embedding_can_create_layer(glove_embedding: WordEmbeddings):
    layer = glove_embedding.to_layer()
    assert isinstance(layer, Embedding)


def test_embedding_layer_can_embed_words(glove_embedding: WordEmbeddings):
    tokens = "<user> it is not in my video".split()
    encoding = glove_embedding.encode(tokens)
    layer = glove_embedding.to_layer()

    assert layer(encoding).numpy()[0] == pytest.approx(FIRST_ROW_VECTOR.numpy())
