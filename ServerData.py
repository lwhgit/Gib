class ServerData:
    
    def __init__(self, server):
        self.server = server
        self.message = None
        self.playerVolume = 0.5
        self.youtubePlayer = None
        self.youtubePlayerStopped = False
        self.youtubePlayerPaused = False
        self.youtubePlayList = []
        self.youtubePlayPosition = 0
        self.youtubeSearchList = []
        self.filePlayer = None
        self.filePlayerPlaying = False
        self.omokboard = None
        self.omokPlaying = False
        self.omokTurn = 0
        self.omokPlayers = []