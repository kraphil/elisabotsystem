import json
import flask
import networkx as nx
import pandas as pd
import numpy as np
import requests
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


def extract_conversationId(message):
    return message['conversationId']


def extract_messages(bot_message):
    return bot_message['messages']
    # return message['messages'][0]['metaData']


def extractGlossaryProfileName(message):
    return message['messages'][0]['metaData']['glossaryProfileName']


def extractContent(message):
    content = message['metaData']['intent']['output'][0]['data']['content']
    return content


def extractTokens(content):
    tokens = np.unique(content.split(','))
    return tokens


def get_list_of_all_topics_name_url():
    # Read MietGraph
    rentGraph = read_miet_graph_data()
    graph = rentGraph.nodes(data=True)
    # Extract the urls from the graph
    data = {}
    data = [x[1] for x in graph]
    name_links = pd.DataFrame(data)[['name', 'url']]
    return name_links


def getLinks(name_links, token):
    name_link = name_links[name_links['name'].str.contains(token, regex=False)]
    name_link.drop_duplicates().dropna()
    return name_link


def getLinksForTokens(tokens, name_links):
    results = []
    for token in tokens:
        link = getLinks(name_links, token.strip()).values.tolist()
        results.append(link)
    return results


def check_message_validity(message):
    isvalid = False
    print(message['metaData']['intent']['output'])
    output = message['metaData']['intent']['output']
    for msg in output:
        if (msg["type"] == 'message' and msg['data'] and msg['data']['type'] == 'text/plain'):
            isvalid = True
        else:
            isvalid = False
    return isvalid


def endOfConversation():
    endOfConversationMessage = {
        "type": 'event',
        "name": 'endOfConversation'
    }
    return endOfConversationMessage


def createAnswer(conversationId, outputMessages):
    payload = {
      "conversationId" : conversationId,
      "messages": outputMessages
    }
    return json.dumps(payload)


app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.route("/0.0.0.0", methods=["GET"])
def defaultFunction():
    return """<h1>Glossar</h1>""" 


@app.route("/", methods=["GET"])  # localhost
def home():
    return """<h1>Glossar</h1>"""


@app.route("/linkToGlossary", methods=["POST"])
def api_response_token():
    referer = request.headers.get("Referer")
    if referer is None:
        referer = request.args.get("referer")
    referer = referer.replace("//", "https://")
    # logging.info("____ referer: %s", referer)
    endpointBaseUrl = referer + '/api/v1/conversation/send'

    bot_message = request.get_json(force=True)
    # logging.info("____ message: %s", bot_message)
    conversationId = extract_conversationId(bot_message)
    #glossaryProfileName = extractGlossaryProfileName(bot_message)
    messages = extract_messages(bot_message)
    output_text = "Weitere Informationen erhalten Sie, wenn Sie auf die folgenden Wörter klicken."

    name_links = get_list_of_all_topics_name_url()
    outputMessages = []
    for msg in messages:
        if (check_message_validity(msg)):
            content = extractContent(msg)
            tokens = extractTokens(content)
            #logging.info("____ tokens: %s", tokens)
            glossaryLinks = getLinksForTokens(tokens, name_links)
            logging.info("____ glossaryLinks: %s", glossaryLinks)
            if len(glossaryLinks)==0:
                htmlContent = '<p>' + "Im Glossar wurden keine entsprechenden Informationen gefunden." + '</p>'
                outputMessage = {
                    'type': 'message',
                    'data': {
                        'type': 'text/html',
                        'content': htmlContent
                    }
                }
            else:
                htmlContent = '<p>' + output_text + '</p>'
                for glossaryLink in glossaryLinks:
                    link = '<a href="' + glossaryLink[0][1] + '" target="_blank" >' + glossaryLink[0][0] + '</a><br>'
                    htmlContent += link
                    outputMessage = {
                        'type': 'message',
                        'data': {
                            'type': 'text/html',
                            'content': htmlContent
                        }
                    }
        else:
            outputMessage = msg
        outputMessages.append(outputMessage)
    outputMessages.append(endOfConversation())
    answer = createAnswer(conversationId, outputMessages)
    try:
        #logging.info("____ endpointUrl: %s", endpointBaseUrl)
        logging.info("____ Request data: {0}".format(outputMessages))
        response = requests.post(endpointBaseUrl, data=answer, headers={'content-type': 'application/json'})
        logging.info("____ Request endpoint response: {0}".format(response))
    except requests.exceptions.RequestException as e:
        logging.debug("____ Request endpoint error: {0}".format(e))
    return ('{}', 200)


if __name__ == '__main__':
    app.run(debug=True)
