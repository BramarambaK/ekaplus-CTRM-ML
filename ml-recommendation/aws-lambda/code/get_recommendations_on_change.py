import logging
from pandas.core.common import flatten
import json
import numpy as np
import pandas as pd
import train_model
import get_recommendations
import push_recommendations
import train_and_get_recommendation

recommendation_object = '75e55d43-3a9f-4240-9916-0716e53ee5ec'

def get_parent_variables(frozen_dep_str):
    frozen_dep_str_list = [list(i) for i in frozen_dep_str]
    parent_var_list = list(flatten(frozen_dep_str_list))
    parent_var_list = list(set(parent_var_list))
    return parent_var_list

def get_dependent_children(parent_var, dependence_structure):
    children_vars = []
    for fields in dependence_structure:
        if parent_var in list(fields.values())[0]:
            children_vars.append(list(fields.keys())[0])
    return children_vars

def get_parent_variable_values(parent_var, training_data, dependence_list):
    all_vars_from_meta, dependence_list = train_model.get_dependence_and_vars_from_meta(dependence_list, training_data)
    df = train_model.make_data_frame(training_data, all_vars_from_meta)
    df = df.fillna(df[parent_var].value_counts().index[0])
    parent_var_column = np.unique(df[[parent_var]].values)
    return parent_var_column

def get_model_file(child, models):
    child_model = models[child]
    return child_model

def get_input_data(user_id, child, parent_variables, var, cols_data_list, all_users=None):
    dummies_list = []
    if all_users == True:
        selected_cols = [i[str(user_id)][child]['train_X_cols'] for i in cols_data_list if user_id in i]
    else:
        selected_cols = [v['train_X_cols'] for k,v in cols_data_list.items() if k == child]
    selected_cols_list = [l.tolist() for l in selected_cols]
    if len(selected_cols) == 0:
        return None, None, None
    else:
        input_x = {parent_var:i.split('_')[1]  for parent_var in parent_variables for i in selected_cols_list[0] if i.split('_')[0] == parent_var if len(i.split('_')) == 2}
        parent_var_vals = [i.split('_')[1] for i in selected_cols_list[0] if i.split('_')[0] == var if len(i.split('_')) == 2]
        input_x['sys__createdBy'] = user_id
        return selected_cols_list, parent_var_vals, input_x

def get_predictions_for_children(input_x, child, models):
    predictions = {}
    input_x = np.array(input_x)
    prob_preds_dict = {}
    for child_val, model in models.items():
        if model is not None:
            try:
                preds = model.predict(input_x)
                prob_preds = model.predict_proba(input_x)
                # print(f"The probability map is: {prob_preds} for child {child} and child value : {child_val}")
                if preds[0] == 1:
                    if len(child_val.split("_")) > 1:
                        predictions[child_val.split('_')[0]] = child_val.split('_')[1]
                else:
                    prob_preds_dict[child_val] = prob_preds
            except ValueError:
                pass
        else:
            pass
    if len(prob_preds_dict) == 0:
        return predictions, prob_preds_dict
    else:
        predicted_val = {k:list(v)[0][0] for k,v in prob_preds_dict.items()}
        predicted_val = max(predicted_val, key=predicted_val.get)
        if len(predicted_val.split("_")) > 1:
            predictions[predicted_val.split('_')[0]] = predicted_val.split('_')[1]
    return predictions, prob_preds_dict

def create_prediction_data(predictions, user, object_id, app_id):
    if "sys__createdBy" in predictions.keys():
        pass
    else:
        result = {}
        result['recommendation_data'] = predictions
        result['user_id'] = str(user)
        # result['name'] = "ml_recommendation"
        result['source_object_id'] = object_id
        result['source_app_id'] = app_id
        result['object'] = recommendation_object
        result['level'] = list(predictions.keys())[0]
        return result

def main(user_id, dep_str, frozen_dep_str, input_data, training_data, models, cols_data_list, object_id, app_id, all_users):
    parent_variables = get_parent_variables(frozen_dep_str)
    # print(f"The cols data list is : {cols_data_list}")
    input_data = [i for i in training_data if 'sys__createdBy' in i if i['sys__createdBy'] == user_id]
    dependent_dropdown_preds = []
    for var in parent_variables:
        on_change = {}
        predictions_on_change_in_var = {}
        if var == 'sys__createdBy':
            pass
        else:
            try:
                parent_var_vals = get_parent_variable_values(var, training_data, dep_str)
            except KeyError:
                parent_var_vals = None
            if parent_var_vals is not None:
                parent_var_val_preds = {}
                for var_ in parent_var_vals:
                    if var_ != 'None':
                        children = get_dependent_children(var, dep_str)
                        child_preds = {}
                        for child in children:
                            # logging.info(f"Computing recommendations for parent {var} and child {child}.")
                            dep_child = [dicts[child] for dicts in dep_str if child in dicts]
                            selected_cols_list, parent_var_vals, input_x = get_input_data(user_id, child, parent_variables, var, cols_data_list, all_users)
                            if any(x is None for x in [selected_cols_list, input_x]):
                                pass
                            else:
                                dep_child = dep_child[0]
                            if input_x is None:
                                pass
                            else:
                                input_val = input_x
                                input_val[var] = var_
                                try:
                                    child_models = get_model_file(child, models)
                                except KeyError:
                                    child_models = None
                                    pass
                                input_val = {k:v for k,v in input_val.items() if k in dep_child}
                                df_x = pd.DataFrame([input_val])
                                dummies_x = pd.get_dummies(df_x)
                                dummies_data_transformed = dummies_x.reindex(columns=selected_cols_list[0], fill_value=0)
                                predictions_child, prob_preds_dict = get_predictions_for_children(dummies_data_transformed, child, child_models)
                                child_preds.update(predictions_child)
                        for k,v in child_preds.items():
                            if v == 'None':
                                child_preds[k] = None
                        parent_var_val_preds[var_] = child_preds
                predictions_on_change_in_var.update(parent_var_val_preds)
        if len(predictions_on_change_in_var) > 0:
            on_change[var] = predictions_on_change_in_var
            pred_data_to_save = create_prediction_data(on_change, user_id, object_id, app_id)
            dependent_dropdown_preds.append(pred_data_to_save)
        else:
            pass
    logging.info("Computed predictions for all the independent variables.")
    return dependent_dropdown_preds