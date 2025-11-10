import requests
from operator import itemgetter
import queue
from collections import defaultdict

## Code for As Built Document
##
##
##
# Function that collects the API bearer token
def get_header(url, usern, passw):
    token = requests.post(f"{url}/api/v1/auth/login", json={"username":usern,"password":passw})
    token_dict=token.json()["token"]
    return {"accept": "application/json", "Authorization": f"Bearer {token_dict}"}

# Function that calls for all Ports from the sources and destinations
def port_collect(ports, api_url, header, sourceOrDest):
    request_ports=requests.get(api_url, headers=header)
    ports_dict=request_ports.json()["items"]
    for count in range(int(request_ports.json()["count"])):
        ports_re=defaultdict(list)
        if "port" not in ports_dict[count]:
            continue
        for key,value in ports_dict[count].items():
            if key == "id":
                ports_re["Name"]=value
            elif key == "type":
                ports_re["Type"]=value
            elif "port" in key.lower():
                ports_re["Port"]=value
            ports_re["Source/Destination"]=sourceOrDest
        ports.append(dict(ports_re))
    return ports

# Function that calls for all Ports given in the worker groups
def get_ports(group,header, url):
    ports=[]
    url_dict = {"Source":f"{url}/api/v1/m/{group}/system/inputs","Destination":f"{url}/api/v1/m/{group}/system/outputs"}
    
    for sourceOrDest, api_url in url_dict.items():
        ports = port_collect(ports, api_url, header, sourceOrDest)

    seen=set()
    while {} in ports:
        ports.remove({})
    for i in ports:
        #print(i)
        i["Port"]=i.pop("Port")
    unique_ports=[]
    for d in ports:
        t=tuple(d.items())
        if t not in seen:
            seen.add(t)
            unique_ports.append(d)
    unique_ports=sorted(unique_ports, key=itemgetter("Port"))
    unique_ports=sorted(unique_ports, key=itemgetter("Source/Destination"))
    for i in unique_ports:
        if i["Port"]==0:
            i["Port"]="None"
    return unique_ports#, leaders_ports

# Function that calls for all Ports given by the Leader
def get_ports_leader(header,url):
    leader_dict={}
    placeholder=[]
    leaders=[]
    request_leaders=requests.get(f"{url}/api/v1/system/info", headers=header)
    for count in range(int(request_leaders.json()["count"])):
        for key,value in request_leaders.json()["items"][count].items():
            if key ==  "apiPort":
                placeholder.append(value)
                for port in placeholder:
                    if port == 9000:
                        leader_dict["Name"]="Web UI"
                        leader_dict["Source"]="User Access"
                        leader_dict["Port"]=value
                        leaders.append(dict(leader_dict))
            if key=="env":
                worker_port=value["CRIBL_DIST_MASTER_URL"]
                if "4200" in worker_port:
                    leader_dict["Name"]="API Communication"
                    leader_dict["Source"]="Workers"
                    leader_dict["Port"]=(4200)
                    leaders.append(dict(leader_dict))
                else:
                    leader_dict["Name"]="API Communication"
                    leader_dict["Source"]="Workers"
                    leader_dict["Port"]="Not Connected"
                    leaders.append(dict(leader_dict))
    return leaders

# Function that calls for all Users
def get_users(header, url):
    request_users = requests.get(f"{url}/api/v1/system/users", headers=header)
    user_count=int(request_users.json()["count"])
    for count in range(user_count):
        for key, value in request_users.json()["items"][count].items():
            print(f"{key}: {value}\n")

# Function that calls for all workers
def get_workers(header,url):
    group_name=""
    work_dict={}
    workers=[]
    workerstest={}
    request_workers=requests.get(f"{url}/api/v1/master/workers", headers=header)
    for count in range(int(request_workers.json()["count"])):
        for key, value in request_workers.json()["items"][count].items():
            #if key == "id":
            #    work_dict["GUID"]=value
            if key == "group":
                #work_dict["Group"]=value
                group_name=value
            elif key == "info":
                work_dict["Hostname"]=value["hostname"]
                work_dict["Group"]=group_name
                work_dict["Cribl Version"]=value["cribl"]["version"]
                work_dict["OS"]=value["platform"]
                work_dict["CPU Cores"]=value["cpus"]
                work_dict["Total Memory in GB"]=int(value["totalmem"]/1024/1024/1024)+1
                work_dict["File Path"]=value["env"]["CRIBL_HOME"]
        workers.append(dict(work_dict))
        workerstest[group_name]=workers
    final={}
    for i in workerstest:
        t=[]
        for b in workerstest[i]:
            if b["Group"] == i:
                t.append(b)
                final[i]=t      
    return final
        
# Function that calls for all pipelines given the worker group
def get_pipelines(group,header,url):
    pipelines=[]
    pipelines_re=defaultdict(list)
    request_pipelines=requests.get(f"{url}/api/v1/m/{group}/pipelines", headers=header)
    pipeline_dict=request_pipelines.json()["items"]
    for count in range(int(request_pipelines.json()["count"])):
        descr=False
        for key, value in pipeline_dict[count].items():
            if key == "id" and not value.startswith("pack"):
                pipelines_re["Name"]=value
            elif key == "conf":
                for k,v in value.items():
                    if k == "description":
                        descr=True
                        pipelines_re["Description"]=v
                    elif k == "functions":
                        pipelines_re["Function Count"]=len(v)
            if key=="id" and value.startswith("pack"):
                descr=True
                pipelines_re["Name"]=value
                pipelines_re["Function Count"]="N/A"
                pipelines_re["Description"]="Find in Packs Table"
        if not descr:
            pipelines_re["Description"]="None"
        pipelines.append(dict(pipelines_re))
    return pipelines

# Function that calls for all routes given the worker group
def get_routes(group,header,url):
    final=""
    routes=[]
    routes_re=defaultdict(list)
    request_routes=requests.get(f"{url}/api/v1/m/{group}/routes", headers=header)
    routes_dict=request_routes.json()["items"]
    if "200" not in str(request_routes):
        print("No routes were set up in this deployment")
        return routes
    
    for i in range(int(request_routes.json()["count"])):
        for key,value in routes_dict[i].items():
            if key != "routes":
                continue
            for j in range(len(value)):
                for k,v in value[j].items():
                    if k == "name":
                        routes_re["Route Name"]=v
                    elif k == "pipeline":
                        routes_re["Pipeline"]=v
                    elif k == "output":
                        routes_re["Output"]=v
                    elif k == "final":
                        final=v
                routes_re["Final?"]=final
                routes.append(dict(routes_re))
    routes=sorted(routes,key=itemgetter("Final?"))
    return routes

# Function that calls for all output routes given the worker group
def get_output_routes(group,header,url):
    output=[]
    request_output_routes=requests.get(f"{url}/api/v1/m/{group}/system/outputs", headers=header)
    output_routes_dict=request_output_routes.json()["items"]
    for i in range(len(output_routes_dict)):
        router=False
        output_re={}
        for key,value in output_routes_dict[i].items():
            if key=="id":
                output_re["Output Router Name"]=value
            if key=="rules":
                for k in value:
                    output_re["Filter"]=k["filter"]
                    output_re["Route"]=k["output"]
                    output_re["Final"]=k["final"]
                    output.append(dict(output_re))
    # request_output_routes=requests.get(f"{url}/api/v1/m/{group}/routes", headers=header)
    # output_routes_dict=request_output_routes.json()["items"]
    # for i in range(len(output_routes_dict)):
    #     for key,value in output_routes_dict[i].items():
    #         if key != "routes":
    #             continue
    #         for j in range(len(value)):
    #             for k,v in value[j].items():
    #                 if k == "name":
    #                     output_re["Route"]=v
    #                 elif k == "filter":
    #                     output_re["Filter"]=v
    #                 elif k == "output":
    #                     output_re["Output Router Name"]=v
    #             output.append(dict(output_re))
    while {} in output:
        output.remove({})
    if output!=[]:
        for i in output:
            i["Final"]=i.pop("Final")
        return output

# Function that calls for all leader information
def get_leaders(header,url):
    leader=[]
    le_dict={}
    request_leader=requests.get(f"{url}/api/v1/system/info", headers=header)
    leader_dict=request_leader.json()["items"]
    for key,value in leader_dict[0].items():
        if key  == "BUILD":
            le_dict["Cribl Version"]=value["VERSION"]
        if key == "hostname":
            le_dict["Hostname"]=value
        elif key == "installPath":
            le_dict["Cribl Home"]=value
        elif key  == "os":
            le_dict["OS"]=value["type"]
        elif key  == "memory":
            le_dict["Total Memory in GB"]=int(value["total"]/1024/1024/1024)+1
        elif key  == "cpus":
            le_dict["CPU"]=value[0]["model"]
        if key =="net":
            le_dict["IP Address"]="empty"
            for k in value["eth0"]:
                if (le_dict["IP Address"]=="empty"):
                    le_dict["IP Address"]=k["address"]
    leader.append(dict(le_dict))
    return leader

# Function that calls for all sources given the worker group
def get_sources(group,header,url):
    source_re=defaultdict(list)
    sources=[]
    request_source=requests.get(f"{url}/api/v1/m/{group}/system/inputs", headers=header)
    source_dict=request_source.json()["items"]
    for count in range(len(source_dict)):
        sour=False
        preprocessing=False
        source_re["Port"]=0
        for key,value in source_dict[count].items():
            if key == "id":
                source_re["Source Name"]=value
            elif key == "type":
                source_re["Type"]=value
            elif(key=="port"):
                sour=True
                if sour==True:
                    source_re["Port"]=value
            elif key=="tcpPort":
                sour=True
                if sour==True:
                    source_re["Port"]=value
            elif(key=="pipeline"):
                preprocessing=True
                source_re["Pre-Processing Pipeline"]=value
            elif (key == "disabled"):
                t=str(value)
                if t == "True":
                    source_re["Enabled"]="False"
                else:
                    source_re["Enabled"]="True"
        if(sour==False):
            source_re["Port"]=0
        if(preprocessing==False):
            source_re["Pre-Processing Pipeline"]="None"
        if "Port" not in source_re:
            source_re["Port"]=0
        sources.append(dict(source_re))
    for j in sources:
        if "Enabled" not in j:
            j["Enabled"]="True"
    sources=sorted(sources,key=itemgetter("Port"))
    sources=sorted(sources,key=itemgetter("Enabled"),reverse=True)
    for i in sources:
        i["Port"]=i.pop("Port")
        if i["Port"]==0:
            i["Port"]="N/A"
    return sources

# Function that calls for all destinations given the worker group
def get_destinations(group,header,url):
    destinations =[]
    request_dest=requests.get(f"{url}/api/v1/m/{group}/system/outputs", headers=header)
    des_dict=request_dest.json()["items"]
    for count in range(len(des_dict)):
        des=False
        preprocessing=False
        destination={}
        for key, value in des_dict[count].items():
            if key == "id":
                destination["Destination Name"]=value
            elif key == "type":
                destination["Type"]=value
            if(key=="port"):
                des=True
                if des==True:
                    destination["Port"]=value
            elif(key=="pipeline"):
                preprocessing=True
                destination["Post-Processing Pipeline"]=value
            if key=="hosts":
                des=True
                destination["Port"]=1
            if key=="rules":
                des=True
                destination["Port"]=2
        if not preprocessing:
            destination["Post-Processing Pipeline"]="None"
        if(des==False):
            destination["Port"]=0
        destinations.append(destination)
    destinations=sorted(destinations,key=itemgetter("Port"))
    for i in destinations:
        i["Port"]=i.pop("Port")
        if i["Port"]==0:
            i["Port"]="N/A"
        if i["Port"]==1:
            i["Port"]="Check Destination Hosts Table"
        if i["Port"]==2:
            i["Port"]="Check Output Routers Table"
    return destinations

# Function that call for all destinations with hosts inside of them
def get_destinations_hosts(group,header,url):
    dest=[]
    request_dest=requests.get(f"{url}/api/v1/m/{group}/system/outputs", headers=header)
    dest_dict=request_dest.json()["items"]
    for count in range(len(dest_dict)):
        dest_current={}
        for key, value in dest_dict[count].items():
            if key=="id":
                dest_current["Destination Name"]=value
            if key=="type":
                dest_current["Type"]=value
            if key=="hosts":
                for k in value:
                    dest_current["Port"]=k["port"]
                    dest_current["Host"]=k["host"]
                    dest.append(dict(dest_current))
    if dest!=[]:
        dest=sorted(dest,key=itemgetter("Destination Name"))
        return(dest)

# Function that calls for all quickconnect data
def get_quickconnects(group,header,url):
    quickconnects=[]
    port1=""
    quick=defaultdict(list)
    request_quickconnect=requests.get(f"{url}/api/v1/m/{group}/system/inputs",headers=header)
    quick_dict=request_quickconnect.json()["items"]
    for count in range(len(quick_dict)):
        for key,value in quick_dict[count].items():
            if key == "id":
                id=value
            elif key == "disabled":
                disabled=value # Is this var used?
            elif key == "port":
                port1=value
            elif key=="type":
                type=value
            elif key == "connections":
                for k in value:
                    quick["Source"]=id
                    quick["Type"]=type
                    quick["Port"] = port1 if port1 != "" else 0
                    if id != "in_win_event_logs":
                        quick["QuickConnect Route"]=k["output"]
        quickconnects.append(dict(quick))
    seen=set()
    while {} in quickconnects:
        quickconnects.remove({})
    unique_quickconnect=[]
    for d in quickconnects:
        t=tuple(d.items())
        if t not in seen:
            seen.add(t)
            unique_quickconnect.append(d)
    if(unique_quickconnect!=[]):
        for i in unique_quickconnect:
            i["Port"]=i.pop("Port")
            if i["Port"]==0:
                i["Port"]="N/A"
        return(unique_quickconnect)
    
# Function that calls for all Packs in the given worker groups
def get_packs(group,header,url):
    packs=[]
    pac_di={}
    request_pack=requests.get(f"{url}/api/v1/m/{group}/packs", headers=header)
    pack_dict=request_pack.json()["items"]
    for count in range(len(pack_dict)):
        usecase=False
        for key,value in pack_dict[count].items():
            if key == "id":
                pac_di["Name"]=value
            elif key == "author":
                pac_di["Author"]=value
            elif key == "version":
                pac_di["Version"]=value
            elif key=="tags":
                try:
                    usecase=True
                    use=""
                    for i in value["useCase"]:
                        use+=i+", "
                    pac_di["Use Case"]=use
                except KeyError:
                    pac_di["Use Case"]="N/A"
            elif key=="description":
                pac_di["Description"]=value
        if usecase==False:
            pac_di["Use Case"]="N/A"
        packs.append(dict(pac_di))
    for i in packs:
        i["Version"]=i.pop("Version")
        i["Author"]=i.pop("Author")
        i["Use Case"]=i.pop("Use Case")
        i["Description"]=i.pop("Description")
    return packs

# Function that calls for all worker groups given an empty array of groups
def all_workgroups(header,url):
    groups=[]
    request_groups=requests.get(f"{url}/api/v1/master/groups", headers=header)
    groups_dict=request_groups.json()["items"]
    for group_dict in groups_dict:
        invalid = False
        for key,value in group_dict.items():
            if (key=="isFleet" or key=="isSearch") and value:
                invalid=True
            if key == "id" and not invalid:
                groups.append(value)
    return groups

# Function that calls for Git Integration Settings
def get_git(header,url):
    gits=[]
    git_items={}
    request_git=requests.get(f"{url}/api/v1/system/settings/git-settings", headers=header)
    git_dict=request_git.json()["items"]
    for git in git_dict:
        try:
            git_items["AuthType"]=git["authType"]
            git_items["AutoAction"]=git["autoAction"]
            git_items["Remote"]=git["remote"]
            git_items["Commit Message"]=git["defaultCommitMessage"]
        except KeyError:
            git_items["AuthType"]="Git not Configured"
            git_items["AutoAction"]="Git not Configured"
            git_items["Remote"]="Git not Configured"
            git_items["Commit Message"]="Git not Configured"
    gits.append(git_items)
    return gits

# Function that calls for all Syslog sources and their ports
def get_syslog(group,header,url):
    syslog_re=defaultdict(list)
    syslog=[]
    request_source=requests.get(f"{url}/api/v1/m/{group}/system/inputs", headers=header)
    syslog_dict=request_source.json()["items"]
    for count in range(len(syslog_dict)):
        boole=False
        name=""
        for key,value in syslog_dict[count].items():
            if key == "id":
                name=value
            if key=="type":
                if value=="syslog":
                    boole=True
                    syslog_re["Syslog"]=name
            if key=="tcpPort":
            #    syslog_re["Syslog"]=name
                syslog_re["Port"]=value
                syslog_re["Bytes"]="Enter value here"
        if boole==False:
            syslog_re={}
        syslog.append(dict(syslog_re))
    while {} in syslog:
        syslog.remove({})
    for i in syslog:
        i["Port"]=i.pop("Port")
        i["Bytes"]=i.pop("Bytes")
    #print(syslog)
    return syslog

# Depth first search of a dictionary for a value at any depth
def multi_layer_find_all(dictionary, search_items):
    output = {}

    search_area = queue.LifoQueue() # creates a stack to store all dictionaries
    search_area.put(dictionary)
    while not search_area.empty():
        if len(output) == len(search_items):
            break
        current = search_area.get()
        for key,value in current.items():
            if key in search_items:
                output[key] = value
            elif type(value) is dict:
                search_area.put(value)
            elif type(value) is list:
                search_area = find_dictionaries_in_list(value, search_area)
    return output

def find_dictionaries_in_list(array, search_area):
    for item in array:
        if type(item) is dict:
            search_area.put(item)
        elif type(item) is list:
            search_area = find_dictionaries_in_list(item, search_area)
    return search_area
    
## Code for Stream Health Check
##
##
##
# Function calling leaders configurations
def get_leader_config(header,url):
    leader=[]
    le_dict={}
    request_workers=requests.get(f"{url}/api/v1/master/workers", headers=header)
    request_leader=requests.get(f"{url}/api/v1/system/info", headers=header)
    leader_dict=request_leader.json()["items"]
    count_total=int(request_workers.json()["count"])
    count_work=0
    for count in range(int(request_workers.json()["count"])):
        count=0
        for key, value in request_workers.json()["items"][count].items():
            if key == "status":
                if value=="healthy":
                    count_work+=1
        le_dict["Active Workers/Total Workers"]=f"{count_work}/{count_total}"
    for key,value in leader_dict[0].items():
        if key == "hostname":
            le_dict["Hostname"]=value
        if key == "memory":
            le_dict["Total Memory in GB"]=int(value["total"]/1024/1024/1024)+1
        if key == "diskUsage":
            le_dict["Disk Total in TB"]=int(value["totalDiskSize"]/1024/1024/1024/1024)+1
        if key == "cpus":
            le_dict["CPU"]=value[0]["model"]
        if key =="net":
            le_dict["IP Address"]="empty"
            for k in value["eth0"]:
                if (le_dict["IP Address"]=="empty"):
                    le_dict["IP Address"]=k["address"]
    leader.append(dict(le_dict))
    return leader

# Function calling workers configurations
def get_workers_config(header,url):
    memory_count=0
    core_count=0
    disk_count=0
    disk_usage=0
    group_name=""
    work_dict={}
    workers=[]
    workerstest={}
    request_workers=requests.get(f"{url}/api/v1/master/workers", headers=header)
    work_dict["Worker Count"]=int(request_workers.json()["count"])
    for count in range(int(request_workers.json()["count"])):
        for key, value in request_workers.json()["items"][count].items():
            if key =="status":
                work_dict["Health"]=value
            if key=="info":
                work_dict["Hostname"]=value["hostname"]
                work_dict["CPU Cores"]=value["cpus"]
                core_count+=value["cpus"]
                work_dict["Memory"]=int(value["totalmem"]/1024/1024/1024)+1
                memory_count+=int(value["totalmem"]/1024/1024/1024)+1
                work_dict["Disk Total in GB"]=int(value["totalDiskSpace"]/1024/1024/1024)
                disk_count+=int(value["totalDiskSpace"]/1024/1024/1024)
                disk_usage+=int(value["freeDiskSpace"]/1024/1024/1024)
        workers.append(dict(work_dict))
    disk_usage=disk_count-disk_usage
    for i in workers:
        i["Total Cores"]=core_count
        i["Total Memory"]=memory_count
        i["Total Disk"]=disk_count
        i["Disk Usage"]=disk_usage
    return workers

# Function calling git configurations
def get_git_config(header,url):
    gits=[]
    git_items={}
    request_git=requests.get(f"{url}/api/v1/system/settings/git-settings", headers=header)
    git_dict=request_git.json()["items"]
    for git in git_dict:
        try:
            git_items["AuthType"]=git["authType"]
            git_items["AutoAction"]=git["autoAction"]
            git_items["Remote"]=git["remote"]
            git_items["Commit Message"]=git["defaultCommitMessage"]
        except KeyError:
            git_items["AuthType"]="Git not Configured"
            git_items["AutoAction"]="Git not Configured"
            git_items["Remote"]="Git not Configured"
            git_items["Commit Message"]="Git not Configured"
    gits.append(git_items)
    return gits

# Function calling destinations failures and Back Pressure settings
def get_destinations_config(group,header,url):
    destinations =[]
    request_dest=requests.get(f"{url}/api/v1/m/{group}/system/outputs", headers=header)
    des_dict=request_dest.json()["items"]
    for count in range(len(des_dict)):
        backpres=False
        destination={}
        for key, value in des_dict[count].items():
            if key == "id":
                destination["Destination Name"]=value
            if key == "onBackpressure":
                backpres=True
                destination["Back Pressure"]=value
            if key == "status":
                try:
                    destination["Health"]=str(value["health"])
                except KeyError:
                    destination["Health"]="N/A"
        if backpres==False:
            destination["Back Pressure"]="N/A"
        destinations.append(dict(destination))
    if destinations!=[]:
        for i in destinations:
            i["Health"]=i.pop("Health")
        return destinations

# Function calling collectors job failures
def get_jobs(group,header,url):
    jobs =[]
    request_jobs=requests.get(f"{url}/api/v1/m/{group}/jobs", headers=header)
    jobs_dict=request_jobs.json()["items"]
    for count in range(len(jobs_dict)):
        name=""
        group_id=""
        job={}
        for key,value in jobs_dict[count].items():
            if key=="args":
                name=value["id"]
                group_id=value["groupId"]
            if key=="status":
                job["Job ID"]=name
                job["Worker Group"]=group_id
                job["Status"]=value["state"]
        jobs.append(dict(job))
    unique_jobs=[]
    seen=set()
    for d in jobs:
        t=tuple(d.items())
        if t not in seen:
            seen.add(t)
            unique_jobs.append(d)
    return unique_jobs

# Function calling sources failures
def get_sources_config(group,header,url):
    source_re=defaultdict(list)
    sources=[]
    request_source=requests.get(f"{url}/api/v1/m/{group}/system/inputs", headers=header)
    source_dict=request_source.json()["items"]
    for count in range(len(source_dict)):
        sour=False
        preprocessing=False
        for key,value in source_dict[count].items():
            if key == "id":
                source_re["Source Name"]=value
            if key == "type":
                source_re["Type"]=value
            if key == "status":
                source_re["Health"]=value["health"]
        sources.append(dict(source_re))
    return sources

# Function calling routes table
def get_routes_config(group,header,url):
    final=""
    routes=[]
    routes_re=defaultdict(list)
    request_routes=requests.get(f"{url}/api/v1/m/{group}/routes", headers=header)
    routes_dict=request_routes.json()["items"]
    if "200" not in str(request_routes):
        print("No routes were set up in this deployment")
        return routes
    
    for i in range(int(request_routes.json()["count"])):
        for key,value in routes_dict[i].items():
            if key != "routes":
                continue
            for j in range(len(value)):
                for k,v in value[j].items():
                    if k == "name":
                        routes_re["Route Name"]=v
                    if k== "filter":
                        routes_re["Filter"]=v
                    elif k == "output":
                        routes_re["Output"]=v
                    elif k == "final":
                        final=v
                routes_re["Final?"]=final
                routes.append(dict(routes_re))
    routes=sorted(routes,key=itemgetter("Final?"))
    return routes

# Function calling Worker API process errors
def get_worker_API_Process_errors(header,url):
    # Use system/logs- match id- then print out the errors using /system/logs/{Ids}
    worker_API_logs=[]
    API_re=defaultdict(list)
    request_worker_API=requests.get(f"{url}/api/v1/m/default/system/logs/__instance__%3Acribl.log?lt=1706717711&filter=level%3D%3D%22error%22%20%26%26%20channel%20%3D%3D%20%22rpc%22", headers=header)
    API_dict=request_worker_API.json()["items"]
    for i in range(int(request_worker_API.json()["count"])):
        for k,v in API_dict[i].items():
            if k=="events":
                for n in v:
                    API_re["Channel"]=n["channel"]
                    API_re["Message"]=n["message"]
                    for t,l in n["msg"].items():
                        if t=="workerId":
                            API_re["Worker_ID"]=l
            worker_API_logs.append(dict(API_re))
    seen=set()
    while {} in worker_API_logs:
        worker_API_logs.remove({})
    unique_worker_API=[]
    for d in worker_API_logs:
        t=tuple(d.items())
        if t not in seen:
            seen.add(t)
            unique_worker_API.append(d)
    if (unique_worker_API!=[]):
        return unique_worker_API

# This is the main function that will call for all the other functions and print out our JSON script
def main(url,header,script_choice):
    # This function will call for a list of all groups in the server and run all the commands for each worker group
    groups = all_workgroups(header,url)
    
    if script_choice=="1":
        output_JSON={"Leader Node":{},"Workers":{},"Git":{},"Sources":{},"Destinations":{},"Destinations Hosts":{},"Output Routers":{},"QuickConnect":{},"Firewall Rules/Ports(Leader)":{},"Firewall Rules/Ports(Worker)":{},"Routes":{},"Pipelines":{},"Packs":{}, "Syslog":{}}
        #This for loop iterates through all the groups in the array to print out the relevant information needed from all Components
        output_JSON["Leader Node"]                             = get_leaders(header,url)
        output_JSON["Workers"]                                 = get_workers(header,url)
        # output_JSON["Git"]                                     = get_git(header,url)
        output_JSON["Firewall Rules/Ports(Leader)"]            = get_ports_leader(header,url)
        for group in groups:
            output_JSON["Sources"][group]                      = get_sources(group,header,url)
            output_JSON["Destinations"][group]                 = get_destinations(group,header,url)
            output_JSON["Destinations Hosts"][group]           = get_destinations_hosts(group,header,url)
            output_JSON["Output Routers"][group]               = get_output_routes(group,header,url)
            output_JSON["Firewall Rules/Ports(Worker)"][group] = get_ports(group,header,url)
            output_JSON["Routes"][group]                       = get_routes(group,header,url)
            output_JSON["Pipelines"][group]                    = get_pipelines(group,header,url)
            output_JSON["Packs"][group]                        = get_packs(group,header,url)
            output_JSON["QuickConnect"][group]                 = get_quickconnects(group,header,url)
            # output_JSON["Syslog"][group]                       = get_syslog(group,header,url)
        return output_JSON
    elif script_choice=="2":
        output_JSON={"Leader Node":{},"Workers":{}, "Git":{}, "Sources":{}, "Destinations":{}, "Jobs":{},"Pipelines":{}, "Routes":{}, "Packs":{},"API_Logs":{}}
        # output_JSON["Git"]                                     = get_git_config(header,url)
        output_JSON["Leader Node"]                             = get_leader_config(header,url)
        output_JSON["Workers"]                                 = get_workers_config(header,url)
        for group in groups:
            output_JSON["Sources"][group]                             = get_sources_config(group,header,url)
            output_JSON["Destinations"][group]                        = get_destinations_config(group,header,url)
            output_JSON["Jobs"][group]                                = get_jobs(group,header,url)
            output_JSON["Pipelines"][group]                           = get_pipelines(group, header, url)
            output_JSON["Routes"][group]                              = get_routes_config(group,header,url)
            output_JSON["Packs"][group]                               = get_packs(group,header,url)
        output_JSON["API_Logs"]                                = get_worker_API_Process_errors(header,url)
        return output_JSON
    