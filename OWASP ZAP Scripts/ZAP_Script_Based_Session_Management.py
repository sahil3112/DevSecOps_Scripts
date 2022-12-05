import argparse
import requests
import json
import time

parser = argparse.ArgumentParser()

#-db DATABSE -u USERNAME -p PASSWORD -size 20
parser.add_argument("-zap", "--zap_url", help="OWASP ZAP API URL e.g http://localhost:8090")
parser.add_argument("-key", "--zap_api_key", help="OWASP ZAP API Key")
parser.add_argument("-t", "--target_url", help="Target URL")
parser.add_argument("-sn", "--script_name", help="Session Management Script Name")
parser.add_argument("-se", "--script_engine", help="Session Management Script Engine (Graal.js, Oracle Nashorn or Mozilla Zest)")
parser.add_argument("-sp", "--script_path", help="Session Management Script Path (As per ZAP Container)")
parser.add_argument("-cp", "--context_path", help="Context Path (As per ZAP Container)")
parser.add_argument("-pool_time", "--pool_time", help="Time interval to get latest scan status (in second)", type=int)
parser.add_argument("-tsp", "--spider_scan_result_path", help="Path to Save Tradition Spider Result")
parser.add_argument("-asp", "--ajax_spider_scan_result_path", help="Path to Save AJAX Spider Result")
parser.add_argument("-title", "--title", help="Report Title")
args = parser.parse_args()

#General variables
zap_url=args.zap_url
zap_api_key=args.zap_api_key
target_url=args.target_url

#Script Load Variable
script_Name=args.script_name
script_Type="session"
script_Engine=args.script_engine
file_Name=args.script_path

#Context file variables
context_File=args.context_path
context_ID=""
context_Name=""

#scanasspider
pool_time=args.pool_time
status=''
spider_scan_result_path=args.spider_scan_result_path
ajax_spider_scan_result_path=args.ajax_spider_scan_result_path
report_title=args.title

# check ZAP API service is live or not
try:
    response = requests.get(zap_url)
    print("[+] ZAP API Server is Live")
except:
    print("[-] ZAP API service is not Live")
    exit()

# Load Script for Session Management
temp_url=zap_url+"/JSON/script/action/load/"
headers = {
  'Accept': 'application/json',
  'X-ZAP-API-Key': zap_api_key
}

r = requests.get(temp_url, params={
  'scriptName': script_Name,  'scriptType': script_Type,  'scriptEngine': script_Engine,  'fileName': file_Name
}, headers = headers)

print(r.json())
if r.json()['Result'] == 'OK':
    print("[+] Session Script is loaded successfully")
else:
    print("[-] error while loading Session Script")
    exit()

#Import Context
temp_url=zap_url+"/JSON/context/action/importContext/"
r = requests.get(temp_url, params={
  'contextFile': context_File
}, headers = headers)
print(r.json())

context_ID=r.json()['contextId']
temp_url=zap_url+"/JSON/context/view/contextList/"
r = requests.get(temp_url, params={
}, headers = headers)
context_Name=r.json()['contextList'][0]
print("[+] context ID is "+context_Name)

#sessionManagementViewGetSessionManagementMethod
temp_url=zap_url+"/JSON/sessionManagement/view/getSessionManagementMethod/"
r = requests.get(temp_url, params={
  'contextId': context_ID
}, headers = headers)

print("[+] Session Management Details")
print(r.json())

#usersViewUsersList
temp_url=zap_url+"/JSON/users/view/usersList/"
r = requests.get(temp_url, params={
    'contextId': context_ID
}, headers = headers)
print("[+] Login User Details")
print(r.json())
user_ID=r.json()['usersList'][0]['id']
username=r.json()['usersList'][0]['name']

#spiderActionScanAsUser
temp_url=zap_url+"/JSON/spider/action/scanAsUser/"
r = requests.get(temp_url, params={
  'contextId': context_ID,  'userId': user_ID, 'url': target_url
}, headers = headers)
print("[+] Traditional Spider is started")
print(r.json())
scan_As_User=r.json()['scanAsUser']

#spider scan status
temp_url=zap_url+"/JSON/spider/view/status/"
while status!="100":
    r = requests.get(temp_url, params={
        'scanAsUser': scan_As_User
    }, headers = headers)
    print("[+] Traditional Spidering in progress "+r.json()['status']+" % completed")
    status=r.json()['status']
    time.sleep(pool_time)
print("[+] Traditional Spidering is completed")

#spider scan full result
temp_url=zap_url+"/JSON/spider/view/fullResults/"
r = requests.get(temp_url, params={
  'scanId': scan_As_User
}, headers = headers)
spider_scan_result_file = open(spider_scan_result_path, "w")
spider_scan_result_file.write(str(r.json()))
spider_scan_result_file.close()
print("[+] generated file contains List of URLs crawled by Traditional Spider, Path: "+spider_scan_result_path)

# ajax spider
temp_url=zap_url+"/JSON/ajaxSpider/action/scanAsUser/"
r = requests.get(temp_url, params={
    'contextName': context_Name, 'userName': username, 'url': target_url
    }, headers = headers)
print(r.json())
print("[+] AJAX Spider is started")

#ajax spider status
temp_url=zap_url+"/JSON/ajaxSpider/view/status/"
r = requests.get(temp_url, params={
}, headers = headers)
print(r.json())
status=r.json()['status']
while status=='running':
    r = requests.get(temp_url, params={
    }, headers = headers)
    print("[+] AJSX Spidering is "+r.json()['status'])
    status=r.json()['status']
    time.sleep(pool_time)
print("[+] AJAX Spidering is completed")

#Number of URLs found by AJAX Spider
temp_url=zap_url+"/JSON/ajaxSpider/view/numberOfResults/"
r = requests.get(temp_url, params={
}, headers = headers)
print("[+] Number of URLs crawled by AJAX Spider "+r.json()['numberOfResults'])

#ajax spider result Result
temp_url=zap_url+"/JSON/ajaxSpider/view/fullResults/"
r = requests.get(temp_url, params={
}, headers = headers)
spider_scan_result_file = open(ajax_spider_scan_result_path, "w")
spider_scan_result_file.write(str(r.json()))
spider_scan_result_file.close()
print("[+] generated AJAX spider result, Path: "+ajax_spider_scan_result_path)

# Run active scan
temp_url=zap_url+"/JSON/ascan/action/scanAsUser/"
r = requests.get(temp_url, params={
    'contextId': context_ID, 'userId': user_ID, 'url': target_url
}, headers = headers)
print("[+] Active Scan Started")
print(r.json())

scan_As_User=r.json()['scanAsUser']
#spider scan status
temp_url=zap_url+"/JSON/ascan/view/status/"
while status!="100":
    r = requests.get(temp_url, params={
        'scanAsUser': scan_As_User
    }, headers = headers)
    print("[+] Active Scan in progress "+r.json()['status']+" % completed")
    status=r.json()['status']
    time.sleep(pool_time)
print("[+] Active Scan is completed")

#report generation
report_title="test"
temp_url=zap_url+"/JSON/reports/action/generate/"
r = requests.get(temp_url, params={
    'title': report_title, 'template': 'traditional-html-plus'
}, headers = headers)
print(r.json())
print("[+] report is generated, Path: "+r.json()['generate'])
