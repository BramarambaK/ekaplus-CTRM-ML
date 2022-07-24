import logging
import json
logger = logging.getLogger()
logger.setLevel(logging.INFO)
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
def get_indices(sentence, word):
    try:
        if word in sentence:
            idx = sentence.find(word)
            idx_tuple = (idx, idx+len(word), )
            return idx_tuple
    except:
        logging.info(f"The word -- {word} is not found in the given sentence -- {sentence}")
        pass


def create_training_data(user_input):
    logging.info("Creating training data to be sent as input to the model.")
    training_data = []
    for data in user_input:
        sentence_ = data['sentence']
        entities = []
        sent_tuple = (sentence_, )
        data.pop('sentence')
        for k,v in data.items():
            index = get_indices(sentence_, v)
            if index is not None:
                tag = (k,)
                idx_and_tag = index + tag
                entities.append(idx_and_tag)
                entities_tup = ({"entities":entities}, )
            else:
                entities_tup = None
        if entities_tup is not None:
            training_sentence = sent_tuple + entities_tup
            training_data.append(training_sentence)
        else:
            pass
    return training_data