import requests
import json
import random


def lambda_handler(event, context):
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event, context)
    elif event['request']['type'] == "IntentRequest":
        return intent_router(event, context)


def intent_router(event, context):
    # Custom Intents
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_end(event['request'], event['session'])
    # Required Intents
    if intent == "AMAZON.CancelIntent":
        return cancel_intent()
    if intent == "AMAZON.HelpIntent":
        return help_intent()
    if intent == "AMAZON.StopIntent":
        return stop_intent()


def on_launch(launch_request, session):
    return get_welcome_response()


def on_intent(intent_request, session):
    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
    global name
    if intent_name == "getAirdate":
        return getAirdate(intent, session)
    elif intent_name == "getDiscription":
        return getDiscription(intent, session)
    elif intent_name == "suggestShows":
        return suggestShows(intent, session)
    elif intent_name == "AMAZON.YesIntent":
        return on_yes(name, session)
    elif intent_name == "AMAZON.NoIntent":
        return on_session_ended(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.StopIntent":
        return on_session_ended(intent, session)
    elif intent_name == "AMAZON.CancelIntent":
        return on_session_ended(intent, session)
    elif intent == "SessionEndedRequest":
        return on_session_end()
    else:
        raise ValueError("Invalid intent")


def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Series Guide Application. " \
                    "You can ask me about air dates of your favourite TV shows by saying, " \
                    "when will Game of Thrones will air?"

    reprompt_text = "You can ask me about air dates of your favourite TV shows by saying, " \
                    "when will Game of Thrones will air?"

    should_end_session = False
    smallLink = None
    largeLink = None
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, smallLink, largeLink, should_end_session))


def getAirdate(intent_request_intent, session):
    try:
        tvSeriesName = intent_request_intent['slots']['TVSeries']['value']
    except KeyError:
        tvSeriesName = "error"
    url = "https://www.episodate.com/api/search?q="
    url1 = "https://www.episodate.com/api/show-details?q="
    myResponse = requests.get(url + tvSeriesName.replace(" ", "%20"), verify=True)
    jData = json.loads(myResponse.content)
    count = 0
    for key in jData["tv_shows"]:
        name = key["name"]
        if (name.lower() == tvSeriesName.lower()):
            show_id = key["id"]
            url1 = url1 + str(show_id)
            myResponse1 = requests.get(url1, verify=True)
            jData1 = json.loads(myResponse1.content)
            count += 1
            break

    card_title = "Air Date of " + tvSeriesName

    if tvSeriesName == "error":
        speech_output = "Didn't catch that. Speak again."
        reprompt_text = ""
        smallLink = None
        largeLink = None
    elif count == 0:
        speech_output = "TV Show not found. Speak Again."
        reprompt_text = ""
        smallLink = None
        largeLink = None
    elif jData1["tvShow"]["status"] == "Running" and jData1["tvShow"]["countdown"] == None:
        speech_output = "Air date of " + tvSeriesName + " is not yet announced."
        reprompt_text = ""
        smallLink = jData1["tvShow"]["image_path"]
        largeLink = jData1["tvShow"]["image_thumbnail_path"]
    elif jData1["tvShow"]["status"] == "Running":
        date = jData1["tvShow"]["countdown"]["air_date"]
        network = jData1["tvShow"]["network"]
        smallLink = jData1["tvShow"]["image_path"]
        largeLink = jData1["tvShow"]["image_thumbnail_path"]
        for episode in jData1["tvShow"]["episodes"]:
            if date == episode["air_date"]:
                ename = episode["name"]
                season = episode["season"]
                eno = episode["episode"]
        speech_output = "Next episode of " + tvSeriesName + " is episode " + str(eno) + " from Season " + str(
            season) + " and name of the episode is " + ename + ". It will air on " + date + " on " + network + "."
        reprompt_text = ""
    else:
        speech_output = "The Show has ended"
        reprompt_text = ""
        smallLink = jData1["tvShow"]["image_path"]
        largeLink = jData1["tvShow"]["image_thumbnail_path"]
    session_attributes = session
    should_end_session = True
    return build_response(session_attributes,
                          build_speechlet_response(card_title, speech_output, reprompt_text, smallLink, largeLink,
                                                   should_end_session))


name = "Game of Thrones"


def suggestShows(intent, session_attributes):
    url = "https://tv-v2.api-fetch.website/shows/page?sort=popularity&order=-1"
    try:
        intent = intent['slots']['genre']['value']
    except KeyError:
        intent = None

    if intent != None:
        url = url + "&genre=" + intent
        response = requests.get(url.replace("page", "1"), verify=True)
        data = json.loads(response.content)
    else:
        count = 1
        data = []
        while (count != 6):
            response = requests.get(url.replace("page", str(count)), verify=True)
            temp = json.loads(response.content)
            data.extend(temp)
            count += 1

    shows = random.choice(data)
    card_title = "Suggested Series"
    speech_output = "You can watch " + shows["title"] + ". " + "It's IMDb ratings are " + str(shows["rating"][
                                                                                                  "percentage"] / 10) + " out of 10. I can tell you about the TV Series. Do you want to know about " + \
                    shows["title"] + "?"
    reprompt_text = ""
    smallLink = shows["images"]["poster"].replace("http", "https")
    largeLink = smallLink
    should_end_session = False
    global name
    name = shows["title"]
    return build_response(session_attributes,
                          build_speechlet_response(card_title, speech_output, reprompt_text, smallLink, largeLink,
                                                   should_end_session))


def on_yes(name, session):
    url = "https://www.episodate.com/api/search?q="
    url1 = "https://www.episodate.com/api/show-details?q="
    myResponse = requests.get(url + name.replace(" ", "%20"), verify=True)
    jData = json.loads(myResponse.content)
    count = 0
    for key in jData["tv_shows"]:
        name1 = key["name"]
        if (name1.lower() == name.lower()):
            show_id = key["id"]
            url1 = url1 + str(show_id)
            myResponse1 = requests.get(url1, verify=True)
            jData1 = json.loads(myResponse1.content)
            count += 1
            break

    card_title = "Description of " + name
    smallLink = jData1["tvShow"]["image_path"]
    largeLink = jData1["tvShow"]["image_thumbnail_path"]
    disc = jData1["tvShow"]["description"].replace("<br>", "").replace("<b>", "").replace("</b>", "").replace("</i>",
                                                                                                              "").replace(
        "<i>", "")
    speech_output = disc
    reprompt_text = ""
    session_attributes = session
    should_end_session = True
    return build_response(session_attributes,
                          build_speechlet_response(card_title, speech_output, reprompt_text, smallLink, largeLink,
                                                   should_end_session))


def getDiscription(intent_request_intent, session):
    try:
        tvSeriesName = intent_request_intent['slots']['TVSeries']['value']
    except KeyError:
        tvSeriesName = "error"
    url = "https://www.episodate.com/api/search?q="
    url1 = "https://www.episodate.com/api/show-details?q="
    myResponse = requests.get(url + tvSeriesName.replace(" ", "%20"), verify=True)
    jData = json.loads(myResponse.content)
    count = 0
    for key in jData["tv_shows"]:
        name = key["name"]
        if (name.lower() == tvSeriesName.lower()):
            show_id = key["id"]
            url1 = url1 + str(show_id)
            myResponse1 = requests.get(url1, verify=True)
            jData1 = json.loads(myResponse1.content)
            count += 1
            break

    card_title = "Description of " + tvSeriesName

    if tvSeriesName == "error":
        speech_output = "Didn't catch that. Try again."
        reprompt_text = ""
        smallLink = None
        largeLink = None
    elif count == 0:
        speech_output = "TV Show not found. Try Again."
        reprompt_text = ""
        smallLink = None
        largeLink = None
    else:
        smallLink = jData1["tvShow"]["image_path"]
        largeLink = jData1["tvShow"]["image_thumbnail_path"]
        disc = jData1["tvShow"]["description"].replace("<br>", "").replace("<b>", "").replace("</b>", "").replace(
            "</i>", "").replace("<i>", "")
        speech_output = disc
        reprompt_text = ""
    session_attributes = session
    should_end_session = True
    return build_response(session_attributes,
                          build_speechlet_response(card_title, speech_output, reprompt_text, smallLink, largeLink,
                                                   should_end_session))


def on_session_ended(session_ended_request, session):
    speech_output = "Thankyou for using Series Guide. See You Again."
    reprompt_text = ""
    card_title = "Thankyou"
    session_attributes = session
    should_end_session = True
    smallLink = None
    largeLink = None
    return build_response(session_attributes,
                          build_speechlet_response(card_title, speech_output, reprompt_text, smallLink, largeLink,
                                                   should_end_session))


def on_session_end():
    speech_output = None
    reprompt_text = None
    card_title = None
    session_attributes = None
    should_end_session = True
    smallLink = None
    largeLink = None
    return build_response(session_attributes,
                          build_speechlet_response(card_title, speech_output, reprompt_text, smallLink, largeLink,
                                                   should_end_session))


def build_speechlet_response(title, output, reprompt_text, smallLink, largeLink, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Standard',
            'title': title,
            'text': output,
            "image": {
                "smallImageUrl": smallLink,
                "largeImageUrl": largeLink
            }
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }
