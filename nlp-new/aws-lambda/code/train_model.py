#!/usr/bin/env python
# coding: utf8
"""Example of training spaCy's named entity recognizer, starting off with an
existing model or a blank model.

For more details, see the documentation:
* Training: https://spacy.io/usage/training
* NER: https://spacy.io/usage/linguistic-features#named-entities

Compatible with: spaCy v2.0.0+
Last tested with: v2.2.4
"""
from __future__ import unicode_literals, print_function
import json
import logging
import random
import warnings
import spacy
from spacy.util import minibatch, compounding
from make_training_data import create_training_data
from save_model import save_model_to_s3
import load_model
import load_model_and_tag_map
from load_response_map import save_response

response_map_object_hardcoded = {
"sold":"Sale",
"sell":"Sale",
"buy":"Purchase",
"bought":"Purchase",
"purchase":"Purchase",
"purchased":"Purchase",
"gas oil":"Gasoil",
"gasoil":"Gasoil",
"crude":"Crude",
"oil":"Gasoil"
}


def save_model_(model, headers):
    # save model to output directory
    try:
        logging.info("Calling the save model function.")
        save_model_to_s3(model=model, headers=headers)
    except Exception as e:
        logging.error(e)
        logging.error("Couldn't save model to s3 due to some error.")
    return None

def save_model_and_tag(model, headers, tag_map):
    # save model to output directory
    try:
        logging.info("Calling the save model function.")
        model_and_tag = {'model':model, 'tags':tag_map}
        save_model_to_s3(model=model_and_tag, headers=headers)
    except Exception as e:
        logging.error(e)
        logging.error("Couldn't save model to s3 due to some error.")
    return None

def save_response_map(headers):
    try:
        logging.info("Calling the save response map function.")
        save_response(response_map_object_hardcoded, headers)
    except Exception as e:
        logging.error(e)
        logging.error("Couldn't save model to s3 due to some error.")
    return None


def main(headers, model=None, n_iter=100, user_input=None, tag_map=None):
    """Load the model, set up the pipeline and train the entity recognizer.
        Data format:
            Training data format must be like below:
                train_data = [
                    ("Buy Crude from ADM BULGARIA", 
                    {"entities": [(0, 3, "contractTypeDisplayName"), (4, 9, "productIdDisplayName"), (15, 27, "cpNameDisplayName")]})
                ]
            Test data format must be like below:
                TEST_DATA = [
                    "Purchase Cotton",
                    "Bought gasoil of Quality 1000 PPM of Quantity 2000 MT using CIF."
                ]
    
    """
    # model = load_model.get_model(headers)
    model = load_model_and_tag_map.get_model(headers)
    if model is not None:
        nlp = model
        logging.info("Loaded model '%s'" % model)
    else:
        nlp = spacy.load("en_core_web_sm")
        logging.info("Loaded 'en_core_web_sm' model")

    # create the built-in pipeline components and add them to the pipeline
    # nlp.create_pipe works for built-ins that are registered with spaCy
    if "ner" not in nlp.pipe_names:
        ner = nlp.create_pipe("ner")
        nlp.add_pipe(ner, last=True)
    # otherwise, get it so we can add labels
    else:
        ner = nlp.get_pipe("ner")

    # add labels
    logging.info("Making training data from sentence.")
    train_data = create_training_data(user_input)
    if len(train_data) == 0:
        msg = {"statusCode": 200, "body":json.dumps({"msg":"Created training data is empty. Aborting training."})}
        return msg
    else:
        logging.info("Successfully created training data.")
        for _, annotations in train_data:
            for ent in annotations.get("entities"):
                ner.add_label(ent[2])

        # get names of other pipes to disable them during training
        pipe_exceptions = ["ner", "trf_wordpiecer", "trf_tok2vec"]
        other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]
        logging.info(other_pipes)
        # only train NER
        with nlp.disable_pipes(*other_pipes) and warnings.catch_warnings():
            # show warnings for misaligned entity spans once
            logging.info("Disabled pipes.")
            warnings.filterwarnings("once", category=UserWarning, module='spacy')

            # reset and initialize the weights randomly – but only if we're
            # training a new model
            if model is None:
                logging.info("Beginnning training.")
                nlp.begin_training()
            for itn in range(n_iter):
                random.shuffle(train_data)
                losses = {}
                # batch up the examples using spaCy's minibatch
                batches = minibatch(train_data, size=compounding(4.0, 32.0, 1.001))
                for batch in batches:
                    texts, annotations = zip(*batch)
                    nlp.update(
                        texts,  # batch of texts
                        annotations,  # batch of annotations
                        drop=0.5,  # dropout - make it harder to memorise data
                        losses=losses,
                    )
                if itn % 10==0:
                    info_ = "For the iteration: " + str(itn) +  " - Losses: " + str(losses)
                    logging.info(info_)
        logging.info("Calling save model function for saving model to s3.")
        # save_model_(nlp, headers)
        save_model_and_tag(nlp, headers, tag_map)
