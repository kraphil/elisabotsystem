import json
import flask
import networkx as nx
import pandas as pd
from flask import request
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[
                        logging.FileHandler("debug.log"),
                        logging.StreamHandler()
                    ]
                    )


def read_miet_graph_data():
    rentGraphD1 = nx.read_graphml("dataset/MietGraphD1.graphml")
    rentGraphD2 = nx.read_graphml("dataset/MietGraphD2.graphml")
    rent_graph = nx.compose(rentGraphD1, rentGraphD2)
    return rent_graph


def add_related_documents(messages, msgType, msgData):
    messages['type'] = msgType
    messages['data'] = msgData

def extract_conversationId(userMessage):
    if (len(userMessage) == 0):
        conversationId = ""
    else:
        conversationId = userMessage['conversationId']
    return conversationId


def createAnswer(metadata, conversationId, endpointBaseUrl, glossaryProfileName):
    payload = {
        "messages": metadata["intent"]["output"],
        "conversationId": conversationId,
        "endpointBaseUrl": endpointBaseUrl,
        "glossaryProfileName": glossaryProfileName
    }
    return json.dumps(payload)

def extractMetadata(message):
    return message[0].metaData

def getDocumentsURLBasedOnToken(token):
    # Read MietGraph
    rentGraph = read_miet_graph_data()
    graph = rentGraph.nodes(data=True)
    # Extract the urls from the graph
    data = {}
    data = [x[1] for x in graph if token in x[1]['name']]
    links = pd.DataFrame(data)[['name', 'url']]
    return links


app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route("/linkToRelatedDocuments", methods=["POST"])
def api_response_token():
    referer = request.headers.get("Referer")
    if referer is None:
        referer = request.args.get("referer")
    referer = referer.replace("//", "https://")
    logging.info("____ referer: %s", referer)
    endpointBaseUrl = referer

    messages = request.get_json(force=True)
    logging.info("____ message: %s", messages)
    conversationId = extract_conversationId(messages)
    metadata = extractMetadata(messages)
    logging.info("____ metadata: %s", metadata)
    ####tokens = listOfWords(message)
    tokens = metadata["intent"]["output"]
    glossaryProfileName = metadata["glossaryProfileName"]
    logging.info("____ tokens: %s", tokens)

    if (metadata):
        links = []
        for token in tokens:
            linksOfTokensDocument = getDocumentsURLBasedOnToken(token)
            if (len(linksOfTokensDocument) == 0):
                GlossaryDocument = {}
            else:
                links.append(linksOfTokensDocument)
        GlossaryDocument = linksOfTokensDocument['messages']['data']['content']
        # logging.info("____ GD: %s", GlossaryDocument)
        answer = createAnswer(links, conversationId, endpointBaseUrl,glossaryProfileName)
    # try:
    #     logging.info("____ endpointUrl: %s", endpointBaseUrl)
    #     logging.info("Request data: {0}".format(answer))
    #     sendOutputWithLinkedGlossaryWords(answer)
        # response = requests.post(endpointBaseUrl, data=answer, headers={'content-type': 'application/json'})
        # logging.info("Request endpoint response: {0}".format(response))
    # except requests.exceptions.RequestException as e:
    #     logging.debug("Request endpoint error: {0}".format(e))
    return ('{}', 200)


if __name__ == '__main__':
    app.run(debug=True)