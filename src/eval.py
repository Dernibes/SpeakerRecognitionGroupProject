import argparse
import functools

import numpy as np
import tensorflow as tf
from tqdm import tqdm

from utils.reader import load_audio
from utils.utility import add_arguments, print_arguments

parser = argparse.ArgumentParser(description=__doc__)
add_arg = functools.partial(add_arguments, argparser=parser)
add_arg('list_path',        str,    'dataset/test_list.txt',  'The path to test data list')
add_arg('input_shape',      str,    '(1, 257, 257)',          'Shape of input data ')
add_arg('model_path',       str,    'models/infer_model.h5',  'The path of model')
args = parser.parse_args()

print_arguments(args)

# Load model
model = tf.keras.models.load_model(args.model_path)
model = tf.keras.models.Model(inputs=model.input, outputs=model.get_layer('batch_normalization').output)

#  Calculate accuracy using cos similarity
def cal_accuracy(y_score, y_true):
    y_score = np.asarray(y_score)
    y_true = np.asarray(y_true)
    best_accuracy = 0
    best_threshold = 0
    for i in tqdm(range(0, 100)):
        threshold = i * 0.01
        y_test = (y_score >= threshold)
        acc = np.mean((y_test == y_true).astype(int))
        if acc > best_accuracy:
            best_accuracy = acc
            best_threshold = threshold

    return best_accuracy, best_threshold


# predict audio
def infer(audio_path):
    input_shape = eval(args.input_shape)
    data = load_audio(audio_path, mode='test', spec_len=input_shape[2])
    data = data[np.newaxis, :]
    # start prediction
    feature = model.predict(data)
    return feature[0]


def get_all_audio_feature(list_path):
    with open(list_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    features, labels = [], []
    print('Start to extract all the features of audio...')
    for line in tqdm(lines):
        path, label = line.replace('\n', '').split('\t')
        feature = infer(path)
        features.append(feature)
        labels.append(int(label))
    return features, labels


# cosine similarit
def cosin_metric(x1, x2):
    return np.dot(x1, x2) / (np.linalg.norm(x1) * np.linalg.norm(x2))


def main():
    features, labels = get_all_audio_feature(args.list_path)
    scores = []
    y_true = []
    print('start comparion of features in pairs...')
    for i in tqdm(range(len(features))):
        feature_1 = features[i]
        for j in range(i, len(features)):
            feature_2 = features[j]
            score = cosin_metric(feature_1, feature_2)
            scores.append(score)
            y_true.append(int(labels[i] == labels[j]))
    accuracy, threshold = cal_accuracy(scores, y_true)
    print('When threshold is %f, accuracy is greatest，it is：%f' % (threshold, accuracy))


if __name__ == '__main__':
    main()
