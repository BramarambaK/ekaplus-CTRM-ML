import os
import pandas as pd
import numpy as np
import logging
from collections import Counter
import datetime
from time import mktime
import httpagentparser

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# date time format
format_date = "%Y-%m-%d %H:%M:%S"

# variables to compute stats for
vars_to_order = ['workflowTask', 'user_agent', 'OS', 'app']
recent_keys = ['recentWorkflows', 'recentUserAgents', 'recentOSs', 'recentApps']
popular_keys = ['popularWorkflows', 'popularUserAgents', 'popularOSs', 'popularApps']


def parse_date(date):
    date = date.split('+')[0]
    date = date.split('.')[0]
    date = date.split('T')[0] + ' ' + date.split('T')[1]
    date = datetime.datetime.strptime(date, format_date)
    unix_secs = mktime(date.timetuple())
    return unix_secs

def get_data_to_compute(user_based_data, unique_users):
    search_data = {}
    wflow_data = {}
    user_agent_data = {}
    user_os_data = {}
    user_apps_data = {}
    for user_id in unique_users:
        if user_id in user_based_data:
            user_data = user_based_data[user_id]
            _data = [{'activityDate':i['activityDate'], 'workflowTask':i['workflowTask'], 'query':i['requestBody']['bool']['must'][0]['multi_match']['query']}  for i in user_data if 'activityDate' in i if 'requestBody' in i if 'bool' in i['requestBody'] if 'must' in i['requestBody']['bool'] if 'multi_match' in i['requestBody']['bool']['must'][0]]
            search_data[user_id] = _data
            wflow_data[user_id] = [{'activityDate':i['activityDate'], 'workflowTask':i['workflowTask']}  for i in user_data if 'activityDate' in i if 'workflowTask' in i]
            user_agent_data[user_id] = [{'activityDate':i['activityDate'], 'user_agent':httpagentparser.simple_detect(i['headers']['User-Agent'][0])[1]}  for i in user_data if 'activityDate' in i if 'headers' in i]
            user_os_data[user_id] = [{'activityDate':i['activityDate'], 'OS':httpagentparser.simple_detect(i['headers']['User-Agent'][0])[0]}  for i in user_data if 'activityDate' in i if 'headers' in i]
            user_apps_data[user_id] = [{'activityDate':i['activityDate'], 'app':i['appId']}  for i in user_data if 'activityDate' in i if 'appId' in i]
        else:
            pass
    # logger.info(f"The time indexed data for SEARCH:\n {search_data}, and WORKFLOW:\n {wflow_data}")
    return search_data, wflow_data, user_agent_data, user_os_data, user_apps_data

def get_source_list(data):
    hits_ = data['hits']['hits']
    source_list = [i['_source'] for i in hits_]
    return source_list

def get_data_by_user(source_list, across_user):
    user_based_data = {}
    for i in source_list:
        if across_user is True:
            i['username'] = 'all_users'
        if 'username' in i:
            user_ = i['username']
            if user_ in user_based_data:
                user_based_data[user_].append(i)
            else:
                user_based_data[user_] = [i]
    unique_users = list(user_based_data.keys())
    # logger.info(f"The unique users are: {unique_users}")
    return user_based_data, unique_users

def order_searches_by_time(search_data, unique_users, unique_wflows):
    latest_searches_all_users = {}
    for user in unique_users:
        search_by_wflow = {}
        most_recent_time = 0
        if user in search_data:
            data_list = search_data[user]
            for wflow in unique_wflows:
                search_terms = []
                for data_items in data_list:
                    if data_items['workflowTask'] == wflow:
                        date = parse_date(data_items['activityDate'])
                        if date > most_recent_time:
                            most_recent_time = date
                            search_terms.append(data_items['query'])
                        else:
                            search_terms.insert(0, data_items['query'])
                search_by_wflow[str(wflow)] = search_terms
        latest_searches_all_users[str(user)] = search_by_wflow
    # logger.info(f"The latest search data for each workflow for the users is : {latest_searches_all_users}")
    return latest_searches_all_users

def wflow_queries(user_based_data):
    wflow_across_users = [i['workflowTask'] for user, user_data in user_based_data.items() for i in user_data if 'workflowTask' in i]
    user_based_wflow = {}
    for user, user_data in user_based_data.items():
        for i in user_data:
            if 'requestBody' in i:
                if user in user_based_wflow:
                    user_based_wflow[user].append(i['workflowTask'])
                else:
                    user_based_wflow[user] = [i['workflowTask']]
    return wflow_across_users, user_based_wflow


def get_most_frequent(wflow_across_users):
    if len(wflow_across_users) > 0:
        data = Counter(wflow_across_users)
        common = data.most_common(3)
        top3 = [k[0] for k in common]
        return top3
    else:
        return None

def get_unique_wflows(source_list):
    wflow_list = []
    for i in source_list:
        wflow_ = i['workflowTask']
        if wflow_ in wflow_list:
            pass
        else:
            wflow_list.append(wflow_)
    # logger.info(f"The wflows are: {wflow_list}")
    return wflow_list

def search_stats(ordered_searches):
    stats_list = []
    for user_, query_dict in ordered_searches.items():
        user_search_stat = {}
        query_per_wflow_list = []
        user_search_stat['user_id'] = user_
        query_dict_usr = ordered_searches[user_]
        wflows = list(query_dict_usr.keys())
        for wflow in wflows:
            if len(query_dict_usr[wflow]) > 0:
                tmp_ = {wflow:{'popularSearchTerms':get_most_frequent(query_dict[wflow]), 'recentSearchTerms':list(set(query_dict[wflow]))[0:6]}}
                query_per_wflow_list.append(tmp_)
            else:
                pass
        user_search_stat['searchTerms'] = query_per_wflow_list
        stats_list.append(user_search_stat)
    return stats_list


def order_stats_by_time(user_data_time_indexed, unique_users, var_to_order, var_ordered, top_k_freq):
    latest_user_agent_all_users = []
    for user in unique_users:
        latest_wflow = {}
        search_by_wflow = {}
        most_recent_time = 0
        recent_user_agent = []
        if user in user_data_time_indexed:
            for data_ in user_data_time_indexed[user]:
                date = parse_date(data_['activityDate'])
                if date > most_recent_time:
                    most_recent_time = date
                    recent_user_agent.append(data_[var_to_order])
                else:
                    recent_user_agent.insert(0, data_[var_to_order])
            latest_wflow['user_id'] = str(user)
            latest_wflow[var_ordered] = list(set(recent_user_agent))[0:top_k_freq+1]
        latest_user_agent_all_users.append(latest_wflow)
    return latest_user_agent_all_users


def get_popular_stat(ordered_wflows, recent_key, popular_key):
    for dicts in ordered_wflows:
        dicts[popular_key] = get_most_frequent(dicts[recent_key])
    return ordered_wflows


def merge_stats(all_stats, unique_users):
    user_stat = []
    # print(f"The uniques users are : {unique_users}")
    unique_users.append('all_users')
    for user in unique_users:
        specific_user_data = {}
        for data in all_stats:
            if data['user_id'] == user:
                specific_user_data.update(data)
        user_stat.append(specific_user_data)
    return user_stat

def order_user_agent_by_time(search_data, unique_users, unique_wflows):
    latest_searches_all_users = {}
    for user in unique_users:
        search_by_wflow = {}
        most_recent_time = 0
        if user in search_data:
            data_list = search_data[user]
            for wflow in unique_wflows:
                search_terms = []
    # logger.info(f"The latest search data for each workflow for the users is : {latest_searches_all_users}")
    return latest_searches_all_users

def order_apps_across_users(user_data_time_indexed):
    app_data = []
    for k,v in user_data_time_indexed.items():
        app_data = app_data + v
    app_data_dict = {'all_users':app_data}
    latest_apps_across_users = order_stats_by_time(app_data_dict, ['all_users'], 'app', 'recentApps', 5)
    return latest_apps_across_users

def get_search_terms(search_data, unique_users, unique_wflows):
    ordered_searches = order_searches_by_time(search_data, unique_users, unique_wflows)
    user_search_stat = search_stats(ordered_searches)
    return user_search_stat

def across_users_app_stats(user_apps_data):
    latest_apps_across_users = order_apps_across_users(user_apps_data)
    app_stat_across_users = get_popular_stat(latest_apps_across_users, 'recentApps', 'popularApps')
    return app_stat_across_users

def get_stats_for_vars(data_list, unique_users, user_search_stat):
    all_stats = []
    for i in range(len(data_list)):
        data = data_list[i]
        ordered_stats = order_stats_by_time(data, unique_users, vars_to_order[i], recent_keys[i], 5)
        user_stat_apps = get_popular_stat(ordered_stats, recent_keys[i], popular_keys[i])
        all_stats = all_stats + user_stat_apps
    all_stats = all_stats + user_search_stat
    return all_stats

def compute(data, across_app_across_user=None, across_user=None):
    user_based_data, unique_users = get_data_by_user(data, across_user)
    unique_wflows = get_unique_wflows(data)
    wflow_across_users, user_based_wflow = wflow_queries(user_based_data)
    freq_wflows_by_user = [{k:get_most_frequent(v)} for k,v in user_based_wflow.items()]
    search_data, wflow_data, user_agent_data, user_os_data, user_apps_data = get_data_to_compute(user_based_data, unique_users)
    user_search_stat = get_search_terms(search_data, unique_users, unique_wflows)
    data_list = [wflow_data, user_agent_data, user_os_data, user_apps_data]
    all_stats = get_stats_for_vars(data_list, unique_users, user_search_stat)
    if across_app_across_user == True:
        app_stat_across_users = across_users_app_stats(user_apps_data)
        all_stats = all_stats + app_stat_across_users
    merge_stat = merge_stats(all_stats, unique_users)

    return merge_stat, unique_users