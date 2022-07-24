import os  
import re
from nltk.tag import StanfordNERTagger      
import json
from flask import Flask,request 
import nltk
import pandas as pd
from flask_cors import CORS, cross_origin
import pathlib
import requests
import datefinder
from datetime import datetime
from dateparser.search import search_dates 


#Finding the os directory and corret java path
#os.chdir("C:/Users/kartik.patnaik/Desktop/mobileapp/new_test/stanford-ner-2018-10-16/train1")
#java_path = "C:/Program Files/Java/jre1.8.0_191/bin/java.exe" 
#os.environ['JAVAHOME'] = java_path


#myCmd = 'java -jar C:/Users/kartik.patnaik/Desktop/mobileapp/new_test/stanford-ner-2018-10-16/stanford-ner.jar -mx4g -prop C:/Users/kartik.patnaik/Desktop/mobileapp/new_test/stanford-ner-2018-10-16/train/prop1.txt'
#os.system(myCmd)

#Flask code
#os.chdir("C:/Users/kartik.patnaik/Desktop/mobileapp/new_test/stanford-ner-2018-10-16/train2/")

#java_path = "java.exe"
#os.environ['JAVAHOME'] = java_path
#print(java_path)

# constants
CONNECT_HOST = os.environ.get("eka_connect_host")

app = Flask(__name__)
CORS(app, support_credentials=True)
@app.route('/nlp/processSentence')  
@cross_origin(supports_credentials=True)

#########################################################################
###############Stanford_base#############################################        
#########################################################################


def recognizer():
    headers_post = request.headers 
    appid = headers_post['appId']
    tenant_id = headers_post['X-TenantID']
    object_id = headers_post['X-Object']
    Authorization = headers_post['Authorization'] 
    
#    dct_prop = dict(line.strip().split('=') for line in open('properties.txt'))
    # URL = os.environ.get("properties_url_review")
    URL = str(CONNECT_HOST)+"/property/platform_url"
    response1 = requests.get(URL,headers={"Content-Type":"application/json","X-TenantID" : tenant_id})
    ENV_URL=response1.json()
    ENV_URL=ENV_URL["propertyValue"]
    vf_url = str(ENV_URL) +"/cac-security/api/userinfo"
    device_id = 'Device-Id'
    if device_id not in headers_post:
        headers_ = {'Authorization': Authorization}
    else:
        device_id_ = headers_post[device_id]
        headers_ = {'Authorization': Authorization, 'Device-Id': device_id_}
    response = requests.get(vf_url,headers=headers_)
    if response.status_code == 200:
        # ROOT_PATH = os.environ.get("path_root_url")
        ROOT_PATH = "/"
        os.chdir(ROOT_PATH)
        df2 = str(tenant_id)+"/"+str(appid)+"/"+str(object_id)
        cwd = os.getcwd()
        cwd = pathlib.PureWindowsPath(cwd)
        cwd = cwd.as_posix()
        if not os.path.exists(str(cwd) +"/" + str(df2)):
            os.makedirs(str(cwd) +"/" + str(df2))
        
        exists = os.path.isfile(str(df2) + '/corpus-tagging.ser.gz')
        if exists:
            jar = 'stanford-ner.jar'
            model = str(df2) + "/corpus-tagging.ser.gz"
            sentence = request.args.get('sentence')
#            sentence = sentence.lower()            
            if sentence !="":
                sentencex = "."
                sentence = sentence.replace('..','.')
                sentence = sentence+sentencex
                article = sentence[:]
                def find_match(sentence,df):
                    for i in range(df.shape[0]):
                        if sentence.find(df['rpl'][i]) !=-1:
                            sentence = sentence[:sentence.find(df['rpl'][i])] +  df['rpl1'][i] +  sentence[sentence.find(df['rpl'][i])+ len(df['rpl'][i]):]
                    return sentence
                
#                ls_1 = list(datefinder.find_dates(sentence, source=True))###########STart
                
                sentencek = sentence[:]
                stopwords=[' between ',' of ']
                for word in stopwords:
                    if word in sentencek:
                        sentencek=sentencek.replace(word," ")               
                
                ls3 = search_dates(sentencek)
                if ls3 == None:
                    ls3 = []
                else:
                    ls3 = [t[::-1] for t in ls3]
#                    ls3 = list(set(ls3+ls_1))

                if ls3!=[]:
                    ls4 = pd.DataFrame(ls3)
                    ls4 = ls4.drop_duplicates()
                    ls4.columns = ["rpl1","rpl"]
                    ls4["rpl1"] = pd.to_datetime(ls4["rpl1"], errors='coerce')
                    ls4 = ls4.query('rpl1 != "NaT"')
                    ls4["rpl1"] = ls4["rpl1"].dt.strftime('%Y-%m-%d')
                    ls4 = ls4[pd.to_numeric(ls4['rpl'], errors='coerce').isna()]
                    ls4["rpl2"] = pd.to_datetime(ls4["rpl"], errors='coerce')
                    ls4 = ls4.query('rpl2 != "NaT"')
                    ls4 = ls4.drop(columns=['rpl2'])
#                    ls4["rpl3"] = ls4["rpl"].dt.strftime('%Y-%m-%d')                    
#                    ls4['rpl'] = ls4['rpl'].astype('datetime64[ns]') 
                    ls4 = ls4.reset_index(drop = True)
                    ls4.index = ls4['rpl'].str.len()
                    ls4 = ls4.sort_index(ascending=True).reset_index(drop=True)
#                    ls4 = ls4.drop(['index'], axis=1)
                    ls4["rpl1"] = ls4["rpl1"].map(str)+ ' '
#                    sentence = re.sub('\s+',' ', sentence)
                    sentence = find_match(sentencek,ls4)                    
#                    return "Enter Text again remove - "#ENDDDDDDDDDDDDDDDDDD

                
                sentence1 = sentence.lower()
                ner_tagger = StanfordNERTagger(model, jar, encoding='utf8')
                words = nltk.word_tokenize(sentence1)
                results = ner_tagger.tag(words)
                filter = ['T']
                ls2 = [(x,y) for (x,y) in results if y not in filter] 
                df = pd.DataFrame(ls2)  
#                df = df.drop(df.index[[0]])  
#                df[2] = df[1].str.rsplit('#$#').str[1] 
#                df1 = df.dropna() 
#                df1[1] = df1[2]
#                df = df.append(df1) 
#                df = df.drop(df.columns[2],axis = "columns")
#                df[1] = df[1].str.rsplit('#$#').str[0] 
#                lst_ip1 = nltk.word_tokenize(sentence)
#                lst_ip3 = pd.DataFrame(lst_ip1)
#                df[0]=lst_ip3[0]                               
#                ls2 = list(df.itertuples(index=False, name=None))
                new = df[1].str.rsplit("#$#",n=10,expand = True)
                lst_ip1 = nltk.word_tokenize(sentence)
                lst_ip3 = pd.DataFrame(lst_ip1)
                df[0]=lst_ip3[0]
                new["sentence"]=lst_ip3[0] 
                df_new = pd.DataFrame()
                for label, content in new.items():
                    df_new1 = pd.DataFrame()
                    df_new1[0] = new["sentence"]
                    df_new1[1] = new[label]
                    df_new = df_new.append(df_new1, ignore_index=True)
                    df_new = df_new[df_new[0] != df_new[1]]
                    df_new = df_new.dropna()
                    df_new = df_new.drop_duplicates()
                    ls2 = list(df_new.itertuples(index=False, name=None))
#                    ls2 = list(set(ls2))
                    
                d = {}
                for a, b in ls2:
                    d.setdefault(b, []).append(a)
                new_abc = [ [ ' '.join(d.pop(b)), b ] for a, b in ls2 if b in d ]
                sub_dict = json.dumps(new_abc)
                
                if new_abc!=[]:
                    new_abc = pd.DataFrame(new_abc)
                    new_abc.columns = ['sentence', 'output']
                    new_abc = new_abc[new_abc.output != 'T']
                    new_abc = new_abc.set_index('output')['sentence'].to_dict()
                    sub_dict = json.dumps(new_abc)
                    df = pd.DataFrame({'input':[sentence]})
                    df["output"] = [ls2]
                    exists = os.path.isfile(str(df2) + "/user_entered.csv")
                    if exists:
                        df1=pd.read_csv(str(df2) + "/user_entered.csv")
                        df1 = df1.append(df) 
                        df1['New_ID'] = range(1, 1+len(df1))
                        df1.to_csv(str(df2) + "/user_entered.csv", sep=',',index=False)
            
                    else:
               
                        df.to_csv(str(df2) + "/user_entered.csv", sep=',',index=False)
                else:
                    sub_dict = {"blank":"blank"}
                    sub_dict = json.dumps(d)
            else:
                d = {}
                sub_dict = {"blank":"blank"}
                sub_dict = json.dumps(d)
                
        else:
            d = {}
            sub_dict = {"blank":"blank"}
            sub_dict = json.dumps(d)
            
        return sub_dict
    else:
        return 'Unsuccessful Auth'
#########################################################################
###############Recurrent Training########################################        
#########################################################################

@app.route('/nlp/tags',methods=['GET', 'POST'] ) 
@cross_origin(supports_credentials=True)


def upload():
    headers_post = request.headers 
    appid = headers_post['appId']
    tenant_id = headers_post['X-TenantID']
    object_id = headers_post['X-Object']
    Authorization = headers_post['Authorization'] 
    
#    dct_prop = dict(line.strip().split('=') for line in open('properties.txt'))
    # URL = os.environ.get("properties_url_review")
    URL = str(CONNECT_HOST)+"/property/platform_url"
    response1 = requests.get(URL,headers={"Content-Type":"application/json","X-TenantID" : tenant_id})
    ENV_URL=response1.json()
    ENV_URL=ENV_URL["propertyValue"]
    vf_url = str(ENV_URL) +"/cac-security/api/userinfo"
    device_id = 'Device-Id'
    if device_id not in headers_post:
        headers_ = {'Authorization': Authorization}
    else:
        device_id_ = headers_post[device_id]
        headers_ = {'Authorization': Authorization, 'Device-Id': device_id_}
    response = requests.get(vf_url,headers=headers_)#    df1=pd.read_csv("C:/Users/kartik.patnaik/Desktop/mobileapp/new_test/stanford-ner-2018-10-16/train2/Book1.csv")
    if response.status_code == 200:
        ROOT_PATH = os.environ.get("path_root_url")
        os.chdir(ROOT_PATH)
        df2 = str(tenant_id)+"/"+str(appid)+"/"+str(object_id)
        user_input = request.get_json()
        if user_input != {}:
            wanted_keys = ['sentence']
            wanted_keys1 = ['Tags']
            sentence = {k: user_input[k] for k in set(wanted_keys) & set(user_input.keys())}
            sentence = list( sentence.values() )[0]
            
            if sentence != None and sentence != '':
                sentence = sentence.lower()  
                article = sentence[:]
                def find_match(sentence,df):
                    for i in range(df.shape[0]):
                        if sentence.find(df['rpl'][i]) !=-1:
                            sentence = sentence[:sentence.find(df['rpl'][i])] +  df['rpl1'][i] +  sentence[sentence.find(df['rpl'][i])+ len(df['rpl'][i]):]
                    return sentence
               
#                ls_1 = list(datefinder.find_dates(sentence, source=True))#####AGAIN
                sentencek = sentence[:]
                stopwords=[' between ',' of ',' to ']
                for word in stopwords:
                    if word in sentencek:
                        sentencek=sentencek.replace(word," ")   
                
                ls3 = search_dates(sentencek)
                if ls3 == None:
                    ls3 = []
                else:
                    ls3 = [t[::-1] for t in ls3]
#                    ls3 = list(set(ls3+ls_1))

                if ls3!=[]:
                    ls4 = pd.DataFrame(ls3)
                    ls4 = ls4.drop_duplicates()
                    ls4.columns = ["rpl1","rpl"]
                    ls4["rpl1"] = pd.to_datetime(ls4["rpl1"], errors='coerce')
                    ls4 = ls4.query('rpl1 != "NaT"')
                    ls4["rpl1"] = ls4["rpl1"].dt.strftime('%Y-%m-%d')
                    ls4 = ls4[pd.to_numeric(ls4['rpl'], errors='coerce').isna()]
                    ls4["rpl2"] = pd.to_datetime(ls4["rpl"], errors='coerce')
                    ls4 = ls4.query('rpl2 != "NaT"')
                    ls4 = ls4.drop(columns=['rpl2'])
#                    ls4["rpl3"] = ls4["rpl"].dt.strftime('%Y-%m-%d')                    
#                    ls4['rpl'] = ls4['rpl'].astype('datetime64[ns]') 
                    ls4 = ls4.reset_index(drop = True)
                    ls4.index = ls4['rpl'].str.len()
                    ls4 = ls4.sort_index(ascending=True).reset_index(drop=True)
#                    ls4 = ls4.drop(['index'], axis=1)
                    ls4["rpl1"] = ls4["rpl1"].map(str)+ ' '
#                    sentence = re.sub('\s+',' ', sentence)
                    sentence = find_match(sentencek,ls4)                    
#                    return "Enter Text again remove - " #######END


                tags = {k: user_input[k] for k in set(wanted_keys1) & set(user_input.keys())}
                tags = list( tags.values() )[0]
                tags = {k:str(v) for k, v in tags.items()}
                def lower_dict(d):
                    new_dict = dict((k, v.lower()) for k, v in d.items())
                    return new_dict
                tags = lower_dict(tags)
                new_list = [] 
                for key, value in tags.items():
                    new_list.append([key, value])
                ui1 = pd.DataFrame(new_list)
                ui1.columns = ['action','sentence']
                ui1["sentence1"] = ""
               
                for label, content in ui1["sentence"].items():
                    if search_dates(ui1["sentence"][label]) != None:
                        ui1["sentence1"][label] = "Found"
                    else:
                        ui1["sentence1"][label] = "Not Found"
                
                uik = ui1[ui1["sentence1"]=="Found"]
#                for label, content in uik["sentence"].items():
#                    if list(datefinder.find_dates(uik["sentence"][label])) != []:
#                        uik["sentence"][label] = list(datefinder.find_dates(uik["sentence"][label]))[0]
                uik["sentence"] = uik["sentence"].astype(str).str[:-6] #Strip time zone        
                uik["sentence"] = pd.to_datetime(uik["sentence"], errors='coerce')
                uik["sentence"] = uik["sentence"].dt.strftime('%Y-%m-%d')            
                uik = uik.query('sentence != "NaT"')
                uik = uik.drop(['sentence1'], axis=1)
                ui1 = ui1.drop(['sentence1'], axis=1)
                ui1 = ui1.append(uik, ignore_index=True) 
#                ui1 = ui1.drop_duplicates(subset='action', keep="last")(keep an eye on)
                
#                ui1[['sentence1','sentence2']] = ui1['sentence'].str.split(' ', n=1, expand=True)
#                ui2 = ui1[['sentence1','action']]
#                ui3 = ui1[['sentence2','action']]
#                #ui3.dropna(subset=['action'],inplace = True) 
#                ui3.dropna(inplace = True)    
#                ui2.columns = ['sentence', 'action']
#                ui3.columns = ['sentence', 'action']
#                ui4 = ui2.append(ui3, ignore_index=True)            
#                lst_ip1 = nltk.word_tokenize(sentence)
#                lst_ip3 = pd.DataFrame(lst_ip1)
#                lst_ip3.columns = ['sentence']


                k = ui1.apply(lambda row: nltk.word_tokenize(row['sentence']), axis=1)
                k = pd.DataFrame(k)
                k.columns = ["sentence"]
                new = k.sentence.apply(pd.Series)
                new["action"]=ui1["action"]
                df_new = pd.DataFrame()
                for label, content in new.items():
                    df_new1 = pd.DataFrame()
                    df_new1[0] = new["action"]
                    df_new1[1] = new[label]
                    df_new = df_new.append(df_new1, ignore_index=True)
                    df_new = df_new[df_new[0] != df_new[1]]
                    df_new = df_new.dropna()
                lst_ip1 = nltk.word_tokenize(sentence)
                lst_ip3 = pd.DataFrame(lst_ip1)
                lst_ip3.columns = ['sentence']
                df_new.columns = ['action','sentence']
                #################################################join
                result = pd.merge(lst_ip3,
                                 df_new,
                                 on='sentence', 
                                 how='left')
#                result = pd.merge(lst_ip3,
#                                 ui4,
#                                 on='sentence', 
#                                 how='left')                
                
                result['action'] = result['action'].fillna('o')
                result['key'] = (result['sentence'] != result['sentence'].shift(1)).astype(int).cumsum()
                result =result.groupby(['key', 'sentence'])['action'].apply('#$#'.join).to_frame()
                result = result.reset_index()
                result['sentence'] = result['sentence'].map(str) + " " + result["action"]
                user_input3 = result['sentence']
                user_input3.to_csv(str(df2) +'/user_input3.tsv',header=False, index=False)
                user_input3 = pd.read_csv(str(df2) +'/user_input3.tsv', sep='\t',header = None)
                exists = os.path.isfile(str(df2) +'/dummy-corpus1.tsv')
                exists1 = os.path.isfile(str(df2) +'/dummy-corpus2.tsv')
                if exists and not exists1:
                    pa1 = pd.read_csv(str(df2) +'/dummy-corpus1.tsv', sep='\t',header = None)
                    pa2 = pa1.append(user_input3,ignore_index=True)
                    pa2 = pa2.append([". o"])
                elif exists1 and exists:
                    pa1 = pd.read_csv(str(df2) +'/dummy-corpus2.tsv', sep='\t',header = None)
                    pa2 = pa1.append(user_input3,ignore_index=True)
                    pa2 = pa2.append([". o"])  
                else:
                    pa2 = user_input3
                    pa2 = pa2.append([". o"])
                    
                pa2.to_csv(str(df2) +'/dummy-corpus1.tsv',header=False, index=False)
                cwd = os.getcwd()
                cwd = pathlib.PureWindowsPath(cwd)
                cwd = cwd.as_posix()
                prop = "trainFile = "+ str(cwd) +"/" + str(df2) + """/dummy-corpus1.tsv
                serializeTo ="""+ str(cwd) +"/" + str(df2) +"""/corpus-tagging.ser.gz
                map = word=0,answer=1
                
                useClassFeature=true
                useWord=true
                useNGrams=true
                noMidNGrams=true
                maxNGramLeng=6
                usePrev=true
                useNext=true
                useSequences=true
                usePrevSequences=true
                maxLeft=1
                useTypeSeqs=true
                useTypeSeqs2=true
                useTypeySequences=true
                wordShape=chris2useLC
                useDisjunctive=true"""
                
                file = open( str(cwd) +"/" + str(df2)+'/prop2.txt', 'w')
                file.write(prop)
                file.close()
                myCmd = 'java -jar stanford-ner.jar -mx4g -prop' " "  + str(df2) + '/prop2.txt'
                os.system(myCmd)   
    
                return 'Recurrent Training on Completed Successfully'
            else:
                return 'No Data to be trained on NULL'
    else:
        return 'Unsuccessful Auth'

#########################################################################
###############blank Trained#############################################       
#########################################################################
@app.route('/nlp/reset')
@cross_origin(supports_credentials=True) 


def blank_trained(): 
    headers_post = request.headers 
    appid = headers_post['appId']
    tenant_id = headers_post['X-TenantID']
    object_id = headers_post['X-Object']
    Authorization = headers_post['Authorization']  
     
#    dct_prop = dict(line.strip().split('=') for line in open('properties.txt'))
#    os.environ["URL"] = "integ.ekaanalytics.com:3140"
    # URL = os.environ.get("properties_url_review")
    URL = str(CONNECT_HOST)+"/property/platform_url"
    response1 = requests.get(URL,headers={"Content-Type":"application/json","X-TenantID" : tenant_id})
    ENV_URL=response1.json()
    ENV_URL=ENV_URL["propertyValue"]
    vf_url = str(ENV_URL) +"/cac-security/api/userinfo"
    device_id = 'Device-Id'
    if device_id not in headers_post:
        headers_ = {'Authorization': Authorization}
    else:
        device_id_ = headers_post[device_id]
        headers_ = {'Authorization': Authorization, 'Device-Id': device_id_}
    response = requests.get(vf_url,headers=headers_)

    if response.status_code == 200:    
    #    df1=pd.read_csv("C:/Users/kartik.patnaik/Desktop/mobileapp/new_test/stanford-ner-2018-10-16/train2/Book1.csv")
    #    df2 = df1[(df1['appid']== appid) & (df1['tenant_id']== tenant_id) & (df1['object_id']== object_id)]['path'].values[0]
        ROOT_PATH = os.environ.get("path_root_url")
#        response_url = requests.get(ROOT_URL,headers={"Authorization":Authorization,"X-TenantID":tenant_id})
#        product=response_url.json()
#        root_product_url = product["propertyValue"]
        os.chdir(ROOT_PATH)
        df2 = str(tenant_id)+"/"+str(appid)+"/"+str(object_id)
        cwd = os.getcwd()
        cwd = pathlib.PureWindowsPath(cwd)
        cwd = cwd.as_posix()
        if not os.path.exists(str(cwd) +"/" + str(df2)):
            os.makedirs(str(cwd) +"/" + str(df2))
        pa2 = pd.DataFrame(index=range(1))
        pa2.to_csv(str(cwd) +"/" +str(df2) +'/dummy-corpus3.tsv',header=False, index=False)
        prop = "trainFile = "+ str(cwd) +"/" + str(df2) + """/dummy-corpus3.tsv
        serializeTo ="""+ str(cwd) +"/" + str(df2) +"""/corpus-tagging.ser.gz
        map = word=0,answer=1
        
        useClassFeature=true
        useWord=true
        useNGrams=true
        noMidNGrams=true
        maxNGramLeng=6
        usePrev=true
        useNext=true
        useSequences=true
        usePrevSequences=true
        maxLeft=1
        useTypeSeqs=true
        useTypeSeqs2=true
        useTypeySequences=true
        wordShape=chris2useLC
        useDisjunctive=true"""
        
        file = open( str(cwd) +"/" + str(df2)+'/prop3.txt', 'w')
        file.write(prop)
        file.close()
        myCmd = 'java -jar stanford-ner.jar -mx4g -prop' " "  + str(df2) + '/prop3.txt'
        os.system(myCmd)  
        if os.system(myCmd)==0:
            return 'Recurrent Training on blank for Completed Successfully'
        else:
            
            return 'Recurrent training Failed check Header'
    else:
        return 'Unsuccessful Auth'


#########################################################################
###############Raw Trained###############################################       
#########################################################################
@app.route('/raw')
@cross_origin(supports_credentials=True)

def raw():
    headers_post = request.headers 
    appid = headers_post['appId']
    tenant_id = headers_post['X-TenantID']
    object_id = headers_post['X-Object']
    Authorization = headers_post['Authorization'] 
    
#    dct_prop = dict(line.strip().split('=') for line in open('properties.txt'))
    # URL = os.environ.get("properties_url_review")
    URL = str(CONNECT_HOST)+"/property/platform_url"
    response1 = requests.get(URL,headers={"Content-Type":"application/json","X-TenantID" : tenant_id})
    ENV_URL=response1.json()
    ENV_URL=ENV_URL["propertyValue"]
    vf_url = str(ENV_URL) +"/cac-security/api/userinfo"
    response = requests.get(vf_url,headers={"Authorization":Authorization})
#    df1=pd.read_csv("C:/Users/kartik.patnaik/Desktop/mobileapp/new_test/stanford-ner-2018-10-16/train2/Book1.csv")
#    df2 = df1[(df1['appid']== appid) & (df1['tenant_id']== tenant_id) & (df1['object_id']== object_id)]['path'].values[0]
    if response.status_code == 200: 
        ROOT_PATH = os.environ.get("path_root_url")
#        response_url = requests.get(ROOT_URL,headers={"Authorization":Authorization,"X-TenantID":tenant_id})
#        product=response_url.json()
#        root_product_url = product["propertyValue"]
        os.chdir(ROOT_PATH)
        df2 = str(tenant_id)+"/"+str(appid)+"/"+str(object_id)
        cwd = os.getcwd()
        cwd = pathlib.PureWindowsPath(cwd)
        cwd = cwd.as_posix()
        if not os.path.exists(str(cwd) +"/" + str(df2)):
            os.makedirs(str(cwd) +"/" + str(df2))
            pa2 = pd.DataFrame(index=range(1))
            pa2.to_csv(str(cwd) +"/" +str(df2) +'/dummy-corpus1.tsv',header=False, index=False)
            prop = "trainFile = "+ str(cwd) +"/" + str(df2) + """/dummy-corpus1.tsv
            serializeTo ="""+ str(cwd) +"/" + str(df2) +"""/corpus-tagging.ser.gz
            map = word=0,answer=1
            
            useClassFeature=true
            useWord=true
            useNGrams=true
            noMidNGrams=true
            maxNGramLeng=6
            usePrev=true
            useNext=true
            useSequences=true
            usePrevSequences=true
            maxLeft=1
            useTypeSeqs=true
            useTypeSeqs2=true
            useTypeySequences=true
            wordShape=chris2useLC
            useDisjunctive=true"""
            
            file = open( str(cwd) +"/" + str(df2)+'/prop1.txt', 'w')
            file.write(prop)
            file.close()
            myCmd = 'java -jar stanford-ner.jar -mx4g -prop' " "  + str(df2) + '/prop1.txt'
            os.system(myCmd)
        else:         
            prop = "trainFile = "+ str(cwd) +"/" + str(df2) + """/dummy-corpus1.tsv
            serializeTo ="""+ str(cwd) +"/" + str(df2) +"""/corpus-tagging.ser.gz
            map = word=0,answer=1
            
            useClassFeature=true
            useWord=true
            useNGrams=true
            noMidNGrams=true
            maxNGramLeng=6
            usePrev=true
            useNext=true
            useSequences=true
            usePrevSequences=true
            maxLeft=1
            useTypeSeqs=true
            useTypeSeqs2=true
            useTypeySequences=true
            wordShape=chris2useLC
            useDisjunctive=true"""
            
            file = open( str(cwd) +"/" + str(df2)+'/prop1.txt', 'w')
            file.write(prop)
            file.close()
            myCmd = 'java -jar stanford-ner.jar -mx4g -prop' " "  + str(df2) + '/prop1.txt'
            os.system(myCmd)  
        if os.system(myCmd)==0:
            return 'Raw Training on blank Completed Successfully'
        else:
            
            return 'Recurrent training Failed check Header or existance of input File'        
    else:
        return 'Unsuccessful Auth'

#if __name__ == '__main__': 
#    app.debug = True
#    app.run(host = '0.0.0.0',port = 1919)

#########################################################################
###############Bulk Training#############################################        
#########################################################################
@app.route('/nlp/bulk_tags',methods=['GET', 'POST']) 
@cross_origin(supports_credentials=True)


def upload_bulk():
    headers_post = request.headers 
    appid = headers_post['appId']
    tenant_id = headers_post['X-TenantID']
    object_id = headers_post['X-Object']
    Authorization = headers_post['Authorization'] 
    
#    dct_prop = dict(line.strip().split('=') for line in open('properties.txt'))
    # URL = os.environ.get("properties_url_review")
    URL = str(CONNECT_HOST)+"/property/platform_url"
    response1 = requests.get(URL,headers={"Content-Type":"application/json","X-TenantID" : tenant_id})
    ENV_URL=response1.json()
    print(ENV_URL)
    ENV_URL=ENV_URL["propertyValue"]
    vf_url = str(ENV_URL) +"/cac-security/api/userinfo"
    device_id = 'Device-Id'
    if device_id not in headers_post:
        headers_ = {'Authorization': Authorization}
    else:
        device_id_ = headers_post[device_id]
        headers_ = {'Authorization': Authorization, 'Device-Id': device_id_}
    response = requests.get(vf_url,headers=headers_)#    df1=pd.read_csv("C:/Users/kartik.patnaik/Desktop/mobileapp/new_test/stanford-ner-2018-10-16/train2/Book1.csv")
    if response.status_code == 200:
        # ROOT_PATH = os.environ.get("path_root_url")
        ROOT_PATH = '/'
        os.chdir(ROOT_PATH)
        df2 = str(tenant_id)+"/"+str(appid)+"/"+str(object_id)
        cwd = os.getcwd()
        cwd = pathlib.PureWindowsPath(cwd)
        cwd = cwd.as_posix()
        if not os.path.exists(str(cwd) +"/" + str(df2)):
            os.makedirs(str(cwd) +"/" + str(df2))
        user_input = request.get_json()
        if user_input != []:
            for i in range(len(user_input)):        
                user_input_1 = user_input[i]
                wanted_keys = ['sentence']
                wanted_keys1 = ['Tags']
                sentence = {k: user_input_1[k] for k in set(wanted_keys) & set(user_input_1.keys())}
                sentence = list( sentence.values() )[0]
            
                if sentence != None and sentence != '':
                    sentence = sentence.lower()  
        #                sentence = sentence.replace('buy','purchase')
        #                sentence = sentence.replace('sell','sale')
                    insensitive_hippo = re.compile(re.escape('buy'), re.IGNORECASE)
                    sentence = insensitive_hippo.sub('purchase', sentence)
                    insensitive_hippo = re.compile(re.escape('sell'), re.IGNORECASE)
                    sentence = insensitive_hippo.sub('sale', sentence) 
                    article = sentence[:]
                    def find_match(sentence,df):
                        for i in range(df.shape[0]):
                            if sentence.find(df['rpl'][i]) !=-1:
                                sentence = sentence[:sentence.find(df['rpl'][i])] +  df['rpl1'][i] +  sentence[sentence.find(df['rpl'][i])+ len(df['rpl'][i]):]
                        return sentence
                   
        #                ls_1 = list(datefinder.find_dates(sentence, source=True))#####AGAIN
                    sentencek = sentence[:]
                    stopwords=[' between ',' of ',' to ']
                    for word in stopwords:
                        if word in sentencek:
                            sentencek=sentencek.replace(word," ")   
                    
                    ls3 = search_dates(sentencek)
                    if ls3 == None:
                        ls3 = []
                    else:
                        ls3 = [t[::-1] for t in ls3]
        #                    ls3 = list(set(ls3+ls_1))
        
                    if ls3!=[]:
                        ls4 = pd.DataFrame(ls3)
                        ls4 = ls4.drop_duplicates()
                        ls4.columns = ["rpl1","rpl"]
                        ls4["rpl1"] = pd.to_datetime(ls4["rpl1"], errors='coerce',utc=True)
                        ls4 = ls4.query('rpl1 != "NaT"')
                        ls4["rpl1"] = ls4["rpl1"].dt.strftime('%Y-%m-%d')
                        ls4 = ls4[pd.to_numeric(ls4['rpl'], errors='coerce').isna()]
                        ls4["rpl2"] = pd.to_datetime(ls4["rpl"], errors='coerce',utc = True)
                        ls4 = ls4.query('rpl2 != "NaT"')
                        ls4 = ls4.drop(columns=['rpl2'])
        #                    ls4["rpl3"] = ls4["rpl"].dt.strftime('%Y-%m-%d')                    
        #                    ls4['rpl'] = ls4['rpl'].astype('datetime64[ns]') 
                        ls4 = ls4.reset_index(drop = True)
                        ls4.index = ls4['rpl'].str.len()
                        ls4 = ls4.sort_index(ascending=True).reset_index(drop=True)
            #                    ls4 = ls4.drop(['index'], axis=1)
                        ls4["rpl1"] = ls4["rpl1"].map(str)+ ' '
#                        sentence = re.sub('\s+',' ', sentence)
                        sentence = find_match(sentencek,ls4)                    
        #                    return "Enter Text again remove - " #######END
        
        
                    tags = {k: user_input_1[k] for k in set(wanted_keys1) & set(user_input_1.keys())}
                    tags = list( tags.values() )[0]
                    tags = {k:str(v) for k, v in tags.items()}
                    def lower_dict(d):
                        new_dict = dict((k, v.lower()) for k, v in d.items())
                        return new_dict
                    tags = lower_dict(tags)
                    new_list = [] 
                    for key, value in tags.items():
                        new_list.append([key, value])
                    ui1 = pd.DataFrame(new_list)
                    ui1.columns = ['action','sentence']
                    ui1["sentence1"] = ""
                   
                    for label, content in ui1["sentence"].items():
                        if search_dates(ui1["sentence"][label]) != None:
                            ui1["sentence1"][label] = "Found"
                        else:
                            ui1["sentence1"][label] = "Not Found"
                    
                    uik = ui1[ui1["sentence1"]=="Found"]
        #                for label, content in uik["sentence"].items():
        #                    if list(datefinder.find_dates(uik["sentence"][label])) != []:
        #                        uik["sentence"][label] = list(datefinder.find_dates(uik["sentence"][label]))[0]
                    uik["sentence"] = uik["sentence"].astype(str).str[:-6] #Strip time zone        
                    uik["sentence"] = pd.to_datetime(uik["sentence"], errors='coerce')
                    uik["sentence"] = uik["sentence"].dt.strftime('%Y-%m-%d')            
                    uik = uik.query('sentence != "NaT"')
                    uik = uik.drop(['sentence1'], axis=1)
                    ui1 = ui1.drop(['sentence1'], axis=1)
                    ui1 = ui1.append(uik, ignore_index=True) 
        #                ui1 = ui1.drop_duplicates(subset='action', keep="last")(keep an eye on)
                    
        #                ui1[['sentence1','sentence2']] = ui1['sentence'].str.split(' ', n=1, expand=True)
        #                ui2 = ui1[['sentence1','action']]
        #                ui3 = ui1[['sentence2','action']]
        #                #ui3.dropna(subset=['action'],inplace = True) 
        #                ui3.dropna(inplace = True)    
        #                ui2.columns = ['sentence', 'action']
        #                ui3.columns = ['sentence', 'action']
        #                ui4 = ui2.append(ui3, ignore_index=True)            
        #                lst_ip1 = nltk.word_tokenize(sentence)
        #                lst_ip3 = pd.DataFrame(lst_ip1)
        #                lst_ip3.columns = ['sentence']
        
                    k = ui1.apply(lambda row: nltk.word_tokenize(str(row['sentence'])), axis=1)
                    k = pd.DataFrame(k)
                    k.columns = ["sentence"]
                    new = k.sentence.apply(pd.Series)
                    new["action"]=ui1["action"]
                    df_new = pd.DataFrame()
                    for label, content in new.items():
                        df_new1 = pd.DataFrame()
                        df_new1[0] = new["action"]
                        df_new1[1] = new[label]
                        df_new = df_new.append(df_new1, ignore_index=True)
                        df_new = df_new[df_new[0] != df_new[1]]
                        df_new = df_new.dropna()
                    lst_ip1 = nltk.word_tokenize(sentence)
                    lst_ip3 = pd.DataFrame(lst_ip1)
                    lst_ip3.columns = ['sentence']
                    df_new.columns = ['action','sentence']
                    #################################################join
                    result = pd.merge(lst_ip3,
                                     df_new,
                                     on='sentence', 
                                     how='left')
        #                result = pd.merge(lst_ip3,
        #                                 ui4,
        #                                 on='sentence', 
        #                                 how='left')                
                    
                    result['action'] = result['action'].fillna('o')
                    result['key'] = (result['sentence'] != result['sentence'].shift(1)).astype(int).cumsum()
                    result =result.groupby(['key', 'sentence'])['action'].apply('#$#'.join).to_frame()
                    result = result.reset_index()
                    result['sentence'] = result['sentence'].map(str) + " " + result["action"]
                    user_input3 = result['sentence']
                    user_input3.to_csv(str(df2) +'/user_input3.tsv',header=False, index=False)
                    user_input3 = pd.read_csv(str(df2) +'/user_input3.tsv', sep='\t',header = None)
                    exists = os.path.isfile(str(df2) +'/dummy-corpus1.tsv')
                    exists1 = os.path.isfile(str(df2) +'/dummy-corpus2.tsv')
                    if exists and not exists1:
                        pa1 = pd.read_csv(str(df2) +'/dummy-corpus1.tsv', sep='\t',header = None)
                        pa2 = pa1.append(user_input3,ignore_index=True)
                        pa2 = pa2.append([". o"])
                    elif exists1 and exists:
                        pa1 = pd.read_csv(str(df2) +'/dummy-corpus2.tsv', sep='\t',header = None)
                        pa2 = pa1.append(user_input3,ignore_index=True)
                        pa2 = pa2.append([". o"])  
                    else:
                        pa2 = user_input3
                        pa2 = pa2.append([". o"])
                        
                    pa2.to_csv(str(df2) +'/dummy-corpus1.tsv',header=False, index=False)
                
            cwd = os.getcwd()
            cwd = pathlib.PureWindowsPath(cwd)
            cwd = cwd.as_posix()
            prop = "trainFile = "+ str(cwd) +"/" + str(df2) + """/dummy-corpus1.tsv
            serializeTo ="""+ str(cwd) +"/" + str(df2) +"""/corpus-tagging.ser.gz
            map = word=0,answer=1
            
            useClassFeature=true
            useWord=true
            useNGrams=true
            noMidNGrams=true
            maxNGramLeng=6
            usePrev=true
            useNext=true
            useSequences=true
            usePrevSequences=true
            maxLeft=1
            useTypeSeqs=true
            useTypeSeqs2=true
            useTypeySequences=true
            wordShape=chris2useLC
            useDisjunctive=true"""
            
            file = open( str(cwd) +"/" + str(df2)+'/prop2.txt', 'w')
            file.write(prop)
            file.close()
            myCmd = 'java -jar stanford-ner.jar -mx4g -prop' " "  + str(df2) + '/prop2.txt'
            os.system(myCmd)   
        
            return 'Recurrent Training Completed Successfully'
        
        else:
                return 'No Data to be trained on NULL'
    else:
        return 'Unsuccessful Auth'
        

#########################################################################
###############Initial Training##########################################        
#########################################################################
@app.route('/nlp/initial_training',methods=['GET', 'POST']) 
@cross_origin(supports_credentials=True)


def initial_bulk_load():
    headers_post = request.headers 
    appid = headers_post['appId']
    tenant_id = headers_post['X-TenantID']
    object_id = headers_post['X-Object']
    Authorization = headers_post['Authorization'] 
    
#    dct_prop = dict(line.strip().split('=') for line in open('properties.txt'))
    # URL = os.environ.get("properties_url_review")
    URL = str(CONNECT_HOST)+"/property/platform_url"
    response1 = requests.get(URL,headers={"Content-Type":"application/json","X-TenantID" : tenant_id})
    ENV_URL=response1.json()
    ENV_URL=ENV_URL["propertyValue"]
    vf_url = str(ENV_URL) +"/cac-security/api/userinfo"
    device_id = 'Device-Id'
    if device_id not in headers_post:
        headers_ = {'Authorization': Authorization}
    else:
        device_id_ = headers_post[device_id]
        headers_ = {'Authorization': Authorization, 'Device-Id': device_id_}
    response = requests.get(vf_url,headers=headers_)#    df1=pd.read_csv("C:/Users/kartik.patnaik/Desktop/mobileapp/new_test/stanford-ner-2018-10-16/train2/Book1.csv")
    if response.status_code == 200:
        ROOT_PATH = os.environ.get("path_root_url")
        os.chdir(ROOT_PATH)
        df2 = str(tenant_id)+"/"+str(appid)+"/"+str(object_id)
        cwd = os.getcwd()
        cwd = pathlib.PureWindowsPath(cwd)
        cwd = cwd.as_posix()
        if not os.path.exists(str(cwd) +"/" + str(df2)):
            os.makedirs(str(cwd) +"/" + str(df2))
#        user_input = request.get_json()
        file = open('pre_load.txt', 'r')
        if file.mode == 'r':
            contents =file.read()
        df = pd.DataFrame([x.split('::') for x in contents.split('\n')])
        df = df.rename(columns=df.iloc[0]).drop(df.index[0])
        
        if (len(df['appid'].str.contains(appid))>0):
            df = df[df['appid'].str.contains(appid)]
            if (len(df['objectid'].str.contains(object_id))>0):
                df = df[df['objectid'].str.contains(object_id)]
                df = df[:1]
                JSON_NAME = df["JSON_name"]
                JSON_NAME.reset_index(drop=True, inplace=True)
                JSON_NAME = JSON_NAME[0]
            else:
                JSON_NAME = ""
        
        if JSON_NAME !="":
            with open(JSON_NAME+".json") as json_file:
                user_input = json.load(json_file)    
        else:
            user_input = []
        
        if user_input != []:
            for i in range(len(user_input)):        
                user_input_1 = user_input[i]
                wanted_keys = ['sentence']
                wanted_keys1 = ['Tags']
                sentence = {k: user_input_1[k] for k in set(wanted_keys) & set(user_input_1.keys())}
                sentence = list( sentence.values() )[0]
            
                if sentence != None and sentence != '':
                    sentence = sentence.lower()  
        #                sentence = sentence.replace('buy','purchase')
        #                sentence = sentence.replace('sell','sale')
                    insensitive_hippo = re.compile(re.escape('buy'), re.IGNORECASE)
                    sentence = insensitive_hippo.sub('purchase', sentence)
                    insensitive_hippo = re.compile(re.escape('sell'), re.IGNORECASE)
                    sentence = insensitive_hippo.sub('sale', sentence) 
                    article = sentence[:]
                    def find_match(sentence,df):
                        for i in range(df.shape[0]):
                            if sentence.find(df['rpl'][i]) !=-1:
                                sentence = sentence[:sentence.find(df['rpl'][i])] +  df['rpl1'][i] +  sentence[sentence.find(df['rpl'][i])+ len(df['rpl'][i]):]
                        return sentence
                   
        #                ls_1 = list(datefinder.find_dates(sentence, source=True))#####AGAIN
                    sentencek = sentence[:]
                    stopwords=[' between ',' of ']
                    for word in stopwords:
                        if word in sentencek:
                            sentencek=sentencek.replace(word," ")   
                    
                    ls3 = search_dates(sentencek)
                    if ls3 == None:
                        ls3 = []
                    else:
                        ls3 = [t[::-1] for t in ls3]
        #                    ls3 = list(set(ls3+ls_1))
        
                    if ls3!=[]:
                        ls4 = pd.DataFrame(ls3)
                        ls4 = ls4.drop_duplicates()
                        ls4.columns = ["rpl1","rpl"]
                        ls4["rpl1"] = pd.to_datetime(ls4["rpl1"], errors='coerce',utc = True)
                        ls4 = ls4.query('rpl1 != "NaT"')
                        ls4["rpl1"] = ls4["rpl1"].dt.strftime('%Y-%m-%d')
                        ls4 = ls4[pd.to_numeric(ls4['rpl'], errors='coerce').isna()]
                        ls4["rpl2"] = pd.to_datetime(ls4["rpl"], errors='coerce',utc = True)
                        ls4 = ls4.query('rpl2 != "NaT"')
                        ls4 = ls4.drop(columns=['rpl2'])
        #                    ls4["rpl3"] = ls4["rpl"].dt.strftime('%Y-%m-%d')                    
        #                    ls4['rpl'] = ls4['rpl'].astype('datetime64[ns]') 
                        ls4 = ls4.reset_index(drop = True)
                        ls4.index = ls4['rpl'].str.len()
                        ls4 = ls4.sort_index(ascending=True).reset_index(drop=True)
        #                    ls4 = ls4.drop(['index'], axis=1)
                        ls4["rpl1"] = ls4["rpl1"].map(str)+ ' '
                        sentence = find_match(sentencek,ls4)                    
        #                    return "Enter Text again remove - " #######END
        
        
                    tags = {k: user_input_1[k] for k in set(wanted_keys1) & set(user_input_1.keys())}
                    tags = list( tags.values() )[0]
                    tags = {k:str(v) for k, v in tags.items()}
                    def lower_dict(d):
                        new_dict = dict((k, v.lower()) for k, v in d.items())
                        return new_dict
                    tags = lower_dict(tags)
                    new_list = [] 
                    for key, value in tags.items():
                        new_list.append([key, value])
                    ui1 = pd.DataFrame(new_list)
                    ui1.columns = ['action','sentence']
                    ui1["sentence1"] = ""
                   
                    for label, content in ui1["sentence"].items():
                        if search_dates(ui1["sentence"][label]) != None:
                            ui1["sentence1"][label] = "Found"
                        else:
                            ui1["sentence1"][label] = "Not Found"
                    
                    uik = ui1[ui1["sentence1"]=="Found"]
        #                for label, content in uik["sentence"].items():
        #                    if list(datefinder.find_dates(uik["sentence"][label])) != []:
        #                        uik["sentence"][label] = list(datefinder.find_dates(uik["sentence"][label]))[0]
                    uik["sentence"] = uik["sentence"].astype(str).str[:-6] #Strip time zone        
                    uik["sentence"] = pd.to_datetime(uik["sentence"], errors='coerce')
                    uik["sentence"] = uik["sentence"].dt.strftime('%Y-%m-%d')            
                    uik = uik.query('sentence != "NaT"')
                    uik = uik.drop(['sentence1'], axis=1)
                    ui1 = ui1.drop(['sentence1'], axis=1)
                    ui1 = ui1.append(uik, ignore_index=True) 
        #                ui1 = ui1.drop_duplicates(subset='action', keep="last")(keep an eye on)
                    
        #                ui1[['sentence1','sentence2']] = ui1['sentence'].str.split(' ', n=1, expand=True)
        #                ui2 = ui1[['sentence1','action']]
        #                ui3 = ui1[['sentence2','action']]
        #                #ui3.dropna(subset=['action'],inplace = True) 
        #                ui3.dropna(inplace = True)    
        #                ui2.columns = ['sentence', 'action']
        #                ui3.columns = ['sentence', 'action']
        #                ui4 = ui2.append(ui3, ignore_index=True)            
        #                lst_ip1 = nltk.word_tokenize(sentence)
        #                lst_ip3 = pd.DataFrame(lst_ip1)
        #                lst_ip3.columns = ['sentence']
        
        
                    k = ui1.apply(lambda row: nltk.word_tokenize(row['sentence']), axis=1)
                    k = pd.DataFrame(k)
                    k.columns = ["sentence"]
                    new = k.sentence.apply(pd.Series)
                    new["action"]=ui1["action"]
                    df_new = pd.DataFrame()
                    for label, content in new.items():
                        df_new1 = pd.DataFrame()
                        df_new1[0] = new["action"]
                        df_new1[1] = new[label]
                        df_new = df_new.append(df_new1, ignore_index=True)
                        df_new = df_new[df_new[0] != df_new[1]]
                        df_new = df_new.dropna()
                    lst_ip1 = nltk.word_tokenize(sentence)
                    lst_ip3 = pd.DataFrame(lst_ip1)
                    lst_ip3.columns = ['sentence']
                    df_new.columns = ['action','sentence']
                    #################################################join
                    result = pd.merge(lst_ip3,
                                     df_new,
                                     on='sentence', 
                                     how='left')
        #                result = pd.merge(lst_ip3,
        #                                 ui4,
        #                                 on='sentence', 
        #                                 how='left')                
                    
                    result['action'] = result['action'].fillna('o')
                    result['key'] = (result['sentence'] != result['sentence'].shift(1)).astype(int).cumsum()
                    result =result.groupby(['key', 'sentence'])['action'].apply('#$#'.join).to_frame()
                    result = result.reset_index()
                    result['sentence'] = result['sentence'].map(str) + " " + result["action"]
                    user_input3 = result['sentence']
                    user_input3.to_csv(str(df2) +'/user_input3.tsv',header=False, index=False)
                    user_input3 = pd.read_csv(str(df2) +'/user_input3.tsv', sep='\t',header = None)
                    exists = os.path.isfile(str(df2) +'/dummy-corpus1.tsv')
                    exists1 = os.path.isfile(str(df2) +'/dummy-corpus2.tsv')
                    if exists and not exists1:
                        pa1 = pd.read_csv(str(df2) +'/dummy-corpus1.tsv', sep='\t',header = None)
                        pa2 = pa1.append(user_input3,ignore_index=True)
                        pa2 = pa2.append([". o"])
                    elif exists1 and exists:
                        pa1 = pd.read_csv(str(df2) +'/dummy-corpus2.tsv', sep='\t',header = None)
                        pa2 = pa1.append(user_input3,ignore_index=True)
                        pa2 = pa2.append([". o"])  
                    else:
                        pa2 = user_input3
                        pa2 = pa2.append([". o"])
                        
                    pa2.to_csv(str(df2) +'/dummy-corpus1.tsv',header=False, index=False)
                
            cwd = os.getcwd()
            cwd = pathlib.PureWindowsPath(cwd)
            cwd = cwd.as_posix()
            prop = "trainFile = "+ str(cwd) +"/" + str(df2) + """/dummy-corpus1.tsv
            serializeTo ="""+ str(cwd) +"/" + str(df2) +"""/corpus-tagging.ser.gz
            map = word=0,answer=1
            
            useClassFeature=true
            useWord=true
            useNGrams=true
            noMidNGrams=true
            maxNGramLeng=6
            usePrev=true
            useNext=true
            useSequences=true
            usePrevSequences=true
            maxLeft=1
            useTypeSeqs=true
            useTypeSeqs2=true
            useTypeySequences=true
            wordShape=chris2useLC
            useDisjunctive=true"""
            
            file = open( str(cwd) +"/" + str(df2)+'/prop2.txt', 'w')
            file.write(prop)
            file.close()
            myCmd = 'java -jar stanford-ner.jar -mx4g -prop' " "  + str(df2) + '/prop2.txt'
            os.system(myCmd)   
        
            return 'Recurrent Training on Completed Successfully'
        
        else:
                return 'No Data to be trained on NULL'
    else:
        return 'Unsuccessful Auth'
    
if __name__ == '__main__':
    app.run(host = '0.0.0.0',port = 3131)