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

import plac
import random
import warnings
from pathlib import Path
import spacy
from spacy.util import minibatch, compounding
from train_data import TRAIN_DATA
import en_core_web_sm


# training data
# TRAIN_DATA = [
#     ("Who is Shaka Khan?", {"entities": [(7, 17, "PERSON")]}),
#     ("I like London and Berlin.", {"entities": [(7, 13, "LOC"), (18, 24, "LOC")]}),
# ]



# TEST_DATA = [
#     "Bought Cotton from KEC Intl.",
#     "Sell crude to Google.",
#     "Bought gasoil from Cargill corp.",
#     "Sold wheat to Cargill corp..",
#     "Purchase Crude from Microware.",
#     "Buy 2000 MT Gasoil of quality 10 PPM.",
#     "Buy 20 MT Gasoil of quality 5000 PPM.",
#     "Buy 1000 MT, 10 PPM gasoil Through DAP.",
#     "Purchase Cotton",
#     "Bought gasoil of Quality 1000 PPM of Quantity 2000 MT using CIF.",
#     "Sold 1 MT, 100 ppm gasoil, on CIF terms, in USD",
#     "Buy Gasoil FOB Singapore for loading from Port of Singapore",
#     "Buy gas oil 5000 MT of 500ppm sulphur ex -CIF from B"

# ]

TEST_DATA = [
    "Sell 2 MT, 10ppm crude to Aramco, in USD, ex DAP, from port of Brisbane, Australia to Buenas Aires port, Argentina."

]

@plac.annotations(
    model=("Model name. Defaults to blank 'en' model.", "option", "m", str),
    output_dir=("Optional output directory", "option", "o", Path),
    n_iter=("Number of training iterations", "option", "n", int),
)
def main(model=None, output_dir=None, n_iter=100):
    """Load the model, set up the pipeline and train the entity recognizer."""
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
    for _, annotations in TRAIN_DATA:
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
            print("Trained model from scratch:")
        for itn in range(n_iter):
            random.shuffle(TRAIN_DATA)
            losses = {}
            # batch up the examples using spaCy's minibatch
            batches = minibatch(TRAIN_DATA, size=compounding(4.0, 32.0, 1.001))
            for batch in batches:
                texts, annotations = zip(*batch)
                nlp.update(
                    texts,  # batch of texts
                    annotations,  # batch of annotations
                    drop=0.5,  # dropout - make it harder to memorise data
                    losses=losses,
                )
            if itn % 10==0:
                print("for the iteration:", itn, "Losses:", losses)

    # test the trained model
    # for text, _ in TRAIN_DATA:
    #     doc = nlp(text)
    #     print("Entities", [(ent.text, ent.label_) for ent in doc.ents])
    #     print("Tokens", [(t.text, t.ent_type_, t.ent_iob) for t in doc])
    for text in TEST_DATA:
        doc = nlp(text)
        print(doc.ents)
        print("Entities", [(ent.text, ent.label_) for ent in doc.ents])
        print("Tokens", [(t.text, t.ent_type_, t.ent_iob) for t in doc])

    # save model to output directory
    if output_dir is not None:
        output_dir = Path(output_dir)
        if not output_dir.exists():
            output_dir.mkdir()
        nlp.to_disk(output_dir)
        print("Saved model to", output_dir)

        # test the saved model
        print("Loading from", output_dir)
        nlp2 = spacy.load(output_dir)
        for text, _ in TRAIN_DATA:
            doc = nlp2(text)
            print("Entities", [(ent.text, ent.label_) for ent in doc.ents])
            print("Tokens", [(t.text, t.ent_type_, t.ent_iob) for t in doc])


if __name__ == "__main__":
    main(model=None, output_dir='D:/work/nlp/scratch/model')

    # Expected output:
    # Entities [('Shaka Khan', 'PERSON')]
    # Tokens [('Who', '', 2), ('is', '', 2), ('Shaka', 'PERSON', 3),
    # ('Khan', 'PERSON', 1), ('?', '', 2)]
    # Entities [('London', 'LOC'), ('Berlin', 'LOC')]
    # Tokens [('I', '', 2), ('like', '', 2), ('London', 'LOC', 3),
    # ('and', '', 2), ('Berlin', 'LOC', 3), ('.', '', 2)]