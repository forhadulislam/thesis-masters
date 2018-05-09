from flask import Flask, render_template, request
import sys, tweepy, csv, gensim, nltk, requests, json
import numpy as np
import re, string, timeit
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.stem import WordNetLemmatizer
from nltk.stem.porter import PorterStemmer
from nltk import word_tokenize, pos_tag
from nltk.corpus import wordnet as wn

from google import google

# Thesaurus-API - https://github.com/Manwholikespie/thesaurus-api
from libs.thesaurus.thesaurus import Word

num_page = 1

stop = set(stopwords.words('english'))
punctuation = ['(', ')', '?', ':', ';', ',', '.', '!', '/', '"', "'"]

app = Flask(__name__)



'''
	Find words
'''

def findWords(data, sentence):

    for cWord in data:
        if cWord in sentence:
            print(cWord)
            return cWord

    return False


def sendDietApiRequest(criteria_importances, num_of_options=6, user_id='msc_forhadul'):
    #criteria_importances = [[6, "7.30"], [7, "9.56"], [8, "18.52"], [9, "37.50"], [10, "49.70"], [11, "61.45"]]

    try:
        r = requests.post('https://api.scientificdiets.com/getrecommendations2.php',
                          data={'criteria_importances': criteria_importances, 'num_of_options': num_of_options,
                                'user_id': user_id})
        return json.loads(r.text)

    except:
        return False

negations = ['not', 'no', 'nothing']

allRanges = {
    'extremely_low': {'score': 0, 'words': ['lowest', 'slightest', 'least', 'extremely low']},
    'very_low': {'score': 0.16, 'words': ['lower', 'very low']},
    'low': {'score': 0.32, 'words': ['low']},
    'average': {'score': 0.48, 'words': ['medium', 'average']},
    'high': {'score': 0.64, 'words': ['high']},
    'very_high': {'score': 0.80, 'words': ['higher', 'very high']},
    'extremely_high': {'score': 1, 'words': ['highest', 'maximum', 'extremely high']},
}

coreCategoriesB = [
    "The diet has rapid weight loss potential",
    "The diet has strong long-term success potential",
    "The diet is affordable",
    "It is mentally stick to the diet",
    "The diet provides all the nutrients needed for well-being",
    "The diet is generally recommended by others"
]

coreCategories = {
    'weight-loss': ['fat loss', 'lose weight', 'losing weight'],
    'cost': ['cost','price', 'worth', 'expense', 'money'],
    'success': ['success','progress','benefit'],
    'nutrition': ['nutrition', 'food', 'nutriment', 'vitamin'],
    'recommendation': ['recommendation','recommended','suggestion', 'support'],
    'mental-effort': ['mental effort','mentality', 'mental power']
}


@app.route("/")
def main():
    inputText = searchResults = ""
    posText = ""
    finalOutput = {}
    quantifier = {}
    allNegations = {}

    if request.method == 'GET':
        inputText = request.args.get('query')
        if inputText:

            # Finding Quantifier
            for cRange in allRanges:
                for cQuantifier in allRanges[cRange]['words']:
                    findQuantifier = inputText.find(cQuantifier)
                    if findQuantifier >= 0:
                        quantifier[cRange] = allRanges[cRange]['score']
                        print(findQuantifier)


            myWord = Word('weight')
            print(myWord.synonyms())

            print( 'findWords()' )
            print( findWords(['cost', 'weight'], inputText) )

            # Google search
            searchResults = google.search(inputText, num_page)
            posText = nltk.pos_tag(word_tokenize(inputText))

            for corecat in coreCategories:

                # Passing all words from the coreCategories to find in the input text
                aWord = findWords(coreCategories[corecat], inputText)
                print('aWord')
                print( aWord )
                # If match found
                if aWord:
                    finalOutput[corecat] = {}
                    finalOutput[corecat]['found'] = True
                    for aQuantifier in quantifier:
                        findSelectedQuantifier = inputText.find(aQuantifier)
                        if findSelectedQuantifier >= 0:
                            finalOutput[corecat]['score'] = quantifier[aQuantifier]
                        else:
                            finalOutput[corecat]['score'] = 0.1
                else:
                    finalOutput[corecat] = {}
                    finalOutput[corecat]['found'] = False

            # Finding Negations
            for negate in allNegations:
                findNegations = inputText.find(negate)
                if findNegations >= 0:
                    allNegations[corecat]['score'] = quantifier[aQuantifier]

        criteria_importances = [[6, "7.30"], [7, "9.56"], [8, "18.52"], [9, "37.50"], [10, "49.70"], [11, "61.45"]]

        apiOutput = sendDietApiRequest(criteria_importances, 10)

    return render_template('index.html', inputText=inputText, posText=posText, finalOutput=finalOutput,
                           searchResults=searchResults, quantifier=quantifier, apiOutput=apiOutput)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
