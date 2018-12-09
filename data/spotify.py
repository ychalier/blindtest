import datetime
import requests
import json

class Client:

	def __init__(self, token=None):
		self.token = token
		if self.token is None:
			self.authenticate()

	def authenticate(self):
		client_id = input("client id> ")
		client_secret = input("client secret> ")
		auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
		response = requests.post(
			"https://accounts.spotify.com/api/token",
			data = {
				"grant_type": "client_credentials"
			},
			auth = auth
		)
		token = json.loads(response.text)
		t = datetime.datetime.now() + datetime.timedelta(seconds=int(token["expires_in"]))
		print("Received token:", token["access_token"])
		print("Expires at:    ", t.strftime("%H:%M:%S"))
		self.token = token["access_token"]

	def request(self, url, params={}):
		response = requests.get(
			"https://api.spotify.com/v1/" + url,
			headers = {
				"Authorization": "Bearer " + self.token
			},
			params = params
		)
		print("{0}\t{1}".format(response.status_code, url))
		return json.loads(response.text)

	def search(self, query, max_results=50, verbose=False):
		params = {
			"q": query,
			"type": "playlist",
			"limit": 50
		}
		data = self.request("search", params)
		answers = []
		while True:
			for item in data["playlists"]["items"]:
				playlist = {
					"id": item["id"],
					"name": item["name"],
					"tracks": str(item["tracks"]["total"]),
					"owner": item["owner"]["display_name"]
				}
				answers.append(playlist)
			if len(answers) < max_results and data["playlists"]["next"] is not None:
				data = self.request(data["playlists"]["next"][:27])
			else:
				break
		if verbose:
			for playlist in answers[:max_results]:
				print("\t".join([playlist["id"], playlist["tracks"], playlist["owner"], playlist["name"]]))

		return answers[:max_results]

	def list(self, playlist, verbose=False):
		data = self.request("playlists/" + playlist["id"] + "/tracks")
		answers = []
		while True:
			for item in data["items"]:
				track = {
					"title": item["track"]["name"],
					"artist": item["track"]["artists"][0]["name"],
					"rank": 101 - item["track"]["popularity"],
					"added": item["added_at"][:4]
				}
				answers.append(track)
			if data["next"] is not None:
				data = self.request(data["next"][27:])
			else:
				break
		if verbose:
			for track in answers:
				print("{2}\t{0} - {1}".format(track["artist"], track["title"], track["rank"]))
		return answers

def write(songs, filename="playlist.json"):
	def format(song):
		values = map(str, [song["added"], song["artist"], song["title"], song["rank"]])
		values = map(lambda val: val.replace("\"", "").replace("/", "").replace("\\", ""), values)
		return "[\"" + "\",\"".join(values) + "\"]"
	with open(filename, "w") as file:
		file.write("[")
		file.write(",".join(map(format, songs)))
		file.write("]")

client = Client()

songs = []
for year in range(2010, 2018):
	playlists = client.search("Top Titres France " + str(year), 1)
	if len(playlists) > 0:
		songs += client.list(playlists[0])
write(songs)
