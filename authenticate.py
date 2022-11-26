import base64
import datetime
import requests
from privacy import UserData

id = UserData.sendCredentials()

class SpotifyAccess(object):

    accessTokenExpires = datetime.datetime.now()
    accessTokenDidExpire = True
    tokenURL = "https://accounts.spotify.com/api/token"
    
    def __init__(self):
        self.clientID = id[0]
        self.clientSecret = id[1]
  
    def getClientCredentials(self):
        clientID = self.clientID
        clientSecret = self.clientSecret
        if clientSecret == None or clientID == None:
            raise Exception("You must set clientID and clientSecret")
        clientCreds = f"{clientID}:{clientSecret}"
        clientCreds64 = base64.b64encode(clientCreds.encode())
        return clientCreds64.decode()
    
    def getTokenData(self):
        return {"grant_type": "client_credentials", "scope": "playlist-modify-private playlist-modify-public user-library-read playlist-read-private"}
    
    def getTokenHeader(self):
        clientCreds64 = self.getClientCredentials()
        return {"Authorization": f"Basic {clientCreds64}"}
        
    def authenticateToken(self):
        tokenURL = self.tokenURL
        tokenData = self.getTokenData()
        tokenHeader = self.getTokenHeader()
        r = requests.post(tokenURL, data = tokenData, headers = tokenHeader)
        if r.status_code not in range(200, 299):
            return False
        data = r.json()
        now = datetime.datetime.now()
        accessToken = data['access_token']
        expires_in = data['expires_in']
        expires = now + datetime.timedelta(seconds = expires_in)
        self.accessToken = accessToken
        self.accessTokenExpires = expires
        self.accessTokenDidExpire = expires < now
        return accessToken
