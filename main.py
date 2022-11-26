""" Developer Notes/Improvements

    Front end development -> javascript/flask/html/css???
    Normalize data points -> scale all metrics from 1-10
    Elbow method -> determine optimal k value -> read documentation
    Feature engineering -> add/subtract metrics

"""

from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from privacy import UserData
from authenticate import SpotifyAccess
import matplotlib.pyplot as plt
import requests
import pandas as pd
import numpy as np

conn = UserData.connection()
authenticate = SpotifyAccess()

class DataWorkings(object):
    
    def __init__(self, goodPlaylistURI, badPlaylistURI, newPlaylistURI):
        self.goodSongs, self.badSongs, self.newSongs, self.pulledData = {}, {}, {}, {}
        self.goodPlaylist, self.badPlaylist, self.newPlaylist = goodPlaylistURI, badPlaylistURI, newPlaylistURI
        self.data, self.target, self.criteria = [], [], [3, 4, 6, 9]
        self.playlists, self.playlistURI = [self.goodSongs, self.badSongs, self.newSongs], [self.goodPlaylist, self.badPlaylist, self.newPlaylist]
    
    def getSongs(self, accessDatabase, cur = conn.cursor()):
        queries = ["https://api.spotify.com/v1/playlists/{}/tracks".format(self.goodPlaylist), 
                    "https://api.spotify.com/v1/playlists/{}/tracks".format(self.badPlaylist), 
                    "https://api.spotify.com/v1/playlists/{}/tracks".format(self.newPlaylist)]
        for i in range(len(queries)):
            response = requests.get(queries[i], headers={"Authorization": "Bearer {}".format(authenticate.authenticateToken())}).json()
            for j in response["items"]:
                self.playlists[i][j["track"]["id"]] = {}
                self.playlists[i][j["track"]["id"]]["ID"], self.playlists[i][j["track"]["id"]]["Title"] = str(j["track"]["id"]), j["track"]["name"]
                self.playlists[i][j["track"]["id"]]["Artist(s)"] = j["track"]["artists"][0]["name"]
            if accessDatabase:
                for keys in self.playlists[i].keys():
                    query = "https://api.spotify.com/v1/audio-features/" + self.playlists[i][keys]["ID"]
                    response = requests.get(query, headers={"Authorization": "Bearer {}".format(authenticate.authenticateToken())}).json()
                    self.pulledData = {key: response[key] for key in response.keys() & {'danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness', 
                                    'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo'}}
                    try:
                        cur.execute("""INSERT INTO importedMusic (SongID, Title, Artist, Danceability, Energy, Key, Loudness, Mode, Speechiness, Acousticness, 
                                    Instrumentalness, Liveness, Valence, Tempo, Playlist_URI) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (self.playlists[i][keys]["ID"],
                                    self.playlists[i][keys]["Title"], self.playlists[i][keys]["Artist(s)"], self.pulledData['danceability'], self.pulledData['energy'], 
                                    self.pulledData['key'], self.pulledData['loudness'], self.pulledData['mode'],  self.pulledData['speechiness'], 
                                    self.pulledData['acousticness'], self.pulledData['instrumentalness'], self.pulledData['liveness'], self.pulledData['valence'], 
                                    self.pulledData['tempo'], self.playlistURI[i]))
                        conn.commit()
                    except:
                        continue

    def formulateData(self, cur = conn.cursor()):
        cur.execute("""SELECT * FROM importedMusic WHERE Playlist_URI = ? OR Playlist_URI = ?""", (self.goodPlaylist, self.badPlaylist,))
        for row in cur.fetchall():
            temp = []
            for i in self.criteria:
                temp.append(row[i])
            self.data.append(temp)
        self.target = np.array(([0]*(len(self.goodSongs.keys()))) + ([1]*(len(self.badSongs.keys()))))
        return self.data, self.target

    def makePrediction(self, cur = conn.cursor()):
        X_train, X_test, Y_train, Y_test = train_test_split(np.array(self.data), np.array(self.target), random_state = 0)
        spotifyDataSet = pd.DataFrame(X_train, columns = self.criteria)
        pd.plotting.scatter_matrix(spotifyDataSet, c = Y_train, figsize = (15,15), marker = 'o', hist_kwds = {"bins": 20}, alpha = 0.8)
        plt.show(block=True)
        knn = KNeighborsClassifier(n_neighbors = 3)
        knn.fit(X_train, Y_train)
        cur.execute("""SELECT * FROM importedMusic WHERE Playlist_URI = ?""", (self.newPlaylist,))
        for row in cur.fetchall():
            temp = []
            for i in self.criteria:
                temp.append(row[i])
            X_new = np.array([temp])
            prediction = knn.predict(X_new)
            if prediction == 0:
                print("You probably will like: " + row[1] + " - " + row[2])
            else:
                print("You probably won't like: " + row[1] + " - " + row[2])

client = DataWorkings('17U7o6IvKzqeKoIR7jRRKy', '1GXJtyfULnAAIQy4HKTDyQ', '37i9dQZEVXbfMjsPvoMXmt')
client.getSongs(False)
client.formulateData()
client.makePrediction()
#data_pd = pd.read_sql('SELECT * FROM importedMusic',conn)
#print(data_pd)
