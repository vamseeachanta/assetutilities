import nltk
from nltk.stem import WordNetLemmatizer

wordnet_lemmatizer = WordNetLemmatizer()

text = "studies studying cries cry"
tokenization = nltk.word_tokenize(text)
lemma_array = [wordnet_lemmatizer.lemmatize(w) for w in tokenization]
print(lemma_array)
