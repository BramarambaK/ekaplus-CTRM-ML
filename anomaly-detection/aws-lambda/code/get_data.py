# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 18:22:51 2019

@author: amitabh.gunjan
"""
def get_training_data(path):
    """Get the training data for the anomaly detection model."""
    with open(path, encoding='utf-8') as data_file:
        data = json.loads(data_file.read())
    return data

def get_test_data(path):
    """Get the test data for detecting anomalies."""
    with open(path, encoding='utf-8') as data_file:
        data = json.loads(data_file.read())
    return data