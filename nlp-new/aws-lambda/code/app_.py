from flask import Flask, request, jsonify
from pathlib import Path
import spacy
import train_model_aws
import train_model
# port = 7676

# Constants
output_dir = 'D:/work/nlp/dev/model'

def get_prediction(test_data):
    print("Loading from", output_dir)
    nlp = spacy.load(output_dir)
    entities_ = []
    doc = nlp(test_data)
    print("Entities", [(ent.text, ent.label_) for ent in doc.ents])
    print("Tokens", [(t.text, t.ent_type_, t.ent_iob) for t in doc])
    entities__ = [{ent.text:ent.label_} for ent in doc.ents]
    result = {}
    print(entities__)
    for d in entities__:
        result.update(d)
    return result

def get_headers_and_data(request):
    headers_post, input_body = request.headers, request.json
    return headers_post, input_body

app = Flask(__name__)
@app.route("/process-sentence", methods = ['POST'])
def process_():
    headers, body = get_headers_and_data(request)
    sent = body["sentence"]
    entities_ = get_prediction(sent)
    print(entities_)
    return entities_

@app.route("/train-nlp", methods = ['POST'])
def train():
    headers, body = get_headers_and_data(request)
    # train_model_aws.main(model='en_core_web_sm', user_input=body)
    train_model.main(model='en_core_web_sm', output_dir=output_dir, user_input=body)
    msg = {"msg":"Trained the nlp model."}
    return msg

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7676, debug=False)