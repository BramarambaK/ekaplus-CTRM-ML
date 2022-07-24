# -*- coding: utf-8 -*-
"""
Created on Tue May 14 13:02:32 2019

@author: amitabh.gunjan
"""
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")

import logging
import pandas as pd
import json
from pandas.io.json import json_normalize
import _pickle as cPickle
import ast as ast
import numpy as np
from itertools import chain, combinations
import sys
import os

def freeze_dependence_str(dependence_structure):
    """Get the frozensets from the dependence list."""
    distinct_lists = []
    for elem in dependence_structure:
        for k,v in elem.items():
            if isinstance(v[0], list):
                pass
            else:
                distinct_lists.append(set(v))
    frozen_set_independents = list(set([frozenset(elem) for elem in distinct_lists]))
    frozen_set_independents.sort(key = len)
    return frozen_set_independents

def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

def get_predictions(dependence_structure, input_data, naive_bayes_classifier, cols_data, frozen_set_independents, rep_call=None, predict_input=None):
    """Based on the dependence structure and input data the prediction has to be made."""

    # find all the possible combinations of the input data used to predict.
    vars_in_input = input_data.keys()
    vars_in_input_combinations = list(powerset(vars_in_input))
    vars_in_input_combinations = [list(a) for a in vars_in_input_combinations if a is not None]

    # Find common variables from the dependence structure and input variables.
    common_vars_to_predict = {}
    for i in dependence_structure:
        common_vars_ = {k:v for k,v in i.items() for combs in vars_in_input_combinations  if not isinstance(v[0], list)  if set(combs) == set(v)}
        common_vars_to_predict.update(common_vars_)
    if cols_data is not None:
        cols_values = [dac['train_X_cols'] for dic, dac in cols_data.items()]
        if rep_call == True:
            ###############################################################################################
            ### Do a check here for the predicted inputs that will be used for getting further predictions.
            ### Take another argument specifying the predicted inputs if rep_call is True. 
            ### Then check for the data that is required from  train_Y_cols and iterate over only that.
            ###############################################################################################
            Y_cols_vals = [dac['train_Y_cols'] for dic, dac in cols_data.items()]
            cols_values = cols_values + Y_cols_vals
        else:
            pass
        cols_vals_list = [tuple(cols_array) for cols_array in cols_values]
        cols_vals_list_uniques = list(set(cols_vals_list))
        cols_vals_list_uniques_list = [list(cols) for cols in cols_vals_list_uniques]
        cols_vals_list_uniques_ = list(set(list(chain.from_iterable(cols_vals_list_uniques_list))))
    else:
        pass
    # Input data frame
    input_data_df = pd.DataFrame([input_data])
    dummies_data = pd.get_dummies(input_data_df)
    # predict for common vars.
    pred_dict_for_current_fields = {}
    for dep_var, ind_vars in common_vars_to_predict.items():
        pred_map = {}
        pred_prob_map = {}
        cols_vars = [a.split("_")[0] for a in cols_vals_list_uniques_]
        selected_cols = []
        for vars_ in ind_vars:
            if vars_ in cols_vars:
                selected_cols.append([k for k in cols_vals_list_uniques_ if k.split("_")[0] == vars_])
            else:
                pass
        selected_cols = [item for sublist in selected_cols for item in sublist]
        dummies_data_transformed = dummies_data.reindex(columns=selected_cols, fill_value=0)
        try:        
            class_models_for_var = naive_bayes_classifier[dep_var]
            for classes in class_models_for_var:
                try:
                    y_pred = class_models_for_var[classes].predict(dummies_data_transformed)
                    y_pred_prob = class_models_for_var[classes].predict_proba(dummies_data_transformed)
                    pred_prob_map[str(classes)] = y_pred_prob
                    prob_for_classes = {k:v[0,1] for k,v in pred_prob_map.items()}
                    predicted_class = max(prob_for_classes, key = prob_for_classes.get)
                    predicted_class = predicted_class.split("_")[1]
                    pred_dict_for_current_fields[str(dep_var)] = predicted_class
                except (IndexError, AttributeError, ValueError):
                    pred_dict_for_current_fields[str(dep_var)] = "null"
        except KeyError:
            pass
    return pred_dict_for_current_fields    

def load_and_run_nb(input_data, model, data, dependence_structure, frozen_dep_set):
    """Load the model and call the get prediction function."""

    pred_dict_for_all_fields = {}
    pred_dict_for_current_fields = {}
    pred_dict_for_current_fields = get_predictions(dependence_structure=dependence_structure, input_data=input_data, naive_bayes_classifier=model, cols_data=data, frozen_set_independents=frozen_dep_set, rep_call=False, predict_input=None)
    pred_dict_for_all_fields.update(pred_dict_for_current_fields)
    input_data_record = []
    input_data_record.append(input_data)

    """Find out Vars in the dependence structure for which prediction has not been done.
    Take the combinations of the predicted vars and match them with the independent vars found from vars in above query.
    If found then create a new input data and call the get_predictions method again."""

    predicted_vars = [k for k, v in pred_dict_for_all_fields.items()]
    vars_to_predicted = [k for i in dependence_structure for k,v in i.items() ]
    # print("Vars to be predicted:\n", vars_to_predicted)
    # print("Dependence str:\n", dependence_structure)
    vars_remaining_to_predict = list(set(vars_to_predicted) - set(predicted_vars))
    if not vars_remaining_to_predict:
        pass
    else:
        # print("Variables remaining to predicted:\n", vars_remaining_to_predict)
        reduced_dependence_str = {k:v for i in dependence_structure  for k, v in i.items() if k in vars_remaining_to_predict}
        ind_vars_from_reduced_dependence_str = list(list(v) for k,v in reduced_dependence_str.items())
        unique_ind_vars_from_dependence = set(x for l in ind_vars_from_reduced_dependence_str for x in l)
        predicted_input = {k:v for k,v in pred_dict_for_all_fields.items() for l in unique_ind_vars_from_dependence if k == l }
        input_data = {**input_data, **predicted_input}
        reduced_dependence_str_list = []
        reduced_dependence_str_list.append(reduced_dependence_str)
        res = get_predictions(dependence_structure=reduced_dependence_str_list, input_data=input_data, naive_bayes_classifier=model, cols_data=data, frozen_set_independents=frozen_dep_set, rep_call=True, predict_input=predicted_input)
        pred_dict_for_all_fields.update(res)
    return pred_dict_for_all_fields

def predict_for_user(model, cols_data, input_data, dependence_structure, frozen_dep_set):
    """Run the prediction engine for an user."""
    # model, data = load_model_and_data(model_path, data_path)
    import warnings  
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pred_dict_for_all_fields = load_and_run_nb(input_data=input_data, model=model, data=cols_data, dependence_structure=dependence_structure, frozen_dep_set=frozen_dep_set)
    return pred_dict_for_all_fields


def compute_recommendations(model_list, cols_data_list, user_ids, dep_list, object_id):
    """Compute recommendations and save them to db."""
    recommendations_for_all = []
    for user in user_ids:
        result = {}
        input_data = {"userId": str(user)}
        for i in model_list:
            if str(user) in i:
                model = i[str(user)]

        for i in cols_data_list:
            if str(user) in i:
                cols_data = i[str(user)]

        for i in dep_list:
            if str(user) in i:
                dependence_structure = i[str(user)]
        frozen_dep_set = freeze_dependence_str(dependence_structure)
        result['recommendation_data'] = predict_for_user(model, cols_data, input_data, dependence_structure, frozen_dep_set)
        result['user_id'] = str(user)
        result['name'] = "ml_recommendation"
        result['source_object_id'] = object_id
        recommendations_for_all.append(result)
    return recommendations_for_all