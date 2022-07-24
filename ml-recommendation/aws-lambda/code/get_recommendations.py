# -*- coding: utf-8 -*-
"""
Created on Tue May 14 13:02:32 2019

@author: amitabh.gunjan
"""
import sys
import os
import copy
import logging
import pandas as pd
import json
from pandas.io.json import json_normalize
import _pickle as cPickle
import ast as ast
import numpy as np
from itertools import chain, combinations
import get_recommendations_on_change

recommendation_object = '75e55d43-3a9f-4240-9916-0716e53ee5ec'

def freeze_dependence_str(dependence_structure):
    """Get the frozensets from the dependence list."""
    distinct_lists = []
    for elem in dependence_structure:
        for k,v in elem.items():
            if isinstance(v[0], list):
                logging.info("Found a list instance. Skipping.")
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
    input_data_df = pd.DataFrame([input_data])
    dummies_data = pd.get_dummies(input_data_df)
    pred_dict_for_current_fields = {}
    for dep_var, ind_vars in common_vars_to_predict.items():
        if dep_var == 'sys__createdBy':
            pass
        else:
            ind_vars = list(set(ind_vars))
            pred_map = {}
            pred_prob_map = {}
            selected_cols = [v['train_X_cols'] for k,v in cols_data.items() if k == dep_var]
            dummies_data_transformed = dummies_data.reindex(columns=selected_cols, fill_value=0)
            ctr = 0
            try:
                class_models_for_var = naive_bayes_classifier[dep_var]
                for classes, models in class_models_for_var.items():
                    if models is None:
                        pred_dict_for_current_fields[str(dep_var)] = "null"
                    else:
                        y_pred = models.predict(dummies_data_transformed)
                        y_pred_prob = models.predict_proba(dummies_data_transformed)
                        pred_prob_map[str(classes)] = y_pred_prob
                        prob_for_classes = {k:list(v)[0][1] for k,v in pred_prob_map.items()}
                        predicted_class = max(prob_for_classes, key = prob_for_classes.get)
                        if len(predicted_class.split("_")) > 1:
                            predicted_class = predicted_class.split("_")[1]
                        else:
                            pass
                        pred_dict_for_current_fields[str(dep_var)] = predicted_class
            except KeyError:
                pass
    return pred_dict_for_current_fields    

def load_and_run_nb(input_data, model, data, dependence_structure, frozen_dep_set, pred_dict_for_all_fields):
    """Load the model and call the get prediction function."""
    if len(pred_dict_for_all_fields) == 0:
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
    vars_remaining_to_predict = list(set(vars_to_predicted) - set(predicted_vars))
    # print(f"The variables remaining to be predicted: {vars_remaining_to_predict}")
    # print(f"The variables that have been predicted: {predicted_vars}")
    if not vars_remaining_to_predict:
        pass
    else:
        reduced_dependence_str = {k:v for i in dependence_structure  for k, v in i.items() if k in vars_remaining_to_predict}
        ind_vars_from_reduced_dependence_str = list(list(v) for k,v in reduced_dependence_str.items())
        unique_ind_vars_from_dependence = set(x for l in ind_vars_from_reduced_dependence_str for x in l)
        predicted_input = {k:v for k,v in pred_dict_for_all_fields.items() for l in unique_ind_vars_from_dependence if k == l }
        # print(f"The input data is : {input_data}")
        input_data = {**input_data, **predicted_input}
        reduced_dependence_str_list = []
        reduced_dependence_str_list.append(reduced_dependence_str)
        # print(f"The variables from dependence structure that are to be predicted are  : {reduced_dependence_str_list}")
        res = get_predictions(dependence_structure=reduced_dependence_str_list, input_data=input_data, naive_bayes_classifier=model, cols_data=data, frozen_set_independents=frozen_dep_set, rep_call=True, predict_input=predicted_input)
        pred_dict_for_all_fields.update(res)
    return pred_dict_for_all_fields


def predict_for_user(model, cols_data, input_data, dependence_structure, frozen_dep_set):
    """Run the prediction engine for an user."""
    longest_dep = max([len(v) for i in dependence_structure for k,v in i.items()])
    # print(f"The longest dependence is : {longest_dep}")
    pred_dict_for_all_fields = {}
    for i in range(longest_dep):
        preds = load_and_run_nb(input_data=input_data, model=model, data=cols_data, dependence_structure=dependence_structure, frozen_dep_set=frozen_dep_set, pred_dict_for_all_fields=pred_dict_for_all_fields)
        pred_dict_for_all_fields.update(preds)
    # print(f"The predicted fields are: {pred_dict_for_all_fields}")
    return pred_dict_for_all_fields

def compute_recommendations(model_list, cols_data_list, user_ids, dep_list, object_id, app_id, training_data, nested_fields_map, all_users=None):
    """Compute recommendations and save them to db."""
    recommendations_for_all = []
    for user in user_ids:
        result = {}
        input_data = {"sys__createdBy": str(user)}
        if all_users == True:
            for i in model_list:
                if str(user) in i:
                    model = i[str(user)]

            for i in cols_data_list:
                if str(user) in i:
                    cols_data = i[str(user)]

            for i in dep_list:
                if str(user) in i:
                    dependence_structure = i[str(user)]
        else:
            dependence_structure = dep_list
            model = model_list
            cols_data = cols_data_list
        frozen_dep_set = freeze_dependence_str(dependence_structure)
        recommendation_data = {}
        generic_preds = predict_for_user(model, cols_data, input_data, dependence_structure, frozen_dep_set)
        
        for k,v in generic_preds.items():
            if v == 'None':
                generic_preds[k] = None

        generic_preds_copy = copy.deepcopy(generic_preds)
        for key_, val_ in nested_fields_map.items():
            nested_dict = {}
            for k,v in generic_preds.items():
                if k in val_:
                    nested_dict[k] = v
                    del generic_preds_copy[k]
            generic_preds_copy[key_] = nested_dict

        # recommendation_data['general'] = generic_preds
        recommendation_data['general'] = generic_preds_copy
        result['recommendation_data'] = recommendation_data
        result['user_id'] = str(user)
        # result['name'] = "ml_recommendation"
        result['source_object_id'] = object_id
        result['source_app_id'] = app_id
        result['object'] = recommendation_object
        result['level'] = list(recommendation_data.keys())[0]
        recommendations_for_all.append(result)
        on_change = get_recommendations_on_change.main(user_id=user, dep_str=dependence_structure, frozen_dep_str=frozen_dep_set, input_data=input_data, training_data=training_data, models=model, cols_data_list=cols_data_list, object_id=object_id, app_id=app_id, all_users=all_users)
        for i in on_change:
            if not i:
                pass
            else:
                recommendations_for_all.append(i)
    return recommendations_for_all