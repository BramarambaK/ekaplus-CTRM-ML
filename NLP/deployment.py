# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 12:53:37 2019

@author: kartik.patnaik
"""
import os
from nltk.tag import StanfordNERTagger  
import re
from quantulum3 import parser
import pandas as pd
import json
from flask import Flask,request 
from datapackage import Package
from country_list import countries_for_language
import requests
from difflib import get_close_matches

#Finding the os directory and corret java path
os.chdir("E:/deployment/CTRM-ML/NLP")
java_path = "E:/deployment/CTRM-ML/NLP/jre1.8.0_191/bin/java.exe" 
os.environ['JAVAHOME'] = java_path
###########################################################################
package = Package('https://datahub.io/core/world-cities/datapackage.json')
###########################################################################
countries = dict(countries_for_language('en'))
countries=list(countries.values())
for resource in package.resources:
    if resource.descriptor['datahub']['type'] == 'derived/csv':
        country_city = resource.read()

city = [i[0] for i in country_city]
city = [x.lower() for x in city]
city.remove('buy')
city.remove('march')
countries = [x.lower() for x in countries]  

###############################################################################################
#MDM-------------------------PRODUCTS---------LIST--------------------------------------------#                              
###############################################################################################
url = 'http://172.16.5.101:1111/mdm/data'
data = '[{"serviceKey": "productComboDropDrown"},{"serviceKey": "businesspartnercontactperson"},{"serviceKey": "userListByRole"},{"serviceKey": "paytermlist_phy"},{"serviceKey": "dealType"},{"serviceKey": "dealType",dependsOn:["DealType"]}]'
response = requests.post(url, data=data,headers={"Content-Type": "application/json","X-TenantID": "boliden","userName": "admin"})

#data = '[{"serviceKey": "dealType",dependsOn:["DealType"]}]'
#response = requests.post(url, data=data,headers={"Content-Type": "application/json","X-TenantID": "boliden","Authorization":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsicmVzdF9hcGkiXSwidXNlcl9uYW1lIjoid2FxdWFhckBla2FwbHVzLmNvbSIsInNjb3BlIjpbInRydXN0IiwicmVhZCIsIndyaXRlIl0sImV4cCI6MTU1Mjk3NTM4MywiYXV0aG9yaXRpZXMiOlsiMTI3LjAuMC4xIl0sImp0aSI6Ijc4OThiN2FmLTU0N2MtNGExMi1hNTU2LTRmYzExYWE3YzY4MCIsImNsaWVudF9pZCI6IjIifQ.nky9Uo2c1xjqLcKozFNS9HyYjncJd4f-3gTk-b3kHS0"})
product=response.json()
product1=list(product.values())[0]
counterparty1=list(product.values())[1]
tradername1=list(product.values())[2]
paymentterm1=list(product.values())[3]
dealtype1=list(product.values())[4]
product = [d['value'] for d in product1 if 'value' in d]
product = [x.lower() for x in product]
counterparty = [d['value'] for d in counterparty1 if 'value' in d]
counterparty = [x.lower() for x in counterparty]
tradername = [d['value'] for d in tradername1 if 'value' in d]
tradername = [x.lower() for x in tradername]
paymentterm = [d['value'] for d in paymentterm1 if 'value' in d]
paymentterm = [x.lower() for x in paymentterm]
dealtype = [d['value'] for d in dealtype1 if 'value' in d]
dealtype = [x.lower() for x in dealtype]

#######################################################################
#Key of every product                                                 #
#######################################################################
key1 = [d['key'] for d in product1 if 'value' in d]
qualt=[]
for i in range(len(key1)):
    data1 = '[{"serviceKey": "qualityComboDropDrown","dependsOn":'+ str([key1[i]]) +'}]'
    response1 = requests.post(url, data=data1,headers={"Content-Type": "application/json","X-TenantID": "boliden","userName": "admin"})
    quality=response1.json()
    if quality!= {}:
        quality=list(quality.values())[0]
    else:
        quality = []
    qualt.append(quality)

qualt2 = []
for i in range(len(qualt)):
    qualt1 = [d['value'] for d in qualt[i] if 'value' in d]
    qualt2.append(qualt1)
############################################################################
#Quality Dictonary                                                         #
############################################################################
flat_list = [item for sublist in qualt2 for item in sublist]
for sublist in qualt2:
    for item in sublist:
        flat_list.append(item)
flat_list = [x.lower() for x in flat_list] 
###########################################################################
#Index Curve                                                              #
###########################################################################
url1 = "http://reference.qa2.ekaanalytics.com:3120/cac-security/api/oauth/token?grant_type=cloud_credentials&client_id=2"
response1 = requests.post(url1,headers={"Content-Type":"application/x-www-form-urlencoded","Authorization":"Basic QnJhdm86QnJhdm8="})
auth=response1.json()
auth = auth["auth2AccessToken"]
auth = auth['access_token']
###########################################################################
#Values                                                                   #
###########################################################################
url2 = "http://reference.qa2.ekaanalytics.com:3120/spring/collection/connectors/subCategory/instruments?collectionId=0&connectorCategoryId=7"
response2 = requests.get(url2,headers = {"Authorization": str(auth),"clientId":"8",})
auth1=response2.json()
auth1 = auth1["data"]
df = pd.DataFrame.from_dict(auth1, orient='columns')
curve = df['name'].tolist()
###########################################################################
#Formula Curve                                                            #
###########################################################################
url3 = "http://manuchar.integ.ekaanalytics.com:99/cac-security/api/oauth/token?grant_type=cloud_credentials&client_id=2"
#url3 = "http://192.168.1.225:8889/connect/api/data/pricing/formula"
response3 = requests.post(url3,headers={"Content-Type":"application/x-www-form-urlencoded","Authorization":"Basic d2FxdWFhckBla2FwbHVzLmNvbTp3YXF1YWFyQGVrYXBsdXMuY29t"})
auth2=response3.json()
auth2 = auth2["auth2AccessToken"]
auth2 = auth2['access_token']
###########################################################################
#Values                                                                   #
###########################################################################
#url4 = "http://manuchar.integ2.ekaanalytics.com:99/connect/api/data/pricing/formula"
url4 = "http://192.168.1.225:8889/connect/api/data/pricing/formula"
#response4 = requests.get(url4,headers = {"Authorization": str(auth2),"Content-Type": "application/json","X-TenantID": "boliden","X-Locale":"en_US"})
response4 = requests.get(url4,headers = {"Authorization": str(auth2),"Content-Type": "application/json","X-TenantID": "manuchar","X-Locale":"en_US"})

auth3=response4.json()
df1 = pd.DataFrame.from_dict(auth3, orient='columns')
formula_curve = df1['formulaName'].tolist()
###############################################################################################
###############################################################################################
 
#Flask code
app = Flask(__name__)
@app.route('/text-string')

def recognizer():
    #article = input("Enter your string:")
    article = request.args.get('article') 
    article = article.lower()
    article = article.replace(',', '')
    article = article.replace('one ', '1')
    article = article.replace('two ', '2')
    article = article.replace('three ', '3')
    article = article.replace('four ', '4')
    article = article.replace('five ', '5')
    article = article.replace('six ', '6')
    article = article.replace('seven ', '7')
    article = article.replace('eight ', '8')
    article = article.replace('nine ', '9')
    article = article.replace('percentage', '%')
    article = article.replace('percent', '%')
    article = article.replace('jan ', 'january ') #converting the month format
    article = article.replace('feb ', 'february ')
    article = article.replace('mar ', 'march ')
    article = article.replace('apr ', 'april ')
    article = article.replace('may ', 'may ')
    article = article.replace('jun ', 'june ')
    article = article.replace('jul ', 'july ')
    article = article.replace('aug ', 'august ')
    article = article.replace('sep ', 'september ')
    article = article.replace('oct ', 'october ')
    article = article.replace('nov ', 'november ')
    article = article.replace('dec ', 'december ')
    article = article.replace('st of ', ' ') #correcting the st of from date
    article = article.replace('augu ', 'august ')
    article = article.replace('bangalore', 'bengaluru')
    article = article.replace('features', 'futures')
    #######################################################
#    package = Package('https://datahub.io/core/world-cities/datapackage.json')
#    #####################################################
#    countries = dict(countries_for_language('en'))
#    countries=list(countries.values())
#    for resource in package.resources:
#        if resource.descriptor['datahub']['type'] == 'derived/csv':
#            country_city = resource.read()
#    
#    city = [i[0] for i in country_city]
#    city = [x.lower() for x in city]
#    city.remove('buy')
#    countries = [x.lower() for x in countries]

    
    word = ['by', 'Buy','By','buy','purchase','buying','purchasing','purchased','bought']  
    word1 = ["sell","sel","cell"]
    pricetype= ["Index"]
    pricetype1= ["Formula"]
#    list_corp = ["Van Loon Farms Ltd.","Cantelon Farms; Attn: Wayne Cantelon","Van Miltenburg Farms Ltd.","Katelyn Moore","ADM Agri-Industries Company (USD)","Greenfield Global","Cargill Inc Grain & Oilseed Supply Chain","(Dubai) Hanjin Shipping Company Inc.","Cartiera Di Bosco Marengo S.P.A.","Statpack Industries Ltd","Manuchar Steel NV","MERCANTIL DEL CARIBE  S.A.S.","Cargill Intl","UNIMAC RUBBER COMPANY LTD","British Petroleum","OCI Methanol","GITI TYRE GLOBAL TRADING PTE LTD","Shell","CS Rubber Industry Co Ltd","BIV Commodities","Agro Pulse Trading House Fze","23-7 Farms","AGROGLOBAL","Almorouj for Animal Feed","TRAFIGURA","LEI SHING","3W Farms","Seller 2","Farmers Fresh","Seller 8","Buyer 1","Abu Qir Fertilizer Company","Sulacid Buyer 3","Cargill In S.A.C.I","MSC BELGIUM NV","CREDIMUNDI","EXCELLENCE SHIPPING COMPANY LIMITED","AGENCIAS NAVIERAS B & R, SA","TIANJIN SEAMART LOGISTICS CO LTD","Grubville Enterprises Corporation","GrainCraft","101010838 Sask Ltd.","Blessey Marine","101038552 Sask. LTD","101110684 Saskatchewan Ltd (Rhett Gerrard)","Marine Shipping Ltd","AAI","AEL","AFCO Energy","ANDIN","AVL Energy Partners","Afrom","Amaggi","Armajaro Trading","Asia Ref Corp","Australia Coal Mining Co.","Az Logistics","BB Energy","BBVA","BHP Billiton Indonesia. PT","BMCE","BPCL Bina Refinery","BPCL Kochi Refinery","BPCL Mumbai Refinery","BPCL Numaligarh Refinery","Bank Negara Malaysia","Bridegport Fittings","Bumi Armada Berhad","CP Indo","CP Malaysia","CS","Cargill Intl","Carolotta Copper Company","CenterPoint Energy Services","Cepaltom","Comfeed Indo","Concordia","Credit du Maroc","DJJ Railroad Company","DJJ WH Corp","Dabhol Terminal","Dorking Warehouse","EA Storage","EKA Asia 5","EKA Asia 6","EKA Asia 7","EKA Asia CP 2","EKA Marubeni","EKA Standard Demo","EKA Sugar Inc.","ETS","Emivest","Emmen","FinCo Logistics B.V","Galta","Gavilon","Glencore","Global Copper Fabricator","Global Metal Industrial Corp","Global Metal Trading Co.","Global Zinc Trading Co.","Gold Coin Indo","GrebGaz","Haldia Refinery","Holland Biomass 4 Energy Solutions","ING","Idemitsu Kosan","Indonesia Coal Mining Co.","Iron Ore Storage","Kapar","Komoro IndoResources","Local Seller A","MF Global","Maersk","Malindo","Manjung","Marubeni WH","Matilda Gaz","Mercuria","Metro","Millenia","Miroil SA","Multigrain","New Edge","ONGC","Oil Trading","PT Coalindo Energy","Patterson Fuels","Proconco","QL Vn","Quingdao","RGL","RSEB","RWE Supply & Trading","Reliance Petroleum","Rio Tinto","Russian-Petroleum","S.Thai","SGI-Coal Quality Surveyors","SNR Commodities","Sascom","Sasma BV","Saudi Aramco","Service Aluminum","Sinar","Singapore Airlines","Sinopec China","Station 1","Sugar Surveyor","Sunoil Processing Plant","TNB","TNBF WH","Tanjung Bin","Toepfer","Traffigura","Tyson Foods","UAB","United Sugar Company","VTTI Energy Partners","Vale","Vale International SA","Vedanta Resources","Vitol","WIN Goal","Wells Fargo","Wood Pellets Surveyor","World Energy Council"]
    inco_term_list = ["CFR","CIF","CPT","DAF","DDP","DDU","DEQ","DES","EXW","FAS","FCA","FOB"]
#    product = ["eston, green lentils","corn","canola meal","brown flaxseed","black beans","gas","gasoil","gasoline","oil","coffee","wheat","corn","oats","barley","rough rice","oilseeds","cotton","palm oil","soybeans","meat","feeder cattle","lean hogs","live cattle","pork bellies","miscellaneous","cocoa","coffee","fcoj","sugar","lumber","rubber","wool","gasoil","crude","gasoline","petrol"]
    calc = ["calculate","formulate","find","get"]
#    list_corp = [x.lower() for x in list_corp]
    inco_term_list = [x.lower() for x in inco_term_list]
#    product = [x.lower() for x in product]
    word = [x.lower() for x in word]
    #    places = [x.lower() for x in places]
    pricetype = [x.lower() for x in pricetype]
    pricetype1 = [x.lower() for x in pricetype1]
    
###############################################
#Filtering basis pretrained+ Manual data Model#
###############################################
    
#Stanford NER library import and using only location filtering
    stanford_ner_tagger = StanfordNERTagger(
        'stanford_ner/' + 'classifiers/english.muc.7class.distsim.crf.ser.gz',
        'stanford_ner/' + 'stanford-ner-3.9.2.jar'
    )
    
    results = stanford_ner_tagger.tag(article.split())
    filter = ['LOCATION']
    ls2 = [(x,y) for (x,y) in results if y in filter] 
    ls2 = [i[0] for i in ls2]
    
#Function to select the locations and the same would be used in future for dates
    def locFn(lsss):
       if len(lsss)>0:
           return lsss[0]
       else:
           return ""
    
    def locFn1(lsss):
       if len(lsss)>1:
           return lsss[1]
       else:
           return ""
       
    def locFn_1(lsss):
       if len(lsss)>0:
           return lsss[0]
       else:
           return []
    
    def locFn1_1(lsss):
       if len(lsss)>1:
           return lsss[1]
       else:
           return []

#Filtering Location            
    ls2 = ls2[:2]
    ls10 = locFn(ls2)
    ls11 = locFn1(ls2)

#filtering buy and sell    
    if any(x in article.lower() for x in word):
        ls1 = ["buy"] 
    elif any(x in article.lower() for x in word1):
        ls1 = ["sell"]
    else:
        ls1 = [""]
        
    ls1 = ls1[:1]
     
#Filtering date    
    if len(re.findall(r"([\d]{1,2}\s(january|february|march|april|may|june|july|august|september|october|november|december)\s[\d]{4})", article)) != 0:
        ls3 = re.findall(r"([\d]{1,2}\s(january|february|march|april|may|june|july|august|september|october|november|december)\s[\d]{4})", article)
    elif len(re.findall(r"([\d]{1,2}\s(january|february|march|april|may|june|july|august|september|october|november|december)\s[\d]{2})", article)) != 0:
        ls3 = re.findall(r"([\d]{1,2}\s(january|february|march|april|may|june|july|august|september|october|november|december)\s[\d]{2})", article)
    elif len(re.findall(r"((january|february|march|april|may|june|july|august|september|october|november|december)\s[\d]{1,2}\s[\d]{4})", article)) !=0:
        ls3 = re.findall(r"((january|february|march|april|may|june|july|august|september|october|november|december)\s[\d]{1,2}\s[\d]{4})", article)
    elif len(re.findall(r"([\d]{1,2}-(january|february|march|april|may|june|july|august|september|october|november|december)-[\d]{4})", article)) != 0:
        ls3 = re.findall(r"([\d]{1,2}-(january|february|march|april|may|june|july|august|september|october|november|december)-[\d]{4})", article)
    elif len(re.findall(r"([\d]{1,2}-(january|february|march|april|may|june|july|august|september|october|november|december)-[\d]{2})", article)) != 0:
        ls3 = re.findall(r"([\d]{1,2}-(january|february|march|april|may|june|july|august|september|october|november|december)-[\d]{2})", article)
    elif len(re.findall(r"([\d]{1,2}/(january|february|march|april|may|june|july|august|september|october|november|december)/[\d]{4})", article)) != 0:
        ls3 = re.findall(r"([\d]{1,2}/(january|february|march|april|may|june|july|august|september|october|november|december)/[\d]{4})", article)
    elif len(re.findall(r"([\d]{1,2}/(january|february|march|april|may|june|july|august|september|october|november|december)/[\d]{2})", article)) != 0:
        ls3 = re.findall(r"([\d]{1,2}/(january|february|march|april|may|june|july|august|september|october|november|december)/[\d]{2})", article)
    elif len(re.findall(r"[\d]{1,2}/[\d]{1,2}/[\d]{4}", article)) !=0:
        ls3 = (re.findall(r"[\d]{1,2}/[\d]{1,2}/[\d]{4}", article))
    elif len(re.findall(r"[\d]{1,2}-[\d]{1,2}-[\d]{4}", article)) !=0:
        ls3 = (re.findall(r"[\d]{1,2}-[\d]{1,2}-[\d]{4}", article))
    elif len(re.findall(r"[\d]{1,2}/[\d]{1,2}/[\d]{2}", article)) !=0:
        ls3 = (re.findall(r"[\d]{1,2}/[\d]{1,2}/[\d]{2}", article))
    elif len(re.findall(r"[\d]{1,2}-[\d]{1,2}-[\d]{2}", article)) !=0:
        ls3 = (re.findall(r"[\d]{1,2}-[\d]{1,2}-[\d]{2}", article))
    elif len(re.findall(r"[\d]{1,2}\s[\d]{1,2}\s[\d]{4}", article)) !=0:
        ls3 = (re.findall(r"[\d]{1,2}\s[\d]{1,2}\s[\d]{4}", article))
    elif len(re.findall(r"[\d]{1,2}\s[\d]{1,2}\s[\d]{2}", article)) !=0:
        ls3 = (re.findall(r"[\d]{1,2}\s[\d]{1,2}\s[\d]{2}", article))
    
    else:
        ls3 = []
        
    #ls3 = [i[0] for i in ls3]
    ls12 = locFn_1(ls3)
    ls13 = locFn1_1(ls3)

#Fetching Incoterm
    if any(s in article.lower() for s in inco_term_list): 
        ls4 = list(set(article.split()) & set(inco_term_list))
    else:
        ls4 = []
    ls4 = ls4[:1]

#Fetching CP name
    counterparty2 = counterparty.copy()
    To_remove = ['-',"  "]
    for t in To_remove:
        for i in range(len(counterparty2)):
            counterparty2[i] = counterparty2[i].replace(t, "")
 
    def remove(list): 
        pattern = '[0-9]'
        list = [re.sub(pattern, '', i) for i in list] 
        return list

    counterparty2 = remove(counterparty2)
    counterparty3 = counterparty2.copy()
    counterparty3 = [x.split(' ') for x in counterparty3]
    counterparty3 = [item[0] for item in counterparty3]
    
    for i in range(len(counterparty3)):
        if len(counterparty3[i])<3:
            counterparty3[i] = ""
    
    ls5 = get_close_matches(counterparty3,article,cutoff=0.4)
    ls5 = ls5[:1]

    if ls5 == []:     
        for x in counterparty3:
            if  article.lower().__contains__(x.lower()):
                ls5.append(x)
    ls5 = ls5[:1]
    
    if ls5 != [""] and ls5 !=[] and counterparty != []:   
        
        ls5 = [counterparty[counterparty3.index(ls5[0])]]
    else:
        ls5 = []

#Fetching product
    ls6 = get_close_matches(article, product,cutoff=0.7)
    ls6 = ls6[:1]
    if ls6 == []:
        for x in product:
            if  (" "+article.lower()+" ").__contains__(" "+x.lower()+" "):
                ls6.append(x)
    
    if len(ls6) > 1:
        ls6 = [max(ls6, key=len)]
    elif len(ls6) == 1:
        ls6 = [ls6[0]]
    else:
        ls6 = []


#Fetching calculated field
    ls14 = []
    for x in calc:
        if  article.lower().__contains__(x.lower()):
            ls14.append(x)
    ls14 = ls14[:1]

#Fetching tolorence
    regex = re.compile('-([0-9]*)')
    ls7 = regex.findall(article) 
    ls7 = ls7[:1]
    
#Appending all     
    ls1.append(ls10)
    ls1.append(ls11)
    ls1.append(ls12)
    ls1.append(ls13)
    ls1.append(ls4)
    ls1.append(ls5)
    ls1.append(ls6)
    ls1.append(ls7)
    
#####################################################
#enabling quantulum pretrained for quantity and unit#
#####################################################
    result = []
    for i in range(len(parser.parse(article))):
        result.append(parser.parse(article)[i].surface)
    df = pd.DataFrame({'col':result})
    if not df.empty:
        df['quantity']=df.col.str.extract('(\d+)')
        df['col'] = df['col'].astype(str)
        df['unit'] = df['col'].str.extract('([a-zA-Z ]+)', expand=False).str.strip()
        filter = df["unit"] != ""
        df= df[filter]
        df= df.dropna(subset=['unit']) 
        ls8 = list(df["quantity"])
        ls9 = list(df["unit"])
    else:
        ls8=[]
        ls9=[]
    
    ls8 = ls8[:1]
    ls9 = ls9[:1]

#Appending again
    
    ls1.append(ls8)
    ls1.append(ls9)
    ls1.append(ls14)

#City and country re loaded!
    ls15 = []
    for x in city:
        if  (" "+article.lower()+" ").__contains__(" "+x.lower()+" "):
            ls15.append(x)
    
    ls15 = locFn(ls15)
    
            
    ls16 = []
    for x in countries:
        if  (" "+article.lower()+" ").__contains__(" "+x.lower()+" "):
            ls16.append(x)
    
    ls16 = locFn(ls16)
    #Appending again
    ls1.append(ls15)
    ls1.append(ls16)


#The best way dealt with list as some times it was a string and sometimes it was an array standardizing
    if isinstance(ls1[3], tuple) or isinstance(ls1[3], list):
        ls1[3] = ls1[3]
    else:
        ls1[3] = [ls1[3]]
        
    if isinstance(ls1[4], tuple) or isinstance(ls1[4], list):
        ls1[4] = ls1[4]
    else:
        ls1[4] = [ls1[4]]
        
#    if isinstance(ls1[12], list):
#        ls1[12]= ls1[12][0]
#    if isinstance(ls1[13], list):
#        ls1[12]= ls1[13][0]
#############################################################################################################
#Quality
#############################################################################################################
    quality_1 = []
    for i in flat_list:
        j = i.replace(' - ',' ')
        quality_1.append(j) 
        
    if ls1[7]!= []:
        ls17 = []
        for x in quality_1:
            if  article.lower().__contains__(x.lower()):
                ls17.append(x)
                ls17=ls17[:1]
        if ls17 !=[]:
            ls17 = [flat_list[quality_1.index(ls17[0])]]
        if ls17==[]:
            ls17 = get_close_matches(article, quality_1,cutoff=0.45)
    else:
        ls17 = []
    
    ls17 = ls17[:1]
    #Appending again
    ls1.append(ls17)
########################################################
#Tradername
#########################################################
    ls18 = get_close_matches(article, tradername,cutoff=0.7)
    ls18 = ls18[:1]
    if ls18 == []:
        for x in tradername:
            if  (" "+article.lower()+" ").__contains__(" "+x.lower()+" "):
                ls18.append(x)
    ls18 = ls18[:1]
    tradername3 = [x.split(' ') for x in tradername]
    tradername3 = [item[0] for item in tradername3]
    for i in range(len(tradername3)):
        if len(tradername3[i])<3:
            tradername3[i] = ""
    
    if ls18==[]:                
        ls18 = get_close_matches(tradername3,article,cutoff=0.7)
        ls18 = ls18[:1]
    if ls18==[]:
        for x in tradername3:
            if  (" "+article.lower()+" ").__contains__(" "+x.lower()+" "):
                ls18.append(x)
                ls18 = ls18[:1]
                if ls18 != [""]:   
                    ls18 = [tradername[tradername3.index(ls18[0])]]
                else:
                    ls18 = []
    
    
########################################################
#paymentterm
#########################################################
    ls19 = get_close_matches(article, paymentterm,cutoff=0.7)
    ls19 = ls19[:1]
    if ls19 == []:
        for x in paymentterm:
            if  (" "+article.lower()+" ").__contains__(" "+x.lower()+" "):
                ls19.append(x)
    ls19 = ls19[:1]
########################################################
#dealtype
#########################################################
    ls20 = get_close_matches(article, dealtype,cutoff=0.7)
    ls20 = ls20[:1]
    if ls20 == []:
        for x in dealtype:
            if  (" "+article.lower()+" ").__contains__(" "+x.lower()+" "):
                ls20.append(x)
    ls20 = ls20[:1]
    #appending agn
    ls1.append(ls18)
    ls1.append(ls19)
    ls1.append(ls20)
    
    #alldates
    if ls3!=[] and isinstance(ls3[0], tuple) and len(ls3)>1:
        ls3 = [item[0] for item in ls3]

    
    ls1.append(ls3)
    
###########################################################
#Price type and price curve
###########################################################
    ls21 = []
    for x in pricetype:
        if  article.lower().__contains__(x.lower()):
            ls21.append(x)
    ls21 = ls21[:1]
    
    if ls21 == []:
        for x in pricetype1:
            if  article.lower().__contains__(x.lower()):
                ls21.append(x)
                ls21 = ls21[:1]
    
    if ls21 == pricetype:
        ls22 = get_close_matches(curve,article,cutoff=0.4)
        ls22 = ls22[:1]    
        if ls22 == []:     
            for x in curve:
                if  article.lower().__contains__(x.lower()):
                    ls22.append(x)
    else:
        ls22=[]
    
    if ls21 == pricetype1:
        formula_curve_1 = []
        for i in formula_curve:
            j = i.replace('_',' ')
            formula_curve_1.append(j)
        ls22 = get_close_matches(formula_curve_1,article,cutoff=0.4)
        ls22 = ls22[:1]
        if ls22 == [] and ls21 != []:     
            for x in formula_curve_1:
                if  article.lower().__contains__(x.lower()):
                    ls22.append(x)
                    if ls22 !=[]:
                        ls22 = formula_curve[formula_curve_1.index(ls22[0])]
        else:
            ls22 = []
        
    ls1.append(ls21)
    ls1.append(ls22)
#converting it into a dictonary        
#    sub_dict= {'status': ls1[0],'location':ls1[1], 'location1': ls1[2],'date':ls1[3],'date1':ls1[4],'incoterm': ls1[5],'cpname': ls1[6],'product': ls1[7],'tol': ls1[8],'quantity': ls1[9],'unit': ls1[10],'calc':ls1[11],'city':ls1[12],'country':ls1[13]}
    sub_dict= {'status': ls1[0],'location':ls1[13], 'location1': ls1[12],'date':ls1[3],'date1':ls1[4],'incoterm': ls1[5],'cpname': ls1[6],'product': ls1[7],'tol': ls1[8],'quantity': ls1[9],'unit': ls1[10],'calc':ls1[11],'quality':ls1[14],'tradername':ls1[15],'paymentterm':ls1[16],'dealtype':ls1[17],'alldates':ls1[18],'price_type':ls1[19],'price_curve':ls1[20]}

#converting into JSON
    sub_dict = json.dumps(sub_dict)
       
    return sub_dict

#recognizer("By oats through CFR , 15,000 metric ton +/-5%, sellers option to Bangalore India between 19 september 2016 to 21 september 2016")
#recognizer("by oats")
#buy wheat from bangalore through cfr from 25-jan-2019 to 29-jan-2019 with +/-5% tolorence

if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0',port = 5000)

#article = "Brown Flaxseed"

#import requests
#url = 'http://192.168.1.225:1111/mdm/data'
#data = '[{"serviceKey": "productComboDropDrown"},]'
#response = requests.post(url, data=data,headers={"Content-Type": "application/json","X-TenantID": "boliden","userName": "admin"})
#sid=response.json()