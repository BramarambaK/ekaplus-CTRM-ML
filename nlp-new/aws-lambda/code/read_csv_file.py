import csv

fields = []
nlp_response_map_json = {}

def make_resp_map(csvreader, tag_idx, mapping_idx):
    for row in csvreader:
        nlp_response_map_json[row[tag_idx]] = row[mapping_idx]
    return nlp_response_map_json

def read_csv_file(filename):
    with open(filename, 'r', encoding="utf8") as csvfile:
        csvreader = csv.reader(csvfile)
        fields = next(csvreader)
        if 'Tag' in fields[0]:
            nlp_response_map = make_resp_map(csvreader, 0, 1)
        else:
            nlp_response_map = make_resp_map(csvreader, 1, 0)
    return nlp_response_map