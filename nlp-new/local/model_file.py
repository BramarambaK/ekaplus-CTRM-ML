import logging
from pathlib import Path
import spacy

def load_model(model):
    if model is not None:
        try:
            nlp = spacy.load(model)  # load existing spaCy model
            logging.info("Loaded model '%s'" % model)
            return nlp
        except:
            logging.info("Specified Model not found '%s'" % model)
    else:
        nlp = spacy.blank("en")  # create blank Language class
        logging.info("Created blank 'en' model")
        return nlp

def save_model(model, output_dir):
    # save model to output directory
    logging.info("Saving the trained model.")
    if output_dir is not None:
        output_dir = Path(output_dir)
        if not output_dir.exists():
            logging.info("Making the directories for saving model.")
            output_dir.mkdir(parents=True)
        model.to_disk(output_dir)
        info_ = "Saved model to : " + str(output_dir)
        logging.info(info_)