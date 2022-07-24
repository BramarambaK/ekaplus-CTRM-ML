"""
Data formats:
    Training data format must be like below:

        train_data = [
            ("Buy Crude from ADM BULGARIA", 
            {"entities": [(0, 3, "contractTypeDisplayName"), (4, 9, "productIdDisplayName"), (15, 27, "cpNameDisplayName")]}),
            
            ("Bought gasoil from 23-7 Farms.", 
            {"entities": [(0, 6, "contractTypeDisplayName"), (7, 13, "productIdDisplayName"), (19, 29, "cpNameDisplayName")]})
        ]

    Test data format must be like below:
        TEST_DATA = [
            "Purchase Cotton",
            "Bought gasoil of Quality 1000 PPM of Quantity 2000 MT using CIF."
        ]
"""

from __future__ import unicode_literals, print_function
import logging
import random
import warnings
import spacy
from spacy.util import minibatch, compounding
from make_training_data import create_training_data
import model_file
# from train_data import train_data

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def main(model=None, output_dir=None, n_iter=100, user_input=None):
    """Load the model, set up the pipeline and train the entity recognizer."""
    if model is not None:
        nlp = model_file.load_model(model)
    else:
        import en_core_web_sm
        nlp = en_core_web_sm.load()

    # create the built-in pipeline components and add them to the pipeline
    # nlp.create_pipe works for built-ins that are registered with spaCy
    if "ner" not in nlp.pipe_names:
        ner = nlp.create_pipe("ner")
        nlp.add_pipe(ner, last=True)
    # otherwise, get it so we can add labels
    else:
        ner = nlp.get_pipe("ner")

    # add labels
    train_data = create_training_data(user_input)
    for _, annotations in train_data:
        for ent in annotations.get("entities"):
            ner.add_label(ent[2])

    # get names of other pipes to disable them during training
    pipe_exceptions = ["ner", "trf_wordpiecer", "trf_tok2vec"]
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]
    # only train NER
    with nlp.disable_pipes(*other_pipes) and warnings.catch_warnings():
        # show warnings for misaligned entity spans once
        warnings.filterwarnings("once", category=UserWarning, module='spacy')
        # reset and initialize the weights randomly – but only if we're
        # training a new model
        if model is None:
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
    model_file.save_model(nlp, output_dir)