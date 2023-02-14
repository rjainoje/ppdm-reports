#!/usr/bin/env python3
# PPDM custom reporting for Dell PowerProtect Data Manager - Github @ rjainoje
# ppdmrpt
__author__ = "Raghava Jainoje"
__version__ = "1.0.0"
__email__ = " "
__date__ = "2023-02-14"

import argparse
from operator import index
from unicodedata import name
import requests
import urllib3
import sys
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
pd.options.mode.chained_assignment = None

writer = pd.ExcelWriter('ppdmrpt.xlsx', engine='xlsxwriter')
urllib3.disable_warnings()
summary_dict = {'PPDM SERVER DETAILS': ''}

def get_args():
    # Get command line args from the user
    parser = argparse.ArgumentParser(
        description='Script to gather PowerProtect Data Manager Information')
    parser.add_argument('-s', '--server', required=True,
                        action='store', help='PPDM DNS name or IP')
    parser.add_argument('-usr', '--user', required=False, action='store',
                        default='admin', help='User')
    parser.add_argument('-pwd', '--password', required=True, action='store',
                        help='Password')
    parser.add_argument('-rd', '--rptdays', required=False, action='store', default=30,
                        help='Report period')                    
    args = parser.parse_args()
    return args

def authenticate(ppdm, user, password, uri):
    # Login
    suffixurl = "/login"
    uri += suffixurl
    headers = {'Content-Type': 'application/json'}
    payload = '{"username": "%s", "password": "%s"}' % (user, password)
    try:
        response = requests.post(uri, data=payload, headers=headers, verify=False)
        response.raise_for_status()
    except requests.exceptions.ConnectionError as err:
        print('Error Connecting to {}: {}'.format(ppdm, err))
        sys.exit(1)
    except requests.exceptions.Timeout as err:
        print('Connection timed out {}: {}'.format(ppdm, err))
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        print("The call {} {} failed with exception:{}".format(response.request.method, response.url, err))
        sys.exit(1)
    if (response.status_code != 200):
        raise Exception('Login failed for user: {}, code: {}, body: {}'.format(
            user, response.status_code, response.text))
    print('Logged in with user: {} to PPDM: {}'.format(user, ppdm))
    token = response.json()['access_token']
    return token


def get_activities(uri, token, window):
    # Get all the Activities
    suffixurl = "/activities"
    uri += suffixurl
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
    filter = 'category eq "PROTECT" and classType in ("JOB") and state in ("COMPLETED") and createTime gt "{}"'.format(window)
    orderby = 'createTime DESC'
    pageSize = '10000'
    params = {'filter': filter, 'orderby': orderby, 'pageSize': pageSize}
    try:
        response = requests.get(uri, headers=headers, params=params, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        print("The call {}{} failed with exception:{}".format(response.request.method, response.url, err))
    if (response.status_code != 200):
        raise Exception('Failed to query {}, code: {}, body: {}'.format(uri, response.status_code, response.text))
    FIELDS1 = ["asset.name", "protectionPolicy.name", "asset.type", "name", "category",	"subcategory", "result.status", "startTime", "endTime",	"duration",	"state", "initiatedType", "scheduleInfo.type", "storageSystem.name", "stats.assetSizeInBytes", "stats.preCompBytes", "stats.postCompBytes", "stats.bytesTransferred", "stats.dedupeRatio", "stats.reductionPercentage"]
    df8 = pd.json_normalize(response.json()['content'])
    # df8['date'] = pd.to_datetime(df8['createTime']).dt.date
    FIELDS2 = list(df8.keys())
    FIELDS = []
    for element in FIELDS1:
        if element in FIELDS2:
            FIELDS.append(element)
    ac_df = df8[FIELDS]
    ac_df.rename(columns={"asset.name":"Asset Name", "protectionPolicy.name":"Policy Name", "asset.type":"Asset Type", "name":"Task Description", "category":"Category", "subcategory":"Backup Type", "result.status":"Status", "startTime":"Start Time", "endTime":"End Time", "duration":"Duration (sec)", "state":"State", "initiatedType":"Job Type", "scheduleInfo.type":"Schedule Frequency", "storageSystem.name":"Data Domain Name",	"stats.assetSizeInBytes":"Asset Size(B)", "stats.preCompBytes":"PreComp Size(B)", "stats.postCompBytes":"PostComp(B)", "stats.bytesTransferred":"Data Transferred(B)", "stats.dedupeRatio":"Dedupe Ratio", "stats.reductionPercentage":"Dedupe %"}, inplace=True)
    # ac_df = ac_df[ac_df["Policy Name"].notnull()]
    return ac_df

def get_jobgroups(uri, token, window):
    # Get all the JOB Groups
    suffixurl = "/activities"
    uri += suffixurl
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
    filter = 'category eq "PROTECT" and classType in ("JOB_GROUP") and state in ("COMPLETED") and createdTime gt "{}"'.format(window)
    orderby = 'createTime DESC'
    pageSize = '10000'
    params = {'filter': filter, 'orderby': orderby, 'pageSize': pageSize}
    try:
        response = requests.get(uri, headers=headers, params=params, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        print("The call {}{} failed with exception:{}".format(response.request.method, response.url, err))
    if (response.status_code != 200):
        raise Exception('Failed to query {}, code: {}, body: {}'.format(uri, response.status_code, response.text))
    FIELDS1 = ["protectionPolicy.name", "protectionPolicy.type", "stats.numberOfAssets", "stats.numberOfProtectedAssets", "category", "subcategory", "classType", "startTime", "endTime", "duration", "stats.bytesTransferredThroughput", "state", "result.status", "stats.assetSizeInBytes", "stats.preCompBytes", "stats.postCompBytes", "stats.bytesTransferred", "stats.dedupeRatio", "stats.reductionPercentage"]
    df9 = pd.json_normalize(response.json()['content'])
    FIELDS2 = list(df9.keys())
    FIELDS = []
    for element in FIELDS1:
        if element in FIELDS2:
            FIELDS.append(element)
    jg_df = df9[FIELDS]
    jg_df['startTime'] = pd.to_datetime(jg_df['startTime']).dt.strftime('%Y-%m-%d %r')
    jg_df['endTime'] = pd.to_datetime(jg_df['endTime']).dt.strftime('%Y-%m-%d %r')
    jg_df.rename(columns={"protectionPolicy.name":'Policy Name', "protectionPolicy.type":'Policy Type', "stats.numberOfAssets":'# of Assets', "stats.numberOfProtectedAssets":'# of Protected Assets', "category":'Category', "subcategory":'SubCategory', "classType":'JobType', "duration":'Duration(sec)', "stats.bytesTransferredThroughput":'Throughput(bytes)', "result.status":'Status', "stats.assetSizeInBytes":'Asset Size(b)', "stats.preCompBytes":'PreComp(b)', "stats.postCompBytes":'PostComp(b)', "stats.bytesTransferred":'Bytes Transferred(b)', "stats.dedupeRatio":'Dedupe Ratio', "stats.reductionPercentage":'Reduction %'}, inplace=True)
    return jg_df

def get_assets(uri, token):
    # Get all the Assets
    suffixurl = "/assets"
    uri += suffixurl
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
    pageSize = '10000'
    filter = 'createdAt gt "2010-05-06T11:20:21.843Z"'
    params = {'filter': filter, 'pageSize': pageSize}
    try:
        response = requests.get(uri, headers=headers, params=params, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        print("The call {}{} failed with exception:{}".format(response.request.method, response.url, err))
    if (response.status_code != 200):
        raise Exception('Failed to query {}, code: {}, body: {}'.format(uri, response.status_code, response.text))
    FIELDS1 = ["name", "protectionStatus", "lastAvailableCopyTime", "size", "protectionCapacity.size", "type", "subtype", "protectionPolicy.name", "details.k8s.inventorySourceName", "details.vm.guestOS", "details.vm.vcenterName", "details.vm.esxName", "details.database.clusterName"]
    df2 = pd.json_normalize(response.json()['content'])
    FIELDS2 = list(df2.keys())
    FIELDS = []
    for element in FIELDS1:
        if element in FIELDS2:
            FIELDS.append(element)
    as_df = df2[FIELDS]
    as_df.rename(columns={"name":'Asset Name', "type":'Asset Type', "protectionStatus":'Protection Status', "size":'Size (B)', "subtype":'SubType', "protectionPolicy.name":'PolicyName', "protectionCapacity.size":'Protection Capacity(B)', "lastAvailableCopyTime":'LastBackupCopy', "details.k8s.inventorySourceName":'K8S Inv Source', "details.vm.guestOS":'VM Guest OS', "details.vm.vcenterName":'vCenterName', "details.vm.esxName":'ESX Name', "details.database.clusterName":'Database ClusterName'}, inplace=True)
    return as_df

def outxls(df_dict):
    # Write output to excel
    for sheet, df in  df_dict.items():
        df.to_excel(writer, sheet_name = sheet, startrow=1, header=False, index=False)
        workbook = writer.book
        worksheet = writer.sheets[sheet]
        (max_row, max_col) = df.shape
        column_settings = [{'header': column} for column in df.columns]
        worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings, 'style': 'Table Style Medium 2'})
        worksheet.set_column(0, max_col - 1, 12)
        print ("Written '{}' information to ppdmreport.xls".format(sheet))
    # writer.sheets['Summary'].activate()
    writer.save()    

def logout(ppdm, user, uri, token):
    suffixurl = "/logout"
    uri += suffixurl
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
    try:
        response = requests.post(uri, headers=headers, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
            print("The call {} {} failed with exception:{}".format(response.request.method, response.url, err))
    if (response.status_code != 204):
        raise Exception('Logout failed for user: {}, code: {}, body: {}'.format(
            user, response.status_code, response.text))
    print('Logout for user: {} from PPDM: {}'.format(user, ppdm))

def main():
    port = "8443"
    apiendpoint = "/api/v2"
    args = get_args()
    ppdm, user, password, rptdays = args.server, args.user, args.password, args.rptdays
    uri = "https://{}:{}{}".format(ppdm, port, apiendpoint)
    token = authenticate(ppdm, user, password, uri)
    gettime = datetime.now() - timedelta(days = int(rptdays))
    window = gettime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    activities = get_activities(uri, token, window)
    jobgroups = get_jobgroups(uri, token, window)
    assets = get_assets(uri, token)
    df_dict = {'BackupReport': activities, 'Policy_Compliance': jobgroups, 'Asset_Compliance': assets}
    outxls(df_dict)
    print("All the data written to the file")
    logout(ppdm, user, uri, token)

if __name__ == "__main__":
    main()