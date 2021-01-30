from time import time
import pandas as pd
import numpy as np
from gensim.models import KeyedVectors
import re
from nltk.corpus import stopwords
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import seaborn as sns

import itertools
import datetime

from keras.preprocessing.sequence import pad_sequences
from keras.models import Model
from keras.layers import Input, Embedding, LSTM, Lambda
import keras.backend as K
from keras.optimizers import Adadelta
from keras.callbacks import ModelCheckpoint


import nltk
  

def text_to_word_list(text):
    ''' Pre process and convert texts to a list of words '''
    text = str(text)
    text = text.lower()

    # Clean the text
    text = re.sub(r"[^A-Za-z0-9^,!.\/'+-=]", " ", text)
    text = re.sub(r"what's", "what is ", text)
    text = re.sub(r"\'s", " ", text)
    text = re.sub(r"\'ve", " have ", text)
    text = re.sub(r"can't", "cannot ", text)
    text = re.sub(r"n't", " not ", text)
    text = re.sub(r"i'm", "i am ", text)
    text = re.sub(r"\'re", " are ", text)
    text = re.sub(r"\'d", " would ", text)
    text = re.sub(r"\'ll", " will ", text)
    text = re.sub(r",", " ", text)
    text = re.sub(r"\.", " ", text)
    text = re.sub(r"!", " ! ", text)
    text = re.sub(r"\/", " ", text)
    text = re.sub(r"\^", " ^ ", text)
    text = re.sub(r"\+", " + ", text)
    text = re.sub(r"\-", " - ", text)
    text = re.sub(r"\=", " = ", text)
    text = re.sub(r"'", " ", text)
    text = re.sub(r"(\d+)(k)", r"\g<1>000", text)
    text = re.sub(r":", " : ", text)
    text = re.sub(r" e g ", " eg ", text)
    text = re.sub(r" b g ", " bg ", text)
    text = re.sub(r" u s ", " american ", text)
    text = re.sub(r"\0s", "0", text)
    text = re.sub(r" 9 11 ", "911", text)
    text = re.sub(r"e - mail", "email", text)
    text = re.sub(r"j k", "jk", text)
    text = re.sub(r"\s{2,}", " ", text)

    text = text.split()
    return text

import json 




#word2vec = KeyedVectors.load_word2vec_format(EMBEDDING_FILE, binary=True)


res = []
def inference(questions):
  for question in questions:
    q2n = []  # q2n -> question numbers representation
    for word in text_to_word_list(question):
      # Check for unwanted word
      #if word in stops and word not in word2vec.vocab:
       # continue                

      if word not in vocabulary:
        vocabulary[word] = len(inverse_vocabulary)
        q2n.append(len(inverse_vocabulary))
        inverse_vocabulary.append(word)
      else:
        q2n.append(vocabulary[word])
    print(q2n)
    res.append(q2n)
  return res


def pad(arr):
  arr = np.asarray(arr, np.int32)
  pad = np.zeros((213,))
  shape = arr.shape[0]
  pad[-shape:] = arr
  return pad


def pad_questions(user_question):
    result = []
    for i in range(len(res)):
        temp = pad(res[i])
        result.append(temp)
    return result




def exponent_neg_manhattan_distance(left, right):
    ''' Helper function for the similarity estimate of the LSTMs outputs'''
    return K.exp(-K.sum(K.abs(left-right), axis=1, keepdims=True))

def create_model():
  n_hidden = 50
  gradient_clipping_norm = 1.25
  batch_size = 64
  n_epoch = 25
    
  # The visible layer
  left_input = Input(shape=(max_seq_length,), dtype='int32')
  right_input = Input(shape=(max_seq_length,), dtype='int32')

  embedding_layer = Embedding(len(embeddings), embedding_dim, weights=[embeddings], input_length=max_seq_length, trainable=False)

  # Embedded version of the inputs
  encoded_left = embedding_layer(left_input)
  encoded_right = embedding_layer(right_input)

  # Since this is a siamese network, both sides share the same LSTM
  shared_lstm = LSTM(n_hidden)

  left_output = shared_lstm(encoded_left)
  right_output = shared_lstm(encoded_right)

  # Calculates the distance as defined by the MaLSTM model
  malstm_distance = Lambda(function=lambda x: exponent_neg_manhattan_distance(x[0], x[1]),output_shape=lambda x: (x[0][0], 1))([left_output, right_output])

  # Pack it all up into a model
  malstm = Model([left_input, right_input], [malstm_distance])

  return malstm

def load_pretrained():
  model = create_model()
  model.load_weights('/content/gdrive/My Drive/Siamese LSTM/model.h5')
  return model


def load_structure():
  with open('/content/gdrive/My Drive/Siamese LSTM/vocab.json') as f:
      vocabulary = json.load(f)
  embeddings = np.load('/content/gdrive/My Drive/Siamese LSTM/data.npy')
  model = load_pretrained()

  return vocabulary, embeddings, model

def checkSemantics(question1, question2, vocabulary, embeddings, model):
    nltk.download('stopwords')
    
    questions = []
    questions.append(question1)
    questions.append(question2)
    res =[]
    stops = set(stopwords.words('english'))
    inverse_vocabulary = ['<unk>']
    inference(questions)
    max_seq_length = 213
    embedding_dim = 300
    result = pad_questions(res)
    vals = model.predict([result[0],result[1]])
    op_len = max(len(questions[0]), len(questions[1]))
    final_score = np.sum(vals[-op_len:]) / op_len
    isSimilar = False
    if(final_score > 0.4):
        isSimilar = True
    return isSimilar