import json
import flask
from flask import request, jsonify
import networkx as nx
from markupsafe import escape


#Step One: Get User's Intent
messagesFromBot = [
    {"conversationId": "1",
    "type": "webhook",
    "name": "message_sent",
    "messages": [
      {"type": "message",
       "data":
           {"type": "text/plain",
            "content": "Bürgerlichen Gesetzbuch"
           }
       }]
     },
    {"conversationId": "2",
    "type": "webhook",
    "name": "message_sent",
    "messages": [
      {"type": "message",
       "data":
           {"type": "text/plain",
            "content": "Wann sind ihre Öffnungszeiten2?"
           }
       }]
     },
    {"conversationId": "3",
    "type": "webhook",
    "name": "message_sent",
    "messages": [
      {"type": "message",
       "data":
           {"type": "text/plain",
            "content": "Wann sind ihre Öffnungszeiten3?"
           }
       }]
     }
]
conversationId = messagesFromBot[0]['conversationId']
userIntents = []
for i in range(len(messagesFromBot)):
    userIntents.append(messagesFromBot[i]['messages'][0]['data']['content'])

messageFromBot = {"conversationId": "1",
    "type": "webhook",
    "name": "message_sent",
    "messages": [
      {"type": "message",
       "data":
           {"type": "text/plain",
            "content": "Bürgerlichen Gesetzbuch"
           }
       }]
     }



#Step Two: Read MietGraph
rentGraphD1 = nx.read_graphml("MietGraphD1.graphml")
rentGraphD2 = nx.read_graphml("MietGraphD2.graphml")

#Step Three: Search in Graph
#select data from node "text" where intent is a substring of node "name"

userIntent = "Bürgerlichen Gesetzbuch"
#test another intent
#userIntent = "Mietvertrag"
relatedDocuments = dict( (nodes,document['text']) for nodes,document in rentGraphD1.nodes().items() if userIntent in document['name'])
relatedDocuments2 = dict( (nodes,document['text']) for nodes,document in rentGraphD1.nodes().items() if userIntent in document['name'])
relatedDocuments.update(relatedDocuments2)


#Step Four: Create Response in JSON Format
def addRelatedDocuments(messages,msgType,msgData):
    messages['type'] = msgType
    messages['data'] = msgData

def extractMessageContents(relatedDocuments):
    data = {}
    messages = {}
    jsonResponse = {}
    for textKey in relatedDocuments.keys():
        data['type'] = "text/plain"
        data['content'] = relatedDocuments[textKey]
        addRelatedDocuments(messages,"message",data)
    ###TODO add multiple message to Json
    ###jsonResponse['conversationId'] = conversationId
    jsonResponse['messages'] = messages
    return jsonResponse

def getDocumentsBasedOnIntent(receivedIntent):
    jsonResponse = {}
    relatedDocuments = dict(
        (nodes, document['text']) for nodes, document in rentGraphD1.nodes().items() if receivedIntent in document['name'])
    return extractMessageContents(relatedDocuments)

def getDoumemtsBasedOnMessage(message):
    #conversationId = message['conversationId']
    intent = message['messages'][0]['data']['content']
    return getDocumentsBasedOnIntent(escape(intent))

#Step Five: Return the Response
app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.route("/0.0.0.0", methods=["GET"])
def defaultFunction():
    return """<h1>Retrieve Data From MietGraph</h1>
<p>A prototype API for retrieving data from renting glossary.</p>"""

@app.route("/", methods=["GET"])  #localhost
def home():
    return """<h1>Retrieve Data From MietGraph</h1>
<p>A prototype API for retrieving data from renting glossary.</p>"""




@app.route("/relatedDocuments/", methods=["GET"])
def api_response():
    return jsonify(getDocumentsBasedOnIntent(escape(userIntent)))

@app.route("/intentRelatedDocuments/<intent>", methods=["GET"])
def api_response_intent(intent):
    return jsonify(getDocumentsBasedOnIntent(escape(intent)))

@app.route("/messageRelatedDocuments/<message>", methods=["GET"])
def api_response_message(message):
    return jsonify(getDoumemtsBasedOnMessage(message))
if __name__ == '__main__':
    app.run(debug=True)

