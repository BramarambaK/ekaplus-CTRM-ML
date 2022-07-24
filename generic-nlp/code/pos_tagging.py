
import spacy 
  
# Load English tokenizer, tagger,  
# parser, NER and word vectors 
nlp = spacy.load("en_core_web_sm") 
  
# # Process whole documents 
# text = ("""My name is Shaurya Uppal.  
# I enjoy writing articles on GeeksforGeeks checkout 
# my other article by going to my profile section.""") 

# Process whole documents 
text = ("""trader Ved cp Amitabh delivery 01 jan 2020 to 30 Jan 2020 unit MT.""") 
# text = ("""trader cofco cp cargill delivery 01 jan 2020 to 30 Jan 2020 unit MT.""") 

doc = nlp(text) 
  
# Token and Tag 
for token in doc: 
  print(token, token.pos_) 
  
# You want list of Verb tokens 
print("Verbs:", [token.text for token in doc if token.pos_ == "VERB"])

######################################
# datefinder Works very well for dates
######################################
import datefinder

# string_with_dates = '''
#     Central design committee session Tuesday 10/22 6:30 pm
#     Th 9/19 LAB: Serial encoding (Section 2.2)
#     There will be another one on December 15th for those who are unable to make it today.
#     Workbook 3 (Minimum Wage): due Wednesday 9/18 11:59pm
#     He will be flying in Sept. 15th.
#     We expect to deliver this between late 2021 and early 2022.
# '''
string_with_dates = 'trader cofco cp cargill delivery 01 jan 2020 to 30 Jan 2020 unit MT'

matches = datefinder.find_dates(string_with_dates)
for match in matches:
    print(match)


import nltk
# text = nltk.word_tokenize('trader cofco cp cargill delivery 01 jan 2020 to 30 Jan 2020 unit MT')
text = nltk.word_tokenize('buy crude from trader cofco')
print(f"The POS tags from NLTK: {nltk.pos_tag(text)}")

