
import logging
import sys
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
    data_frame = json_normalize(data_frame)
    return data_frame
    
def make_data_frame(merged, all_vars_from_meta, inner_object):
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
        train_X = pd.get_dummies(df_X)
        train_Y = pd.get_dummies(df_Y)
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
    dependence_list = [{var:['userId']} for var in all_vars_from_meta]
    return all_vars_from_meta, dependence_list


def create_dependence_structure(dependence_list, input_data):
    """Create dependence by finding the matching variables from meta and data."""

    all_vars_from_meta = get_vars_from_dependence_structure(dependence_list)
    matched_vars_meta_and_data_list = []
    for contract in input_data:
        """Check if all the variables from dependence list are in the variables in the data."""
        matched_vars_meta_and_data_position = np.where(list(keys in all_vars_from_meta for keys, vals in contract.items()))
        # print("Position of the matching variables in the data.\n", matched_vars_meta_and_data_position)
        ###############################################################################################
        # This block of code needs to be tested. This creates the dependence list from the variables in 
        # data if that dependence is not found in the dependence structure list.
        if len(matched_vars_meta_and_data_position[0]) > 0:
            vars_contract = [k for k,v in contract.items()]
            matched_vars_meta_and_data = [vars_contract[i] for i in matched_vars_meta_and_data_position[0]]
            matched_vars_meta_and_data_list.append(matched_vars_meta_and_data)
        else:
            pass
    if len(matched_vars_meta_and_data_list) > 0:
        matched_vars_meta_and_data_list = list(set([item for sublist in matched_vars_meta_and_data_list for item in sublist]))
        # Only keep those lists from the dependence structure dictionary which have a subset of the variables from the matched_vars_meta_and_data_list.
        dependence_list_intersected = []
        for pair in dependence_list:
            dependent_var = [k for k,v in pair.items()]
            independent_var = [v for v in pair.values()]
            independent_var_list = [item for sublist in independent_var for item in sublist]
            independent_var_list.extend(dependent_var)
            all_vars = independent_var_list
            intersection = list(set(all_vars) & set(matched_vars_meta_and_data_list))
            if len(intersection) > 0:
                # print("Intersection i.e. common from all variables and matched_vars_meta_and_data_list\n", intersection)
                ###########################################################################
                ### Assuming that there would only be one parent for a variable in the meta
                ###########################################################################
                ind_var = independent_var[0]
                ind_var.append('userId')
                key_val = {dependent_var[0]:ind_var}
                dependence_list_intersected.append(key_val)
            else:
                key_val = {"userId":independent_var}
                dependence_list_intersected.append(key_val)
        independent_var = [v for i in dependence_list for k,v in i.items() ]
        independent_var = list(set([item for sublist in independent_var for item in sublist]))    
        ind_var_dependence_str = [{independent_var[i]:['userId']} for i in range(len(independent_var))]
        dependence_list_intersected = dependence_list_intersected + ind_var_dependence_str
        dependence_list = dependence_list_intersected
        ### get the first contract from the list of contracts
        contract_0 = input_data[0]
        all_vars_in_data = [keys for keys, vals in contract_0.items()]
        all_dep_vars = get_vars_from_dependence_structure(dependence_list)
        vars_difference = list(set(all_vars_in_data) - set(all_dep_vars))
        # print("Vars difference:\n", vars_difference)
        for vars_ in vars_difference:
            dependence_list.append({vars_ :["userId"]})
    else:
        all_vars_from_meta, dependence_list = get_dependence_from_data(input_data)
    return all_vars_from_meta, dependence_list


def get_dependence_and_vars_from_meta(dependence_list, input_data):
    """Get the dependence list and variables from the meta data of the object."""
    if dependence_list is not None:
        all_vars_from_meta, dependence_list = create_dependence_structure(dependence_list=dependence_list, input_data=input_data)
    else:
        all_vars_from_meta, dependence_list = get_dependence_from_data(input_data)
    return all_vars_from_meta, dependence_list

def kick_off_training(input_data, dependence_list, inner_object):
    """Start training of the Naive Bayes Model. Augment the data by user.
    Read the config files, Make data frame, Run the naive bayes saver function"""
    all_vars_from_meta, dependence_list = get_dependence_and_vars_from_meta(dependence_list, input_data)
    df_input = make_data_frame(input_data, all_vars_from_meta, inner_object)
    trained_model , cols_data = run_naive_bayes_saver(df_input, recursive=True, dependence_list=dependence_list, partial_fit=False)
    return trained_model, cols_data, dependence_list


def train_model_for_all_users(input_data, dependence_list, inner_object):
    """Trains the model for all users for the app and the object."""
    user_ids = [i['userId'] for i in input_data]
    user_ids = list(set(user_ids))
    model_list = []
    cols_data_list = []
    dep_list = []
    # print("The user IDs:",user_ids)
    logging.info("The userIds for which model is being trained.")
    logging.info(user_ids)
    for user in user_ids:
        model_dict = {}
        cols_data_dict = {}
        dep_dict = {}
        input_data = [i for i in input_data if i['userId'] == user]
        if not input_data:
            pass
        else:
            trained_model, cols_data, dependence_list = kick_off_training(input_data, dependence_list, inner_object)
            model_dict[str(user)] = trained_model
            model_list.append(model_dict)
            cols_data_dict[str(user)] = cols_data
            cols_data_list.append(cols_data_dict)
            dep_dict[str(user)] = dependence_list
            dep_list.append(dep_dict)
    return model_list, cols_data_list, dep_list, user_ids

def train_model_for_system_user(input_data, dependence_list, inner_object):
    """Trains the model for all users for the app and the object."""
    for i in input_data:
        i['userId'] = 'system'
    user_ids = [i['userId'] for i in input_data]
    user_ids = list(set(user_ids))
    for user in user_ids:
        model_dict = {}
        cols_data_dict = {}
        dep_dict = {}
        trained_model, cols_data, dependence_list = kick_off_training(input_data, dependence_list, inner_object)
        model_dict[str(user)] = trained_model
        cols_data_dict[str(user)] = cols_data
        dep_dict[str(user)] = dependence_list
    return model_dict, cols_data_dict, dep_dict