from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score
from privacy import UserData
from authenticate import SpotifyAccess
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import requests
import pandas as pd
import numpy as np

conn = UserData.connection()
authenticate = SpotifyAccess()

class DataWorkings():
    
    def __init__(self, goodPlaylistURI, badPlaylistURI, newPlaylistURI):
        self.goodSongs, self.badSongs, self.newSongs, self.pulledData = {}, {}, {}, {}
        self.goodPlaylist, self.badPlaylist, self.newPlaylist = goodPlaylistURI, badPlaylistURI, newPlaylistURI
        self.data, self.target, self.criteria = [], [], [3, 4, 9] # [3, 4, 9]
        self.features = {3: "Danceability", 4: "Energy", 5: "Key", 6: "Loudness", 7: "Mode", 8: "Speechiness", 9: "Acousticness", 10: "Instrumentalness", 11: "Liveness",
                         12: "Valence", 13: "Tempo"}
        self.playlists, self.playlistURI = [self.goodSongs, self.badSongs, self.newSongs], [self.goodPlaylist, self.badPlaylist, self.newPlaylist]
        self.optimalNeighbours = 0
    
    def getSongs(self, accessDatabase, cur = conn.cursor()):
        # API Call
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
                    # print(response) for Checking API Call Rate Limit Error 429

                    # Store in Database
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
        # Query Data
        cur.execute("""SELECT * FROM importedMusic WHERE Playlist_URI = ? OR Playlist_URI = ?""", 
                   (self.goodPlaylist, self.badPlaylist,))
        
        # Label Data
        for row in cur.fetchall():
            temp = []
            for i in self.criteria:
                temp.append(row[i])
            self.data.append(temp)
        self.target = np.array(([0]*(len(self.goodSongs.keys()))) + ([1]*(len(self.badSongs.keys())))) # Always the same size
        return self.data, self.target
    
    def elbowMethod(self, cur = conn.cursor(), neighbour_tracking = {}):

        # Get Optimal K Value
        X_train, X_test, Y_train, Y_test = train_test_split(np.array(self.data), np.array(self.target), random_state = 100, shuffle = True, test_size = 0.33)
        print("\n")

        for i in range(1, 19):
            knn = KNeighborsClassifier(n_neighbors = i, algorithm = "kd_tree")
            knn.fit(X_train, Y_train)
            scores = cross_val_score(knn, X_train, Y_train, cv=5, scoring='accuracy')
            print(f"Error Rate with {i} Neighbours: {round(1 - scores.mean(), 5)}%")
            neighbour_tracking[i] = round(1 - scores.mean(), 5)

        plt.plot(neighbour_tracking.keys(), neighbour_tracking.values())
        plt.suptitle("k Neighbours vs. Error Rate Percentage")
        plt.xlabel("k Neighbours")
        plt.ylabel("Cross-Validated Error Rate")
        plt.show()

        self.optimalNeighbours = 8 # Set optimalNeighbours based off Elbow Method Plot

        print("\n")
        return self.optimalNeighbours

    def makePrediction(self, cur = conn.cursor(), color_map = {0: '#010033', 1: '#c4dcf5'}):

        # Model Setup
        X_train, X_test, Y_train, Y_test = train_test_split(np.array(self.data), np.array(self.target), random_state = 250, shuffle = True, test_size = 0.33)
        spotifyDataSet = pd.DataFrame(X_train, columns = [self.features[feature] for feature in self.criteria])

        # Plotting
        pd.plotting.scatter_matrix(spotifyDataSet, c = [color_map[label] for label in Y_train], figsize = (15,15), marker = 'o', hist_kwds = {"bins": 20}, alpha = 0.8)
        plt.suptitle("KNN Scatter Matrix of JC's Spotify Discography") 
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#010033', markersize=10, label="Good Songs"),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#c4dcf5', markersize=10, label="Bad Songs")
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        plt.show(block=True)

        # Model
        knn = KNeighborsClassifier(n_neighbors = self.optimalNeighbours, algorithm = "kd_tree")
        knn.fit(X_train, Y_train)

        # Examine Test Set Results
        y_pred = knn.predict(X_test)
        accuracy = accuracy_score(Y_test, y_pred)
        
        print(f"\nTest Set Accuracy Rate: {round(accuracy, 3)}%\n")

        # Make Predictions on New Data
        cur.execute("""SELECT * FROM importedMusic WHERE Playlist_URI = ?""", (self.newPlaylist,))
        dontLike, like = [], []
        for row in cur.fetchall():
            temp = []
            for i in self.criteria:
                temp.append(row[i])
            X_new = np.array([temp])
            prediction = knn.predict(X_new)
            if prediction == 0:
                like.append(row[1] + " by " + row[2])
            else:
                dontLike.append(row[1] + " by " + row[2])

        print("List of songs I think you won't like:\n-------------------------------------")
        for song in dontLike:
            print(song)

        print("\nList of songs I think you will like:\n------------------------------------")
        for song in like:
            print(song)
        print("\n")

client = DataWorkings('4e9TQ0JBW0F09qnLtzR41t', '4qg4Zbhqn4Db21U5XWeYwc', '5pfmBIVgAsRuUpcopGW4Um')
client.getSongs(False) # True if Database Empty
client.formulateData()
client.elbowMethod()
client.makePrediction()