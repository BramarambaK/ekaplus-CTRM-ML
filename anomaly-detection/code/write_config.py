# -*- coding: utf-8 -*-
"""
Created on Tue May 21 18:07:43 2019

@author: amitabh.gunjan
"""
import configparser
import os
import sys
import create_folders



def create_config_file(conf_contents):
    """Parse the config file containing path to the models and the data."""

    config = configparser.ConfigParser()
    # add a new section and some values
    config.add_section('PATH')
    config['PATH']['input_df'] = conf_contents['input_df']
    config['PATH']['model_path'] = conf_contents['model_path']
    conf_path = conf_contents['conf_file']
    with open(conf_path, 'w') as configfile:
        config.write(configfile)
    return None

def conf_content_writer(models_and_data_path, tenant_id, app_id, user_id):
    """Config file contents."""

    outside_apps_path = models_and_data_path.split('/')[:-1]
    code_path = "/".join(outside_apps_path) + "codes"
    sys.path.append(os.path.join(code_path))
    conf_contents = create_folders.config_file_contents(models_and_data_path, tenant_id, app_id, user_id)
    create_folders.make_folders(conf_contents)
    create_config_file(conf_contents)
    return None

def config_parser(models_and_data_path, tenant_id, app_id, user_id):
    """Parse the config file containing path to the models and the data."""
    
    conf_contents = create_folders.config_file_contents(models_and_data_path, tenant_id, app_id, user_id)
    file = conf_contents['conf_file']
    config = configparser.ConfigParser()
    config.read(file)
    config.sections()
    'PATH' in config
    data_path = config['PATH']['input_df']
    model_path = config['PATH']['model_path']
    return data_path, model_path