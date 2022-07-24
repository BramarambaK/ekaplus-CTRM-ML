# -*- coding: utf-8 -*-
"""
Created on Tue May 21 17:36:16 2019

@author: amitabh.gunjan
"""
import configparser
import _pickle as cPickle
import os
import inspect

def config_file_contents(models_and_data_path, tenant_id, app_id, user_id):
    """Create the paths for the relevant files required for creating recommendation engine for a new app."""
    
    path_df = models_and_data_path + "/" + tenant_id + "/" + app_id + "/" + user_id + "/data/" 
    path_model = models_and_data_path + "/" + tenant_id + "/"  + app_id + "/" + user_id + "/model"
    conf_file_path = models_and_data_path + "/" + tenant_id + "/" + app_id +"/" + user_id + "/conf/" + user_id + ".ini"
    logging_path = models_and_data_path + "/" + tenant_id + "/" + app_id + "/" + user_id + "/logs/" + user_id + ".log"
    conf_map = {"input_df" : path_df
                , "model_path" : path_model
                , "conf_file" : conf_file_path
                , "logging_path" : logging_path}
    return conf_map

def make_folders(conf_contents):
    """Make folders for the new app to be added to the recommendation engine."""

    conf_contents = {k:"/".join(v.split('/')[:-1]) for k, v in conf_contents.items()}
    for k,v in conf_contents.items():
        if not os.path.exists(v):
            os.makedirs(v)
    return None