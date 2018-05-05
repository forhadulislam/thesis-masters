from flask import Flask, render_template, request
import sys, tweepy, csv, gensim, nltk
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

allRanges = {
    'extremely_low': {'score': 0, 'words': ['lowest', 'slightest', 'least', 'extremely low']},
    'very_low': {'score': 0.16, 'words': ['lower', 'very low']},
    'low': {'score': 0.32, 'words': ['low']},
    'average': {'score': 0.48, 'words': ['medium', 'average']},
    'high': {'score': 0.64, 'words': ['high']},
    'very_high': {'score': 0.80, 'words': ['higher', 'very high']},
    'extremely_high': {'score': 1, 'words': ['highest', 'maximum', 'extremely high']},
}

'''
	Sentence similarity
'''


def penn_to_wn(tag):
    """ Convert between a Penn Treebank tag to a simplified Wordnet tag """
    if tag.startswith('N'):
        return 'n'

    if tag.startswith('V'):
        return 'v'

    if tag.startswith('J'):
        return 'a'

    if tag.startswith('R'):
        return 'r'

    return None


def tagged_to_synset(word, tag):
    wn_tag = penn_to_wn(tag)
    if wn_tag is None:
        return None

    try:
        return wn.synsets(word, wn_tag)[0]
    except:
        return None


def sentence_similarity(sentence1, sentence2):
    """ compute the sentence similarity using Wordnet """
    # Tokenize and tag
    sentence1 = pos_tag(word_tokenize(sentence1))
    sentence2 = pos_tag(word_tokenize(sentence2))

    # Get the synsets for the tagged words
    synsets1 = [tagged_to_synset(*tagged_word) for tagged_word in sentence1]
    synsets2 = [tagged_to_synset(*tagged_word) for tagged_word in sentence2]

    # Filter out the Nones
    synsets1 = [ss for ss in synsets1 if ss]
    synsets2 = [ss for ss in synsets2 if ss]

    score, count = 0.0, 0

    # For each word in the first sentence
    for synset in synsets1:
        # Get the similarity value of the most similar word in the other sentence
        best_score = max([synset.path_similarity(ss) for ss in synsets2])

        # Check that the similarity could have been computed
        if best_score is not None:
            score += best_score
            count += 1

    # Average the values
    score /= count
    return score


def symmetric_sentence_similarity(sentence1, sentence2):
    """ compute the symmetric sentence similarity using Wordnet """
    return (sentence_similarity(sentence1, sentence2) + sentence_similarity(sentence2, sentence1)) / 2


'''
	Sentence similarity ends
'''

coreCategories = [
    "The diet has rapid weight loss potential",
    "The diet has strong long-term success potential",
    "The diet is affordable",
    "It is mentally stick to the diet",
    "The diet provides all the nutrients needed for well-being",
    "The diet is generally recommended by others"
]

coreCategories = [
    'weight loss',
    'cost',
    'success',
    'nutrition',
    'recommendation',
    'mental effort'
]


@app.route("/")
def main():
    inputText = searchResults = ""
    posText = ""
    finalOutput = []
    quantifier = {}
    if request.method == 'GET':
        inputText = request.args.get('query')
        if inputText:

            # Finding Quantifier
            for cRange in allRanges:
                for cQuantifier in allRanges[cRange]['words']:
                    print(inputText.find(cQuantifier), allRanges[cRange]['score'])

            myWord = Word('weight')
            print(myWord.synonyms())

            # Google search
            searchResults = google.search(inputText, num_page)
            posText = nltk.pos_tag(word_tokenize(inputText))
            for corecat in coreCategories:
                # score = sentence_similarity(inputText, corecat)
                score = symmetric_sentence_similarity(inputText, corecat)
                finalOutput.append(score)
                print(corecat, score)

    return render_template('index.html', inputText=inputText, posText=posText, finalOutput=finalOutput,
                           searchResults=searchResults)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
