
import logging
import sys
import copy
import os
import time
import pandas as pd
import json
from pandas.io.json import json_normalize
import sklearn.naive_bayes as nb
from itertools import chain
import numpy as np
import get_recommendations


def extract_variables(list_contract, all_vars_from_meta):
    """Remove the variables that are not useful for model training using the dependence matrix."""
    dict_list = []
    for contract in list_contract:
        if any(keys in all_vars_from_meta for keys, vals in contract.items()): # changed here for getting the data for any variable if present.
            dict_list.append(contract)
        else:
            pass
    return dict_list

def create_df(dflist, all_vars_from_meta):
    """Create the Python Dataframe"""
    data_frame = extract_variables(dflist, all_vars_from_meta)
    data_frame = pd.json_normalize(data_frame)
    data_frame = data_frame.replace({np.nan: None})
    data_frame = data_frame.applymap(str)
    return data_frame
    
def make_data_frame(merged, all_vars_from_meta):
    """Flatten the JSON data and create dataframe for processing."""
    # contracts_data = flatten_data(merged, inner_object)
    df_input = create_df(merged, all_vars_from_meta)
    return df_input

def fit_naive_bayes(df_list):
    """Fit the Multinomial Naive Bayes model for all the dependnet variables in the data.
    Misclassification data frame's row names should be the column names of the data i.e. 
    the fields in the data. The column names will be the model names."""
    df_X, df_Y = df_list
    models_dict = {}
    import warnings  
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        train_X = pd.get_dummies(df_X, columns=df_X.columns)
        train_Y = pd.get_dummies(df_Y, columns=df_Y.columns)
        data = {"train_X_cols":train_X.columns.values, "train_Y_cols":train_Y.columns.values}
        for col in train_Y:
            nb_model = nb.MultinomialNB(alpha=0.5)
            try:
                train_y_cols = train_Y[[col]]
                fit = nb_model.fit(train_X, train_y_cols)
                models_dict[str(col)] = fit
            except (ValueError, TypeError):
                models_dict[str(col)] = None
    return models_dict, data

def run_naive_bayes_saver(data, recursive, dependence_list, partial_fit=None):
    '''Run the Naive Bayes model for each dependent variable defined according to the dependence structure provided.'''

    models_for_all_fields = {}
    col_names_for_all_fields = {}
    if recursive:
        for i in dependence_list:
            ind_vars_ = []
            dep_vars_ = []
            [dep_vars_.append(k) for k, v in i.items()]
            [ind_vars_.append(v) for k, v in i.items()]
            ind_vars_ = list(chain(*ind_vars_))
            try:
                df_list_nb = [data[ind_vars_], data[dep_vars_]]
                if partial_fit == True:
                    fit_model = partial_fit_naive_bayes(df_list=df_list_nb, dep_var=i)
                else:
                    fit_model, cols_data = fit_naive_bayes(df_list=df_list_nb)
                models_for_all_fields[str(dep_vars_[0])] = fit_model
                col_names_for_all_fields[str(dep_vars_[0])] = cols_data
            except KeyError:
                pass
    return models_for_all_fields, col_names_for_all_fields


def get_vars_from_dependence_structure(dependence_list):
    """Create the total variables from dependence list in the input.
        Need to do this and then the model training should work for contract object.
        Send the dependence list as input in the body of the API. """
    all_vars_from_meta = []
    for pairs in dependence_list:
        keys = [k for k,v in pairs.items()]
        values = [v for v in pairs.values()]
        flat_list_values = [item for sublist in values for item in sublist]
        flat_list_values.extend(keys)
        if isinstance(flat_list_values[0], list):
            pass
        else:
            all_vars_from_meta.extend(flat_list_values)
    all_vars = list(set(all_vars_from_meta))
    return all_vars


def get_longest_list(listOflists):
    count = []
    for i in listOflists:
        count.append(len(i))
    idx = count.index(max(count))
    return listOflists[idx]

def get_dependence_from_data(input_data):
    """Get all the variables from the data if there is no depenence structure in the db."""
    contract = get_longest_list(input_data)
    all_vars_from_meta = [k for k,v in contract.items()]
    dependence_list = [{var:['sys__createdBy']} for var in all_vars_from_meta]
    return all_vars_from_meta, dependence_list

def create_dependence_structure(dependence_list, input_data):
    """Create dependence for training the model."""
    vars_in_dep_list = [k for i in dependence_list for k,v in i.items()]
    vars_in_data = [keys for contract in input_data for keys, vals in  contract.items()]
    vars_not_in_dep = list(set(vars_in_data) - set(vars_in_dep_list))
    for i in vars_not_in_dep:
        dependence_list.append({str(i):['sys__createdBy']})
    dependence_list = [{k:v+['sys__createdBy']} if k not in vars_not_in_dep else {k:v} for i in dependence_list for k,v in i.items()]
    all_vars_from_meta = get_vars_from_dependence_structure(dependence_list)
    return all_vars_from_meta, dependence_list


def get_dependence_and_vars_from_meta(dependence_list, input_data):
    """Get the dependence list and variables from the meta data of the object."""
    if dependence_list is not None:
        all_vars_from_meta, dependence_list = create_dependence_structure(dependence_list=dependence_list, input_data=input_data)
    else:
        all_vars_from_meta, dependence_list = get_dependence_from_data(input_data)
    return all_vars_from_meta, dependence_list

def kick_off_training(input_data, dependence_list, inner_object):
    """Start training of the Naive Bayes Model.
        Augment the data by user, Read the config files, Make data frame, Run the naive bayes saver function"""
    # input_data = augment_data_with_user(input_data, user)
    # input_data = [{k:v for i in input_data for k,v in i.items() if not isinstance(v, list) if not isinstance(v, dict)}]
    input_data_ = []
    nested_fields_map = {}
    for i in input_data:
        i_copy = copy.deepcopy(i)
        for k,v in i.items():
            if isinstance(v, list):
                del i_copy[k]
            elif isinstance(v, dict):
                nested_fields_map[k] = list()
                for key_, val_ in v.items():
                    i_copy[key_] = val_
                    nested_fields_map[k].append(key_)
        input_data_.append(i_copy)
    # print(f"The data is {input_data_}")
    all_vars_from_meta, dependence_list = get_dependence_and_vars_from_meta(dependence_list, input_data_)
    df_input = make_data_frame(input_data_, all_vars_from_meta)
    trained_model , cols_data = run_naive_bayes_saver(df_input, recursive=True, dependence_list=dependence_list, partial_fit=False)
    return trained_model, cols_data, dependence_list, nested_fields_map

def train_model_for_all_users(input_data, dependence_list, inner_object):
    """Trains the model for all users for the app and the object."""
    user_ids = [i['sys__createdBy'] for i in input_data if 'sys__createdBy' in i]
    user_ids = list(set(user_ids))
    model_list = []
    cols_data_list = []
    dep_list = []
    info_ = "The user IDs :" + str(user_ids)
    logging.info(info_)
    for user in user_ids:
        model_dict = {}
        cols_data_dict = {}
        dep_dict = {}
        input_data_user = []
        for i in input_data:
            if 'sys__createdBy' in i:
                input_data_user.append(i)
            else:
                pass
        if not input_data_user:
            pass
        else:
            trained_model, cols_data, dependence_list = kick_off_training(input_data_user, dependence_list, inner_object)
            model_dict[str(user)] = trained_model
            model_list.append(model_dict)
            cols_data_dict[str(user)] = cols_data
            cols_data_list.append(cols_data_dict)
            dep_dict[str(user)] = dependence_list
            dep_list.append(dep_dict)
    return model_list, cols_data_list, dep_list, user_ids

def train_model_for_system_user(train_data, dependence_list, inner_object):
    """Trains the model for all users for the app and the object."""
    for i in train_data:
        i['userId'] = 'system'
    user_ids = [i['userId'] for i in train_data]
    user_ids = list(set(user_ids))
    for user in user_ids:
        model_dict = {}
        cols_data_dict = {}
        dep_dict = {}
        trained_model, cols_data, dependence_list = kick_off_training(train_data, dependence_list, inner_object)
        model_dict[str(user)] = trained_model
        cols_data_dict[str(user)] = cols_data
        dep_dict[str(user)] = dependence_list
    return model_dict, cols_data_dict, dep_dict