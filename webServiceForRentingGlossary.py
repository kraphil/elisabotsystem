import flask
from flask import request
import networkx as nx
from markupsafe import escape

# Read MietGraph
rentGraphD1 = nx.read_graphml("MietGraphD1.graphml")
rentGraphD2 = nx.read_graphml("MietGraphD2.graphml")


def searchInKnowledbase(userIntent):
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
    return extractMessageContents(relatedDocuments)


def getDoumemtsBasedOnMessage(message):
    # conversationId = message['conversationId']
    intent = message['messages'][0]['data']['content']
    return getDocumentsBasedOnIntent(escape(intent))


app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route("/0.0.0.0", methods=["GET"])
def defaultFunction():
    return """<h1>Retrieve Data From MietGraph</h1><p>A prototype API for retrieving data from renting glossary.</p>"""


@app.route("/", methods=["GET"])  # localhost
def home():
    return """<h1>Retrieve Data From MietGraph</h1><p>A prototype API for retrieving data from renting glossary.</p>"""


@app.route("/messageFromBot", methods=["POST"])
def api_get_message():
    return getDoumemtsBasedOnMessage(request.json)


@app.route("/intentRelatedDocuments/", methods=["POST", "GET"])
def api_response_intent():
    return getDocumentsBasedOnIntent(escape(request.args.get('intent', type=str)))


@app.route("/messageRelatedDocuments", methods=["POST"])
def api_response_message():
    return getDoumemtsBasedOnMessage(request.json)

if __name__ == '__main__':
    app.run(debug=True)
