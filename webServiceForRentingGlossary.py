import json
import flask
import networkx as nx
import requests
from flask import request
import logging

logging.basicConfig( level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)
def searchInKnowledbase(userIntent):
    # Read MietGraph
    rentGraphD1 = nx.read_graphml("dataset/MietGraphD1.graphml")
    rentGraphD2 = nx.read_graphml("dataset/MietGraphD2.graphml")
    # select data from node "text" where intent is a substring of node "name"
    relatedDocuments1 = dict(
        (nodes, document['text']) for nodes, document in rentGraphD1.nodes().items() if userIntent in document['name'])
    relatedDocuments2 = dict(
        (nodes, document['text']) for nodes, document in rentGraphD2.nodes().items() if userIntent in document['name'])
    relatedDocuments1.update(relatedDocuments2)
    return relatedDocuments1


def addRelatedDocuments(messages, msgType, msgData):
    messages['type'] = msgType
    messages['data'] = msgData


def extractMessageContents(relatedDocuments):
    data = {}
    messages = {}
    jsonResponse = {}
    for textKey in relatedDocuments.keys():
        data['type'] = "text/plain"
        data['content'] = relatedDocuments[textKey]
        addRelatedDocuments(messages, "message", data)
    jsonResponse['messages'] = messages
    return jsonResponse


def getDocumentsBasedOnIntent(receivedIntent):
    relatedDocuments = searchInKnowledbase(receivedIntent)
    if(len(relatedDocuments) == 0):
        messages = {}
        return messages
    return extractMessageContents(relatedDocuments)


def extractIntent(userMessage):
    if(len(userMessage) == 0):
        intent = ""
    else:
        intent = userMessage['messages'][0]['data']['content']
    return intent


def extractConversationId(userMessage):
    if(len(userMessage) == 0):
        conversationId = ""
    else:
        conversationId = userMessage['conversationId']
    return conversationId


def createAnswer(conversationId, GlossaryDocument):
    payload = {
      "conversationId" : conversationId,
      "messages": [
        {
          "type" : "message",
          "data" : {
            "type" : "text/plain",
            "content" : GlossaryDocument
          }
        }
      ]
    }
    return json.dumps(payload)

def getDocumentsBasedOnToken(token):
    # Read MietGraph
    rentG = nx.Graph()
    rentG.add_edges_from(nx.read_graphml("dataset/MietGraphD1.graphml"))
    rentG.add_edges_from(nx.read_graphml("dataset/MietGraphD2.graphml"))
    relatedDocuments = dict(
        (nodes, document['name'], document['url'], document['text']) for nodes, document in rentG.nodes().items() if
        token in document['name'])
    return relatedDocuments

app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route("/0.0.0.0", methods=["GET","POST"])
def defaultFunction():
    return """<h1>Retrieve Data From MietGraph</h1><p>A prototype API for retrieving data from renting glossary.</p>"""


@app.route("/", methods=["GET", "POST"])  # localhost
def home():
    return """<h1>Retrieve Data From MietGraph</h1><p>A prototype API for retrieving data from renting glossary...</p>"""


@app.route("/messageRelatedDocuments", methods=["POST"])
def api_response_message():
    referer = request.headers.get("Referer")
    if referer is None:
      referer = request.args.get("referer")
    referer = referer.replace("//", "https://")
    # logging.info("____ referer: %s", referer)

    endpointUrl = referer + "/api/v1/conversation/send"
    message =  request.get_json(force=True)
    logging.info("____ message: %s", message)

    conversationId = extractConversationId(message)
    intent = extractIntent(message)
    if(len(intent) == 0):
        GlossaryDocument = "No intention word detected!"
    else:
        document = getDocumentsBasedOnIntent(intent)
        if(len(document) == 0):
            GlossaryDocument = f"No related information found for \"{intent}\" in knowledgebase!"
        else:
            GlossaryDocument = document['messages']['data']['content']
        # logging.info("____ GD: %s", GlossaryDocument)
    answer = createAnswer(conversationId, GlossaryDocument)
    try:
      # logging.info("____ endpointUrl: %s", endpointUrl)
      # logging.info("Request data: {0}".format(answer))
      response = requests.post(endpointUrl, data=answer, headers={'content-type': 'application/json'})
      # logging.info("Request endpoint response: {0}".format(response))
    except requests.exceptions.RequestException as e:
      logging.debug("Request endpoint error: {0}".format(e))
    return ('{}', 200)


@app.route("/linkToRelatedDocuments", methods=["POST"])
def api_response_message():
    referer = request.headers.get("Referer")
    if referer is None:
      referer = request.args.get("referer")
    referer = referer.replace("//", "https://")
    ####
    logging.info("____ referer: %s", referer)

    endpointUrl = referer + "/api/v1/conversation/send"
    message =  request.get_json(force=True)
    ####
    logging.info("____ message: %s", message)

    conversationId = extractConversationId(message)

    ####tokens = listOfWords(message)
    tokens = message
    logging.info("____ tokens: %s", tokens)
    ######

    if(len(tokens) == 0):
        GlossaryDocument = "No intention word detected!"
    else:
        linksOfTokensDocument = getDocumentsBasedOnToken(tokens)
        if(len(linksOfTokensDocument) == 0):
            GlossaryDocument = {}
        else:
            GlossaryDocument = linksOfTokensDocument['messages']['data']['content']
        # logging.info("____ GD: %s", GlossaryDocument)
    answer = createAnswer(conversationId, GlossaryDocument)
    try:
      # logging.info("____ endpointUrl: %s", endpointUrl)
      # logging.info("Request data: {0}".format(answer))
      response = requests.post(endpointUrl, data=answer, headers={'content-type': 'application/json'})
      # logging.info("Request endpoint response: {0}".format(response))
    except requests.exceptions.RequestException as e:
      logging.debug("Request endpoint error: {0}".format(e))
    return ('{}', 200)


if __name__ == '__main__':
    app.run(debug=True)
