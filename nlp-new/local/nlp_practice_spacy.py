#%% [Markdown]

# ## This is markdown

import spacy
nlp = spacy.load("en_core_web_lg")
# doc = nlp("Apple is looking at buying U.K. startup for $1 billion")
# doc = nlp("For the counter party AdC warehousing, currency EUR with credendo for an amount of 386000 from 2019-10-28T00:00:00.000+05:30  to 2019-10-29T00:00:00.000+05:30  with an inactive limit status")

doc = nlp("buy 100 MT of cotton from Cargill")
for token in doc:
    # print(token.text, token.lemma_, token.pos_, token.tag_, token.dep_,
    #         token.shape_, token.is_alpha, token.is_stop, token.ent_type, token.ent_type_)
    print(token.text, token.ent_type_, token.pos_, token.ent_type_)
spacy.displacy.render(doc, style='ent', jupyter=True)
########
### NLTK
########

import nltk
# sentence = """At eight o'clock on Thursday morning Arthur didn't feel very good."""
sentence = """buy 100 MT of cotton from Cargill"""

tokens = nltk.word_tokenize(sentence)
print(tokens)
tagged = nltk.pos_tag(tokens)
print(tagged)
entities = nltk.chunk.ne_chunk(tagged)
print(entities)
# for i in entities:
#     print(i)
#     print(i[0])

# %%
