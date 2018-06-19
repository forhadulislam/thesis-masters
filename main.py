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
from bs4 import BeautifulSoup

# Thesaurus-API - https://github.com/Manwholikespie/thesaurus-api
from libs.thesaurus.thesaurus import Word

num_page = 1

stop = set(stopwords.words('english'))
punctuation = ['(', ')', '?', ':', ';', ',', '.', '!', '/', '"', "'"]

app = Flask(__name__)


negations = ['not', 'no', 'nothing']

allRanges = {
    'extremely_low': {'score': 0, 'index': 1, 'words': ['lowest', 'slightest', 'least', 'extremely low']},
    'very_low': {'score': 0.16, 'index': 2, 'words': ['lower', 'very low', 'so low']},
    'low': {'score': 0.32, 'index': 3, 'words': ['low']},
    'average': {'score': 0.48, 'index': 4, 'words': ['medium', 'average']},
    'high': {'score': 0.64, 'index': 5, 'words': ['high']},
    'very_high': {'score': 0.80, 'index': 6, 'words': ['higher', 'very high', 'so high']},
    'extremely_high': {'score': 1, 'index': 7, 'words': ['highest', 'maximum', 'extremely high']},
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
    'weight-loss': { 'words': ['fat loss', 'lose weight', 'losing weight'], 'id': 6 },
    'cost': { 'words': ['cost','price', 'worth', 'expense', 'money'], 'id': 8 },
    'success': { 'words': ['success','progress','benefit'], 'id': 7 },
    'nutrition': { 'words': ['nutrition', 'food', 'nutriment', 'vitamin'], 'id': 10 },
    'recommendation': { 'words': ['recommendation','recommended','suggestion', 'support'], 'id': 11 },
    'mental-effort': { 'words': ['mental effort','mentality', 'mental power', 'mental'], 'id': 9 }
}


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
    try:
        r = requests.post('https://api.scientificdiets.com/getrecommendations2.php',
                          data={'criteria_importances': criteria_importances, 'num_of_options': num_of_options,
                                'user_id': user_id})
        return json.loads(r.text)

    except:
        return False

def findQuantifier( queryWord ):

    resultOutput = {}

    for cRange in allRanges:
        for cQuantifier in allRanges[cRange]['words']:
            if ( len(queryWord) > len(cQuantifier) ) or ( len(cQuantifier) > len(queryWord) ):
                continue

            findaQuantifier = cQuantifier.find(queryWord)
            if findaQuantifier >= 0:
                resultOutput[cRange] = allRanges[cRange]['score']

    return resultOutput


def findCoreCategory( inputs ):
    output = {}

    varType = isinstance(inputs, list)

    if varType:
        # For each and every input check in the coreCategories
        for inp in inputs:
            for corecat in coreCategories:

                # Passing all words from the coreCategories to find in the input text
                aWord = findWords(coreCategories[corecat]['words'], inp)

                # If match found
                if aWord:
                    output[corecat] = {}
                    output[corecat]['found'] = True

    return output

def findReverseQuantifier( input ):
    output = {}

    if len(input):

        keyCat, valueCat = input.items()[0]
        reverseIndex = -1
        try:
            if len(allRanges[keyCat]):
                rangeIndex = allRanges[keyCat]['index']
                reverseIndex = len(allRanges) - rangeIndex + 1
            else:
                return output

        except:
            return output

        for aQuantifier in allRanges:
            if (allRanges[aQuantifier]['index'] == reverseIndex):
                output[aQuantifier] = allRanges[aQuantifier]['score']
                return output


    return output



@app.route("/")
def main():
    inputText = searchResults = posText = ""
    finalOutput = {}
    quantifier = {}
    findTheCategories = {}
    allNegations = {}
    gSearchOutputs = []

    apiOutput = False

    if request.method == 'GET':
        inputText = request.args.get('query')
        if inputText:

            # New Part

            # POS Tagging
            posText = nltk.pos_tag(word_tokenize(inputText))

            for idx, postag in enumerate(posText):

                pWord = postag[0]
                pType = postag[1]

                # Finding if the word is JJ or Adjective
                if pType == 'JJ':

                    categories = []

                    findWordCategory = False
                    findWordQuantifier = False

                    try:
                        categories.append(posText[idx + 1])
                    except:
                        pass

                    try:
                        categories.append(posText[idx + 2])
                    except:
                        pass

                    # Finding if the previous word
                    # is RB or Adverb
                    if posText[idx-1] and posText[idx-1][1] == 'RB':
                        prevWord = posText[idx-1][0]
                        fWord = prevWord + ' ' + pWord
                        findQ = findQuantifier( fWord )




                        if posText[idx -2] and posText[idx - 2][1] == 'RB':
                            prevPrevWord = posText[idx -2]
                            prevPrevWord = prevPrevWord[0]

                            # Finding negations
                            if prevPrevWord in negations:
                                # if negation is found
                                print('query RB RB JJ: negation', fWord, findQ)
                                print('query RB RB JJ: negation', findReverseQuantifier( findQ ) )
                                findWordCategory = findCoreCategory(categories)
                                findWordQuantifier = findQ
                                findWordQuantifier = findReverseQuantifier( findQ )
                            else:
                                # if negation isn't found
                                print('query RB JJ 213', fWord, findQ, prevPrevWord)

                                findWordCategory = findCoreCategory(categories)
                                findWordQuantifier = findQ
                        else:

                            # If the word before JJ or Ajdective is found in negation or else
                            if prevWord in negations:
                                findQ = findQuantifier(pWord)
                                print('query RB RB JJ: negation 222', pWord, findQ)
                                print('query RB RB JJ: negation 223', findReverseQuantifier(findQ))
                                findWordCategory = findCoreCategory(categories)
                                findWordQuantifier = findReverseQuantifier( findQ )

                            else:

                                print('query RB JJ 229', fWord, findQ)
                                findWordCategory = findCoreCategory(categories)
                                findWordQuantifier = findQ



                    else:
                        findQ = findQuantifier(pWord)
                        prevWord = posText[idx - 1][0]
                        print('prevWord')
                        print(prevWord)
                        if prevWord in negations:
                            # if negation is found
                            print('query RB JJ: negation 242', findQ)
                            print('query RB JJ: negation 243', findReverseQuantifier(findQ))
                            findWordCategory = findCoreCategory(categories)
                            findWordQuantifier = findReverseQuantifier( findQ )
                        else:
                            # if negation isn't found
                            print('query', findQ)
                            findWordCategory = findCoreCategory(categories)
                            findWordQuantifier = findQ




                    # Append the coreCategory

                    if len(findWordCategory):
                        try:
                            keyCat, valueCat = findWordCategory.items()[0]
                            keyQnt, valueQnt = findWordQuantifier.items()[0]

                            findTheCategories[keyCat] = valueCat

                            quantifierKey = findWordQuantifier.items()[0]
                            findTheCategories[keyCat]['quantifier'] = {quantifierKey[0]: quantifierKey[1] }
                            findTheCategories[keyCat]['score'] = quantifierKey[1]
                            quantifier[keyQnt] = valueQnt
                        except:
                            pass


            # New Part


            for corecat in coreCategories:

                print(corecat)
                # If match found
                if corecat not in findTheCategories:
                    findTheCategories[corecat] = {}
                    findTheCategories[corecat]['found'] = False
                    findTheCategories[corecat]['score'] = 0
                '''
                else:
                    finalOutput[corecat] = {}
                    finalOutput[corecat]['found'] = False
                '''



            criteria_importances = []
            for coreCategory in coreCategories:
                if 'score' in findTheCategories[coreCategory].keys():
                    currentScore = findTheCategories[coreCategory]['score']
                else:
                    currentScore = 0

                criteria_importances.append( [ coreCategories[coreCategory]['id'], currentScore ] )

            print('Line 299')
            print(criteria_importances)
            #criteria_importances = [[6, "7.30"], [7, "9.56"], [8, "18.52"], [9, "37.50"], [10, "49.70"], [11, "61.45"]]

            apiOutput = sendDietApiRequest(criteria_importances, 6)

            # Google search
            searchResults = google.search(inputText, num_page)

            searchResults = searchResults[0:6]

            for gResult in searchResults:
                analyzedResult = {}
                try:
                    r = requests.get(gResult.link)
                    soup = BeautifulSoup(r.text, 'html.parser')

                    headings2 = soup.find_all('h2')[0:7]
                    headings3 = soup.find_all('h3')[0:7]

                    analyzedResult['name'] = gResult.name
                    analyzedResult['link'] = gResult.link
                    analyzedResult['description'] = gResult.description

                    analyzedResult['headings2'] = None
                    analyzedResult['headings3'] = None

                    if headings2:
                        analyzedResult['headings2'] = headings2

                    if headings3:
                        analyzedResult['headings3'] = headings3
                except:
                    pass

                gSearchOutputs.append(analyzedResult)


    return render_template('index.html', inputText=inputText, posText=posText, finalOutput=finalOutput,
                           gSearchOutputs=gSearchOutputs, quantifier=quantifier, apiOutput=apiOutput, findTheCategories=findTheCategories)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
