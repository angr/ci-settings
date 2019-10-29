#!/usr/bin/env python
# coding: utf-8
import re
import requests
import sys

url = sys.argv[1]
api_url = re.search('https:[^"]*Builds/[0-9]*', requests.get(url).text).group(0)
artifact_id = requests.get(api_url + '/artifacts').json()['value'][0]['resource']['data']
artifact_file_id = requests.get(api_url + '/artifacts?artifactName=build_archive&fileId=' + artifact_id + '&fileName=manifest').json()['items'][0]['blob']['id']
final_url = api_url + '/artifacts?artifactName=build_archive&fileId=' + artifact_file_id + '&fileName=build.tar.gz'
print(final_url)
