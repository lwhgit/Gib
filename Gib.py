#https://discordapp.com/oauth2/authorize?client_id=<CLIENT_ID>&scope=bot

import asyncio
import discord
import time
import os
import threading
import Util
from gtts import gTTS
from Logger import Log
from ServerData import *
from BotStateData import *
from game.OmokBoard import *
from midiutil.MidiFile import MIDIFile
from midi2audio import FluidSynth

PATH = os.path.dirname(os.path.realpath(__file__))
client = discord.Client()
serverDatas = {}
state = State()

TOKEN = [
    {
        "name": "LwhTest",
        "token": "NDE3MjQ4NzM4OTIzMzgwNzM2.Dj7CeA.mIlZyfgS7htnt-5LJON7-UuyACk",
    },
    {
        "name": "Gib_beta",
        "token": "NDcyNDA2NTg1MjIyNzU4NDAx.Dj31AA.tr1iAfTuiBfNw8jGAzcc5gABfSk"
    }
]

@client.event
async def on_ready():
    global state
    
    try:
        Log.i("[" + client.user.name + "]", end="")
        Log.i(" Logged In")
        Log.line()
        Log.i("Servers:")
        for server in client.servers:
            serverDatas[server.name] = ServerData(server)
            Log.i("    [" + str(server.name) + "]")
            Log.i("        Channels:")
            try:
                for channel in server.channels:
                    if (channel.type == 4):
                        continue
                        
                    Log.i("            [" + str(channel.type) + "]")
                    if (channel.type == discord.ChannelType.voice):
                        await client.join_voice_channel(channel)
            except Exception as e:
                Log.e("Exception: " + str(e))
            
        Log.line()
        
        state.ready = True
        
        await checkPlayer()
    except Exception as e:
        Log.e("Exception: " + str(e))

@client.event
async def on_message(message):
    global serverDatas
    
    if (message.author.bot or state.ready == False):
        return
    
    data = serverDatas[message.server.name]
    data.message = message
    
    Log.i("    CHAT  |IN [" + data.server.name + "]|  ", end="")
    Log.out(str(data.message.timestamp) + "|", end="")
    Log.i(data.message.author.name + ": ", end="")
    Log.out(data.message.content)
    
    await processCommand(data)
    
@client.event
async def on_voice_state_update(before, after):
    global serverDatas
    
    if (after.bot == True):
        return
    
    try:
        if (before.voice.voice_channel == None and after.voice.voice_channel != None):
            name = after.name
            nick = after.nick
            text = ""
            if (nick == None):
                text = name + "님이 보이스 채널에 들어왔습니다."
            elif (nick != None):
                text = nick + "님이 보이스 채널에 들어왔습니다."
            
            
            await sendTTS(serverDatas[after.server.name], text)
    except Exception as e:
        Log.e("Exception: " + str(e))

async def processCommand(data):
    global state
    global serverDatas
    
    voiceClient = data.message.server.voice_client
    author_voiceChannel = data.message.author.voice_channel
    bot_voiceChannel = None
    if (voiceClient != None):
        bot_voiceChannel = voiceClient.channel
    msgContent = data.message.content
    cmd = msgContent.split(" ")
    cmdLen = len(cmd)
    
    try:
        if (cmd[0] == "집"):
            
            if (state.working == True):
                await client.send_message(data.message.channel, "다른 명령을 처리하고 있어요. 기다려 주세요.")
                return
            
            state.working = True
            
            if (cmdLen == 1):
                if (author_voiceChannel == None):
                    await client.send_message(data.message.channel, "저를 부르신 분이 보이스 채널에 있질 않아요.")
                elif (author_voiceChannel == bot_voiceChannel):
                    await client.send_message(data.message.channel, "이미 같은 보이스 채널에 있네요.")
                else:
                    if (bot_voiceChannel != None):
                        await voiceClient.disconnect()
                        
                    await client.join_voice_channel(author_voiceChannel)
            
            if (cmdLen >= 2):
                if (cmd[1] == "핑"):
                    await client.send_message(data.message.channel, "퐁")
                elif (cmd[1] == "나가"):
                    if (bot_voiceChannel == None):
                        await client.send_message(data.message.channel, "이미 보이스 채널에서 나가있었어요.")
                    else:
                        await voiceClient.disconnect()
                elif (cmd[1] == "꺼져"):
                    await client.logout()
                elif (cmd[1] == "일시정지"):
                    if (bot_voiceChannel == None or data.youtubePlayer == None or data.youtubePlayer.is_playing() == False):
                        await client.send_message(data.message.channel, "틀고 있지 않았어요.")
                    else:
                        data.youtubePlayer.pause()
                elif (cmd[1] == "정지"):
                    if (bot_voiceChannel == None or data.youtubePlayer == None or data.youtubePlayer.is_playing() == False):
                        await client.send_message(data.message.channel, "틀고 있지 않았어요.")
                    else:
                        data.youtubePlayerStopped = True
                        data.youtubePlayer.stop()
                elif (cmd[1] == "재생"):
                    if (bot_voiceChannel == None or data.youtubePlayer == None):
                        await client.send_message(data.message.channel, "틀 수 없어요.")
                    elif (data.youtubePlayer != None and data.youtubePlayer.is_playing() == True):
                        await client.send_message(data.message.channel, "이미 틀고 있었어요.")
                    else:
                        if (data.youtubePlayerStopped == True):
                            await youtubePlay(data)
                        else:
                            data.youtubePlayer.resume()
                elif (cmd[1] == "재생목록"):
                    if (cmdLen == 2):
                        count = len(data.youtubePlayList)
                        
                        if (count == 0):
                            await client.send_message(data.message.channel, "재생목록에 아무것도 없어요.")
                        else:
                            embed = genYTPlayListEmbed(data.youtubePlayList)
                            await client.send_message(data.message.channel, str(count) + "개의 목록이 있어요.", embed=embed)
                    else:
                        pos = int(cmd[2])
                        data.youtubePlayPosition = pos - 1
                        await youtubePlay(data)
                elif (cmd[1] == "다음"):
                    count = len(data.youtubePlayList)
                    if (count == 0):
                        await client.send_message(data.message.channel, "재생목록에 아무것도 없어요.")
                    else:
                        if (bot_voiceChannel == None or data.youtubePlayer == None):
                            await client.send_message(data.message.channel, "틀 수 없어요.")
                        else:
                            await youtubePlayNext(data)
                
                        
            if (cmdLen >= 3):
                if (cmd[1] == "유튜브"):
                    if (bot_voiceChannel == None):
                        await client.send_message(data.message.channel, "보이스 채널에 제가 없어요.")
                    
                    query = msgContent.split("집 유튜브 ")[1]
                    
                    msg = await client.send_message(data.message.channel, "``" + query + "`` 를 유튜브에서 검색할게요.")
                    
                    ytdata = (await Util.getYTData(query, 1))[0]
                    await client.edit_message(msg, msg.content + "\n찾았어요.")
                    embed = genYTEmbed(ytdata)
                    await client.edit_message(msg, embed=embed)
                    #await client.send_message(data.message.channel, embed=embed)
                    
                    serverDatas[data.server.name].youtubePlayList.append(ytdata)
                    
                    if (data.youtubePlayer != None and data.youtubePlayer.is_playing() == True):
                        await client.edit_message(msg, msg.content + "\n찾았어요.\n재생목록에 추가할게요.")
                        
                        embed = genYTPlayListEmbed(data.youtubePlayList)
                        await client.send_message(data.message.channel, embed=embed)
                    else:
                        await client.edit_message(msg, msg.content + "\n찾았어요.\n재생 준비가 끝나면 바로 재생할게요.")
                        await youtubePlay(data)
                        
                elif (cmd[1] == "유튜브검색"):
                    if (bot_voiceChannel == None):
                        await client.send_message(data.message.channel, "보이스 채널에 제가 없어요.")
                    
                    query = msgContent.split("집 유튜브검색 ")[1]
                    
                    msg = await client.send_message(data.message.channel, "``" + query + "`` 를 유튜브에서 검색할게요.")
                    
                    ytdataList = await Util.getYTData(query, 5)
                    await client.edit_message(msg, msg.content + "\n5개의 리스트를 찾았어요.")
                    embed = genYTListEmbed(ytdataList)
                    await client.edit_message(msg, embed=embed)
                elif (cmd[1] == "볼륨"):
                    
                    data.playerVolume = float(msgContent.split("집 볼륨 ")[1]) / 100
                    
                    if (data.youtubePlayer != None):
                        data.youtubePlayer.volume = data.playerVolume
                elif (cmd[1] == "삭제"):
                    
                    index = int(msgContent.split("집 삭제 ")[1])
                    
                    if (index >= len(data.youtubePlayList) or index < 0):
                        await client.send_message(data.message.channel, "삭제할 수 없어요.")
                    else:
                        await client.send_message(data.message.channel, data.youtubePlayList[index - 1]["title"] + "를 재생목록에서 삭제할게요.")
                        data.youtubePlayList.remove(data.youtubePlayList[(index - 1):index][0])
                        if ((index - 1) <= data.youtubePlayPosition):
                            data.youtubePlayPosition -= 1
                            
                        if (data.youtubePlayPosition < 0):
                            data.youtubePlayPosition = 0
                            
                    Log.i("Play pos: " + str(data.youtubePlayPosition))
                elif (cmd[1] == "tts"):
                    
                    text = msgContent.split("집 tts ")[1]
                    
                    if (text.replace(" ", "") == "아베마리아"):
                        await playAudio(data, PATH + "\\res\\sound\\강인_아베마리아.mp3")
                    elif (text.replace(" ", "") == "우연히"):
                        await playAudio(data, PATH + "\\res\\sound\\우연히.mp3")
                    elif (text.replace(" ", "") == "우흥"):
                        await playAudio(data, PATH + "\\res\\sound\\우흥.mp3")
                    elif (text.replace(" ", "") == "판깨잔말입니까"):
                        await playAudio(data, PATH + "\\res\\sound\\판깨잔말입니까.mp3")
                    elif (text.replace(" ", "") == "부끄러운줄알아야지"):
                        await playAudio(data, PATH + "\\res\\sound\\부끄러운줄알아야지.mp3")
                    else:
                        await sendTTS(data, text)
                    
                elif (cmd[1] == "오목"):
                    if (cmd[2] == "상태"):
                        if (data.omokPlaying == True):
                            map = OmokBoard.genString(data.omokboard.getMap())
                            embed = genOmokStateEmbed(map, data.omokPlayers[data.omokTurn])
                            await client.send_message(data.message.channel, embed=embed)
                    elif (cmd[2] == "기권"):
                        if (data.omokPlaying == True):
                            putter = data.message.author.name
                            data.omokTurn = 0
                            data.omokPlaying = False
                            await client.send_message(data.message.channel, "``" + putter + "`` 님이 기권하였습니다.")
                            await client.send_message(data.message.channel, "``Black: " + data.omokPlayers[0] + "``님과 ``White: " + data.omokPlayers[1] + "`` 님의 오목이 끝났습니다.")
                               
                elif (cmd[1] == "미디"):
                    midiString = msgContent.split("집 미디 ")[1].split(" ")
                    midi = genMidiString2MidiCode(midiString)
                    print(midi)
                    await playMidi(data, midi)
                    
                elif (cmd[1] == "노모티콘"):
                    nomoName = msgContent.split("집 노모티콘 ")[1]
                    
                    if (nomoName == "화남"):
                        await client.send_file(data.message.channel, PATH + "\\res\\nomoticon\\angry.mp4")
                    elif (nomoName == "노알라파티"):
                        await client.send_file(data.message.channel, PATH + "\\res\\nomoticon\\party.png")
                    elif (nomoName.replace(" ", "") == "흔들으라이거야"):
                        await client.send_file(data.message.channel, PATH + "\\res\\nomoticon\\shake.gif")
                    elif (nomoName == "휴식"):
                        await client.send_file(data.message.channel, PATH + "\\res\\nomoticon\\sleep.gif")
                    elif (nomoName.replace(" ", "") == "쫙스웩"):
                        await client.send_file(data.message.channel, PATH + "\\res\\nomoticon\\slide.mp4")
                    elif (nomoName.replace(" ", "") == "내리막을쫙스웩"):
                        await client.send_file(data.message.channel, PATH + "\\res\\nomoticon\\sweg.gif")
                    elif (nomoName == "답답"):
                        await client.send_file(data.message.channel, PATH + "\\res\\nomoticon\\tight.gif")
                    elif (nomoName == "왕"):
                        await client.send_file(data.message.channel, PATH + "\\res\\nomoticon\\wang.gif")
            
            if (cmdLen >= 4):
                if (cmd[1] == "오목"):
                    if (data.omokPlaying == False):
                        p_black = data.message.author.name
                        p_white = cmd[2]
                        
                        omokSize = int(cmd[3])
                        
                        data.omokboard = OmokBoard(omokSize)
                        data.omokPlayers.append(p_black)
                        data.omokPlayers.append(p_white)
                        data.omokTurn = 0
                        data.omokPlaying = True
                        await client.send_message(data.message.channel, "``Black: " + data.omokPlayers[0] + "``님과 ``White: " + data.omokPlayers[1] + "`` 님의 오목이 시작되었습니다.")
                                
                    else:
                        putter = data.message.author.name
                        
                        if (putter in data.omokPlayers == False):
                            await client.send_message(data.message.channel, putter + "님은 오목 참여자가 아니네요.")
                            
                        elif (putter == data.omokPlayers[data.omokTurn]):
                            x = int(cmd[2])
                            y = int(cmd[3])
                            
                            result = data.omokboard.putStone(x, y, data.omokTurn + 1)
                            
                            if (result == 0):
                                if (data.omokTurn == 0):
                                    data.omokTurn = 1
                                elif (data.omokTurn == 1):
                                    data.omokTurn = 0
                                    
                                
                                map = OmokBoard.genString(data.omokboard.getMap())
                                embed = genOmokStateEmbed(map, data.omokPlayers[data.omokTurn])
                                await client.send_message(data.message.channel, embed=embed)
                            elif (result == -1):
                                await client.send_message(data.message.channel, "그곳에는 둘 수 없어요.")
                            else:
                                if (result == 1):
                                    await client.send_message(data.message.channel, "``Black: " + data.omokPlayers[0] + "``님이 이겼습니다.")
                                elif (result == 2):
                                    await client.send_message(data.message.channel, "``White: " + data.omokPlayers[1] + "``님이 이겼습니다.")
                                
                                data.omokTurn = 0
                                data.omokPlaying = False
                                await client.send_message(data.message.channel, "``Black: " + data.omokPlayers[0] + "``님과 ``White: " + data.omokPlayers[1] + "`` 님의 오목이 끝났습니다.")
                                
                                
                        elif (putter != data.omokPlayers[data.omokTurn]):
                            await client.send_message(data.message.channel, putter + "님의 턴이 아니예요.")
                                
            
    except Exception as e:
        Log.e("Exception: " + str(e))
        await client.send_message(data.message.channel, "``" + msgContent + "`` 명령을 처리하다가 오류가 발생했어요.\n" +
                                                        "```오류 메세지: " + str(e) + "```")
    finally:
        state.working = False
    
async def checkPlayer():
    global serverDatas
    
    while (True):
        try:
            
            for name in serverDatas:
                #Log.i("    Server: " + name)
                #Log.i("        PlayList Count: " + str(len(serverDatas[name].youtubePlayList)))
                if (serverDatas[name].youtubePlayer != None):
                    if (serverDatas[name].youtubePlayer.is_done() and serverDatas[name].youtubePlayerStopped == False):
                        await youtubePlayNext(serverDatas[name])
                    #Log.i("        YT Player Playing: " + str(serverDatas[name].youtubePlayer.is_playing()))
                    #Log.i("        YT Player Done: " + str(serverDatas[name].youtubePlayer.is_done()))
        except Exception as e:
            Log.w("    " + str(e))
        finally:
            await asyncio.sleep(1)
    
async def youtubePlayNext(data):
    data.youtubePlayPosition += 1
    
    if (data.youtubePlayPosition == len(data.youtubePlayList)):
        data.youtubePlayPosition = 0
        
    await youtubePlay(data)
    
async def youtubePlay(data):
    if (data.youtubePlayer != None and data.youtubePlayer.is_playing() == True):
        data.youtubePlayerStopped = True
        data.youtubePlayer.stop()
        
    data.youtubePlayer = await data.message.server.voice_client.create_ytdl_player(data.youtubePlayList[data.youtubePlayPosition]["url"])
    data.youtubePlayer.volume = data.playerVolume
    data.youtubePlayer.start()
    embed = genYTEmbed(data.youtubePlayList[data.youtubePlayPosition])
    await client.send_message(data.message.channel, "현재 재생중", embed=embed)
    data.youtubePlayerStopped = False
    
def genYTEmbed(data):
    embed = discord.Embed(title=str(data["title"]) + " ``" + data["time"] + "``", description=data["url"])
    embed.set_thumbnail(url=data["img"])
    return embed
    
def genYTListEmbed(dataList):
    embed = discord.Embed()
    index = 1
    for data in dataList:
        embed.add_field(name=str(index) + "  " + data["title"] + " " + data["time"], value=data["url"])
        index += 1
    return embed
    
def genYTPlayListEmbed(playList):
    embed = discord.Embed()
    index = 1
    for data in playList:
        embed.add_field(name="``" + str(index) + "`` " + str(data["title"]) + " ``" + data["time"] + "``", value=data["url"])
        index += 1
    return embed
    
def genOmokStateEmbed(str, putter):
    embed = discord.Embed(title=putter + "님의 턴", description="``" + str + "``")
    return embed
    
async def sendTTS(data, text):
    try:
        dir = PATH + "\\res\\" + data.server.name
        if (os.path.isdir(dir) == False):
            os.mkdir(dir)
        
        tts = gTTS(text=text, lang="ko")
        tts.save(dir + "\\tts.mp3")
        
        if (data.youtubePlayer != None and data.youtubePlayer.is_playing() == True):
            data.youtubePlayer.pause()
            data.youtubePlayerPaused = True
            
        while (data.filePlayer != None and data.filePlayer.is_playing() == True):
            await asyncio.sleep(1)
            
        voiceClient = None
        
        if (data.message != None):
            voiceClient = data.message.server.voice_client
        elif (data.message == None):
            voiceClient = data.server.voice_client
            
        if (data.youtubePlayerPaused == True):
            data.filePlayer = voiceClient.create_ffmpeg_player(dir + "\\tts.mp3", after= (lambda:
                    resumePausedYTPlayer(data)
                )
            )
        else:
            data.filePlayer = voiceClient.create_ffmpeg_player(dir + "\\tts.mp3")
            
        data.filePlayer.start()
    except Exception as e:
        Log.e("Exceptoion: " + str(e))
    
def resumePausedYTPlayer(data):
    data.youtubePlayer.resume()
    data.youtubePlayerPaused = False
    
def genMidiString2MidiCode(arr):
    list = []
    for str in arr:
        pitch = 60
        
        for s in str:
            if (s == "+"):
                pitch += 12
            elif (s == "-"):
                pitch -= 12
            elif (s == "레"):
                pitch += 2
            elif (s == "미"):
                pitch += 4
            elif (s == "파"):
                pitch += 5
            elif (s == "솔"):
                pitch += 7
            elif (s == "라"):
                pitch += 9
            elif (s == "시"):
                pitch += 11
            elif (s == "#"):
                pitch += 1
            elif (s == "p"):
                pitch -= 1
                
        list.append(pitch)
    return list
            
async def playMidi(data, arr):
    dir = PATH + "\\res\\" + data.server.name
    
    mf = MIDIFile(1)
    mf.addTrackName(0, 0, "Sample Track")
    mf.addTempo(0, 0, 120)
    
    for i in range(0, len(arr)):
        mf.addNote(0, 0, arr[i], i, 1, 100)
    
    with open(dir + "\\midi.mid", 'wb') as outf:
        mf.writeFile(outf)
        
    await client.send_file(data.message.channel, dir + "\\midi.mid")
        
    #FluidSynth().midi_to_audio(PATH + "\\res\\" + data.server.name + "\\midi.mid", PATH + "\\res\\" + data.server.name + "\\midi.wav")
    '''
    if (data.youtubePlayer != None and data.youtubePlayer.is_playing() == True):
        data.youtubePlayer.pause()
        data.youtubePlayerPaused = True
        
    while (data.filePlayer != None and data.filePlayer.is_playing() == True):
        await asyncio.sleep(1)
        
    if (data.youtubePlayerPaused == True):
        data.filePlayer = data.message.server.voice_client.create_ffmpeg_player(PATH + "\\res\\" + data.server.name + "\\midi.mid", after= (lambda:
                resumePausedYTPlayer(data)
            )
        )
    else:
        data.filePlayer = data.message.server.voice_client.create_ffmpeg_player(PATH + "\\res\\" + data.server.name + "\\midi.mid")
        
    data.filePlayer.start()'''
    
async def playAudio(data, file):
    if (data.youtubePlayer != None and data.youtubePlayer.is_playing() == True):
        data.youtubePlayer.pause()
        data.youtubePlayerPaused = True
        
    while (data.filePlayer != None and data.filePlayer.is_playing() == True):
        await asyncio.sleep(1)
        
    if (data.youtubePlayerPaused == True):
        data.filePlayer = data.message.server.voice_client.create_ffmpeg_player(file, after= (lambda:
                resumePausedYTPlayer(data)
            )
        )
    else:
        data.filePlayer = data.message.server.voice_client.create_ffmpeg_player(file)
        
    data.filePlayer.start()
    
def login(index):
    Log.line()
    Log.i("Bot : " + TOKEN[index]["name"])
    Log.i("Try to login.")
    client.run(TOKEN[index]["token"])