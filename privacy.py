import sqlite3
conn = None

class UserData(object):
    
    def sendCredentials():
        clientID = ''
        clientSecret =''    
        return [clientID, clientSecret]

    def connection():
        global conn
        if conn == None:
            try: 
                conn = sqlite3.connect("importedMusic")
            except:
                conn = sqlite3.connect("importedMusic" + ".db")
        cur = conn.cursor()
        musicTable = """ CREATE TABLE IF NOT EXISTS importedMusic (SongID text PRIMARY KEY, Title text, Artist text, Danceability float, Energy float, Key int, 
                        Loudness float, Mode int, Speechiness float, Acousticness float, Instrumentalness float, Liveness float, Valence float, Tempo float,
                        Playlist_URI text); """
        try:
            cur.execute(musicTable)
            conn.commit()
        except:
            print("Database already exists.") 
        return conn
    
