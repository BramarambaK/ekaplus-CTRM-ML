import logging
import json

"""
Input expected from user:
    INPUT_DATA = [
        {"sentence":"Sold 100 ppm, 2 MT gasoil to A&M Global Transport Inc.", "Sold":"contractTypeDisplayName", "100 ppm":"qualityDisplayName", "2":"itemQty"
        , "A&M Global Transport Inc.":"cpNameDisplayName", "MT":"itemQtyUnitIdDisplayName"
        , "gasoil":"productIdDisplayName"},

        {"sentence":"Sold 100 ppm, 2 MT gasoil to A&M Global Transport Inc.", "Sold":"contractTypeDisplayName", "100 ppm":"qualityDisplayName", "2":"itemQty"
        , "A&M Global Transport Inc.":"cpNameDisplayName", "MT":"itemQtyUnitIdDisplayName"
        , "gasoil":"productIdDisplayName"}

    ]
"""

def create_training_data(user_input):
    training_data = []
    user_input_data = user_input['data']
    for data in user_input_data:
        sentence_ = data['sentence']
        entities = []
        sent_tuple = (sentence_, )
        data.pop('sentence')
        for k,v in data.items():
            index = get_indices(sentence_, v)
            tag = (k,)
            if index is None:
                entities_tup = None
            else:
                idx_and_tag = index + tag
                entities.append(idx_and_tag)
                entities_tup = ({"entities":entities}, )
        if entities_tup is None:
            pass
        else:
            training_sentence = sent_tuple + entities_tup
            training_data.append(training_sentence)
    return training_data

def get_indices(sentence, word):
    if word.lower() in sentence.lower():
        idx = sentence.lower().find(word.lower())
        idx_tuple = (idx, idx+len(word), )
        return idx_tuple