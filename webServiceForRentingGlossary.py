import flask
from flask import request
import networkx as nx
from markupsafe import escape

# Read MietGraph
rentGraphD1 = nx.read_graphml("dataset/MietGraphD1.graphml")
rentGraphD2 = nx.read_graphml("dataset/MietGraphD2.graphml")


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


app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route("/0.0.0.0", methods=["GET"])
def defaultFunction():
    return """<h1>Retrieve Data From MietGraph</h1><p>A prototype API for retrieving data from renting glossary.</p>"""


@app.route("/", methods=["GET"])  # localhost
def home():
    return """<h1>Retrieve Data From MietGraph</h1><p>A prototype API for retrieving data from renting glossary.</p>"""


@app.route("/messageRelatedDocuments", methods=["POST"])
def api_response_message():
    intent = extractIntent(request.json)
    if(len(intent) == 0):
        return "No intention word detected!"    
    document = getDocumentsBasedOnIntent(intent)
    if(len(document) == 0):
        return f"No related information found for \"{intent}\" in knowledgebase!"
    return (document['messages']['data']['content'])


if __name__ == '__main__':
    app.run(debug=True)
