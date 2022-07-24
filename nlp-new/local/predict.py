import logging
import spacy

def load_trained_model(test_data, output_dir):
    info_ = "Loading model from :" + str(output_dir)
    logging.info(info_)
    try:
        nlp = spacy.load(output_dir)
        logging.info("Loaded the nlp model.")
        result = get_prediction(nlp, test_data)
        logging.info("Computed the predictions.")
        return result
    except OSError:
        logging.error("Model files not found. Can't predict without trained model.")
        msg = {"msg":"Model files not found. Can't predict without trained model."}
        return msg

def get_prediction(nlp, test_data):
    entities_ = []
    doc = nlp(test_data)
    # print("Entities", [(ent.text, ent.label_) for ent in doc.ents])
    # print("Tokens", [(t.text, t.ent_type_, t.ent_iob) for t in doc])
    # entities__ = [{ent.text:ent.label_} for ent in doc.ents]
    entities__ = [{ent.label_:ent.text} for ent in doc.ents]

    result = {}
    # print(entities__)
    for d in entities__:
        result.update(d)
    return result
