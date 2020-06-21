import difflib

class Utils():
    # Method to calculate the Match Score of the titles
    def getMatchScore(self, title1, title2):
        #result = int(100 - abs(String.LevenshteinDistance(title1, title2)))
        result = int(difflib.SequenceMatcher(None, title1, title2).ratio() * 100)

        return result