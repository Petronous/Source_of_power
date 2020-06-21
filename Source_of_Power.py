import pickle
import os.path
import pyglet
from weakref import ref
from pyglet import gl
from random import randint as rand
import packages.player as player
#I try to use '' for single characters and "" for strings, but in the end it's somewhat random
class MapHex:
    def FindMatch(self, index = None):
        re = False
        while not(re):
            y = -1
            x = -1

            if index is None: index = rand(0, self.tileNum-1)
            oriIndex = index

            for a,i in enumerate(self.tiles):
                if index >= i: index -= i
                else:
                    x,y = (self.boundaries[a][0] + index, a)
                    break
            re = True
            if y == -1: print("NO Y FOUND", oriIndex)
            if x == -1: print("NO X FOUND", oriIndex)
            if x in self.bases[y]:
                    re = False
                    index = None
        if re: return x,y


    def DrawTiles(self, tileSize, tileYSize, camX, camY, builgingImages):
        global diffX, diffY


        for a,row in enumerate(self.tileSprites):
            for b,sprite in enumerate(row):
                x = b + Map.boundaries[a][0]
                sprite.x = x*tileSize + camX
                sprite.y = int(a*tileSize*tileYSize + camY)
                plid = -1
                baseThere = False
                if x in Map.bases[a]:
                    plid = Map.bases[a][x][1]
                    baseThere = True
                    if plid > -1:
                        sprite.color = Map.players[plid].color
                    else:
                        sprite.color = (255,255,255)
                for pl in Map.players.values():
                    if x in pl.units[a]:
                        if baseThere and plid != pl.ID: pl.units[a][x].sprite.color = pl.color
                        else: sprite.color = pl.color
                        break


        for a,i in enumerate(self.bases):
            for base in i.values():
                base[3].x = base[0]*tileSize + camX
                if base[2] == 'p': base[3].x += 0.12*tileSize
                base[3].y = int((a+0.12)*tileSize*tileYSize + camY)
                if len(base) > 4:
                    base[4].x = (base[0]+0.05)*tileSize + camX
                    base[4].y = int((a+0.12)*tileSize*tileYSize + camY)

        for pl in self.players.values():
            for y,row in enumerate(pl.units):
                    for unit in row.values():
                        unit.sprite.x = unit.pos[0]*tileSize + tileSize//2 + camX
                        unit.sprite.y = int(((y+0.12)*tileSize)*tileYSize + camY)
                        if unit.movePoints == 0 and pl.ID == self.playerActive: unit.sprite.opacity = 150
                        else: unit.sprite.opacity = 255
                        if unit.new and pl.ID != Map.playerActive: unit.sprite.opacity = 0


    def NewUnit(self, UType, x,y, plID, upped = False, hp = None, movePoints = None, dmg = None,orders = None, new = True, save = True):
        global unitImages, mapButtons, tileSize, UIBatch

        u = self.unitTypes[UType]
        U = [[x,y]]
        U.extend(u)
        U[6] = unitImages[U[6]]
        if hp is None:hp = U[1]
        if movePoints is None:movePoints = U[4]
        if dmg is not None:U[5] = dmg
        if orders == None: orders = []

        print(orders, "ORDERS")
        unit = player.Unit(U, hp, movePoints, orders, new)
        print(unit, "NEW UNIT")
        unit.sprite.batch = UIBatch
        unit.sprite.scale = tileSize/100

        if upped:
            unit.hp    *= 2
            unit.damage*= 2
        if save:
            self.players[plID].units[y][x] = unit
            mapButtons[plID]['units'][y][x] = ('unit', (y,x))
            print(mapButtons[plID]['units'])
        if new and save:
            print("INITING THE START TILE")
            unit.orders.append((unit.pos, 'move'))
            timeStep = 1/(unit.startMP + 1)
            plIDs = [pp for pp in self.players]
            pl = self.players[plID]
            x,y = unit.pos
            if x in self.tilesUsed[y]:
                for a,p in self.tilesUsed[y][x][0].items():
                    if a != plID:
                        for uu in p:
                            xx,yy = uu[0]
                            del self.players[a].units[yy][xx].orders[uu[1]:]
                        p = []
            self.tilesUsed = unit.MakeRequests([unit.pos], pl.ID, self.tilesUsed, plIDs)
        return unit

    def DelUnit(self, x,y, plID):
        global mapButton
        print("DELETE UNIT AT", x,y)
        self.players[plID].units[y][x].sprite.delete()
        self.tilesUsed = self.players[plID].units[y][x].CancelRequests(self.tilesUsed, plID)
        print(self.tilesUsed)
        del self.players[plID].units[y][x]
        del mapButtons[plID]['units'][y][x]

    def NewBuilding(self, x,y, plID, type):
        self.bases[y][x] = [x, plID, type]
        if type == 's': self.sourceNum += 1
        if type == 'u': self.upNum +=1

    def DelBuilding(self, x,y, decreaseNum = True):
        base = self.bases[y][x]
        type = base[2]
        if type == 's': self.sourceNum -= 1
        if decreaseNum and type == 'u': self.upNum -= 1
        if len(base) >= 4 and base[3] is not None: base[3].delete()
        del self.bases[y][x]

    def NewBase(self, x,y, plID):
        global buildingImages, tileSize, camX, camY, UIBatch
        self.bases[y][x][1] = plID
        print("MAKING NEW BASE \n       NEW BASE")
        if len(self.bases[y][x]) < 5 and self.bases[y][x][2] != 'p':
            self.bases[y][x].append(pyglet.sprite.Sprite(buildingImages['p'], x = x*tileSize + camX,
                                                         y = y*tileSize + camX, batch = UIBatch))
            self.bases[y][x][4].scale = tileSize/100
            gl.glTexParameteri(self.bases[y][x][4]._texture.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
            gl.glTexParameteri(self.bases[y][x][4]._texture.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
            print("ADD NEW SPRITE")
        if plID != -1: self.players[plID].bases.append((x,y, self.bases[y][x][2]))

    def DelBase(self, x,y, plID):
        base = self.bases[y][x]
        baType = base[2]
        base[1] = -1
        if len(base) > 4:
            base[4].delete()
            base.pop(4)
        if (x,y,baType) in self.players[plID].bases: self.players[plID].bases.remove((x,y,baType))
        else:
            print("NO BASE FOUND NO BASE FOUND ######################################")

    def OnBase(self, x,y, plID):
        return (x in self.bases[y] and self.bases[y][x][1] == plID)

    def Win(self, plID):
        self.playerHere   = False
        self.winningPlayer= plID
        self.game         = False

    def DelPlayer(self, plID, redoIDs = False):
        pl = self.players[plID]
        for row in pl.units:
            for unit in row.values():
                for order in unit.orders:
                    pos = order[0]
                    if order[1] == 'move': type = 0
                    else: type = 1
                    result = player.PosIndex(pos, plID, unit.pos, self.tilesUsed, type = type)
                    if result[1]:
                        del self.tilesUsed[pos[0]][pos[1]][type][plID][result[0]]
        for base in pl.bases:
            x,y = base[:2]
            self.bases[y][x][1] = -1

            x -= Map.boundaries[y][0]
            x = int(x)
            self.tileSprites[y][x].color = (255,255,255)
        del self.players[plID]

        if redoIDs: self.RedoIDs()
        elif plID == self.maxPlID:
            newMax = 0
            for i in self.players:
                if i > newMax and i != plID: newMax = i
            self.maxPlID = newMax


    def NewPlayer(self, x,y, ID = None, upPlNum = False):
        if ID is None:
            ID = 0
            while ID in self.players: ID += 1
        self.NewBuilding(x,y, ID, 'p')
        units = []
        for i in range(0, len(self.boundaries)):
            units.append({})
        #resUn = []
        #for i in self.unitTypes:
        #    resUn.append(i)
        if upPlNum: self.playerNum += 1
        self.players[ID] = player.Player(ID, [(x,y, 'p')], [6]*len(self.unitTypes), (rand(80,255),rand(80,255),rand(80,255)), units)

    def RedoIDs(self):
        newMax = len(self.players)-1
        na = 0
        np = {}
        idPairs = {}
        for a,i in sorted(list(self.players.items())):
            idPairs[a] = na
            i.ID = na
            np[na] = i
            na += 1
        self.UpdateBaseIDs(idPairs)
        self.players = np
        self.maxPlID = newMax

    def UpdateBaseIDs(self, idPairs):
        for row in self.bases:
            for base in row.values():
                try:
                    if base[1] in idPairs: base[1] = idPairs[base[1]]
                except TypeError:
                    print('ERROR OF TYPE')
                    print(base)
                    print(row)
                    print(idPairs)
                    pyglet.app.exit()

    def UpdateTilesUsedIDs(self, idPairs):
        for row in self.tilesUsed:
            for tile in row.values():
                for mode in tile:
                    nps = {}
                    for id, player in list(mode.items()):
                        nps[idPairs[id]] = player
                    mode = nps


    #deathCondition = "noUnits"||"noBases||noHomeBase"
    #winCondition   = "totalDomination"||"allBases"||"allSources||allHomeBases"
    def __init__(self, a,b,c, sourceNum, playerNum, upNum, tilesUsed = [], deathCondition = "noUnits", winCondition = "allBases", generate = True):
        self.sides = a,b,c
        #c -=1
        b -=1
        self.deathCondition = deathCondition
        self.winCondition  = winCondition
        self.winningPlayer = None
        self.tilesUsed    = tilesUsed
        self.boundaries  = []
        self.bases       = []
        self.turnNum     = 0
        self.playerActive= 0
        self.players     = {}
        self.playerHere  = True
        self.game        = True
        self.XSize       = 0
        self.YSize       = 0
        self.tileSprites = []
        #startHp, airDrop, Range, startMP, dmg, img,  index
        self.unitTypes= [[1, True, 1, 2, 1, 0,  0], [1, False, 2, 1, 1, 1,  1], [3, False, 1, 1, 1, 2,  2]]
        left          = b/2
        right         = b/2 + a-1
        self.tileNum  = a
        self.tiles    = []
        self.prevOrders = []
        self.maxPlID  = playerNum
        for i in range(b+c):
            self.boundaries.append((left, right))
            self.tiles.append(int(self.tileNum))
            if i < b:
                left    -= 0.5
                self.tileNum += 0.5
            else:
                left    += 0.5
                self.tileNum -= 0.5
            if i < c-1:
                right   += 0.5
                self.tileNum += 0.5
            else:
                right   -= 0.5
                self.tileNum -= 0.5
        print(self.boundaries)
        self.tileNum = sum(self.tiles)
        print(self.tileNum, self.tiles)


        for i in self.tiles: self.bases.append({})

        playerNum = min(self.tileNum, playerNum)
        self.playerNum = playerNum
        sourceNum = min(self.tileNum - playerNum, sourceNum)
        self.sourceNum = sourceNum
        upNum = min(self.tileNum - playerNum - sourceNum, upNum)
        self.upNum = upNum
        if generate:
            for i in self.boundaries:
                tilesUsed.append({})

            for pl in range(0, playerNum):
                x,y = self.FindMatch()
                self.NewPlayer(x,y, ID = pl)

            for i in range(0, sourceNum):
                x,y = self.FindMatch()
                self.bases[y][x] = [x, -1, 's']

            for i in range(0, upNum):
                x,y = self.FindMatch()
                self.bases[y][x] = [x, -1, 'u']

        #for i in self.bases: print(i, 'BASES')

############################################################################x#########################
def Frange(start, stop, step = 1):
     i = start
     while i < stop:
         yield i
         i += step
######################################################################################################
#def len2d(list2d):
#    x = 0
#    for i in list2d:
#        for a in i:
#            x += 1
#    return x

def update(dt):
    pass
#if __name__ == "__main__":
pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)

tileSize = 100
tileYSize = 0.75


# a,b,c sources, players, upgrades
Map = MapHex(5,3,3, 3, 2, 0)

#platform = pyglet.window.get_platform()
display = pyglet.canvas.get_display()
screen = display.get_default_screen()
Map.XSize = screen.width
Map.YSize = screen.height - 0.5*tileSize
print('SIZES', Map.XSize, Map.YSize)

window = pyglet.window.Window(resizable = True, caption='Source of Power')
window.config.alpha_size = 8
window.activate()
window.maximize()
print(window.config.alpha_size)

camX = int(0.5 * tileSize)
camY = int(0.5 * tileSize)

batch = pyglet.graphics.Batch()
UIBatch = pyglet.graphics.Batch()
tileBatch = pyglet.graphics.Batch()

#Assign sprites to buildings
#Assign sprites to tiles
pyglet.resource.path = ['assets']
buildingImages = {'s': pyglet.resource.image('Nuclear.png'), 'p': pyglet.resource.image('Base.png'), 'u': pyglet.resource.image('Upgrade.png')}
buildingImages['s'].anchor_x = -15
buildingImages['u'].anchor_x = -32
buildingImages['u'].anchor_y = 0
tileImage = pyglet.resource.image('Tile-hex.png')
tileImage.anchor_y = 12.5

def MakeBaseSprite(xx,yy):
    global buildingImages, UIBatch, tileImage, tileBatch, Map
    base = Map.bases[yy][xx]
    x = xx*tileSize + camX
    y = yy*tileYSize + camY
    base.append(pyglet.sprite.Sprite(buildingImages[base[2]], x=x, y=y, batch = batch))
    gl.glTexParameteri(base[3]._texture.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    gl.glTexParameteri(base[3]._texture.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
    if base[2] == 's':
        sc = tileSize/128
    elif base[2] == 'u':
        sc = tileSize/100 * 0.70
    else: sc = tileSize/100
    base[3].scale = sc
    if (base[1] > -1) and (base[2] != 'p'):
        base.append(pyglet.sprite.Sprite(buildingImages['p'], x=x, y=y, batch = UIBatch))
        base[4].scale = tileSize/100


def MakeBaseSprites(tileSprites = None):
    for y,i in enumerate(Map.bases):
        for x in i: MakeBaseSprite(x,y)

    for a,row in enumerate(Map.boundaries):
        Map.tileSprites.append([])
        for i in Frange(row[0], row[1]+1):
            x = i*tileSize + camX
            y = a*tileSize*tileYSize + camY
            sprite = pyglet.sprite.Sprite(tileImage, x=x,y=y, batch = tileBatch)
            sprite.scale_y = tileYSize+0.25
            if tileSprites is not None:
                sprite.color = tileSprites[a][int(i-row[0])]
            Map.tileSprites[a].append(sprite)


MakeBaseSprites()

unitImages = [pyglet.resource.image('Soldier.png'), pyglet.resource.image('Artillery.png'), pyglet.resource.image('Tank.png')]
playerColorSprite = pyglet.sprite.Sprite(tileImage, x=0,y=0, batch = UIBatch)

change = True
zoom   = True
frame  = 0
zframe = 0
menuSprites = {'normMenu': {}, 'gameSetup': {}}
menuButtons = {'normMenu': {}, 'gameSetup': {}}
mapButtons  = {}
buttonID    = -1
mapButtonID = -1
bType       = None
baseType    = 's'
showPrevOrders = True

unitTypeSelected = None
unitSelected= [None, 'move']
upgrade = False

diffX = 0
diffY = 0

cursors = {
    "Default": window.get_system_mouse_cursor(window.CURSOR_DEFAULT),
    "building": window.get_system_mouse_cursor(window.CURSOR_DEFAULT),
    "tile": window.get_system_mouse_cursor(window.CURSOR_DEFAULT),
    "otherUnits": window.get_system_mouse_cursor(window.CURSOR_DEFAULT),
    "menu": window.get_system_mouse_cursor(window.CURSOR_HAND),
    "mapS": window.get_system_mouse_cursor(window.CURSOR_HAND),
    "bases": window.get_system_mouse_cursor(window.CURSOR_SIZE_DOWN),
    "units": window.get_system_mouse_cursor(window.CURSOR_SIZE),
    "moves": window.get_system_mouse_cursor(window.CURSOR_CROSSHAIR)
}

######################################################################################################



#-------------------------------------------FUNCTIONS------------------------------------------------#
######################################################################################################

def DrawUI(height, width): #---------------------------------------------------------> DRAW_UI BEGINS
    global showPrevOrders, UIBatch, menuSprites, menuButtons, mapButtons, unitTypeSelected, unitSelected, tileSize, upgrade, playerColorSprite, mapButtonID
    if mapButtonID != -1: bType = mapButtonID[2]
    shapesBatch = pyglet.graphics.Batch()
    shapesBatch.add(4, pyglet.gl.GL_QUADS, None,
                        ("v2i", (int(width*0.8),0, int(width*0.8),height, width,height, width,0)),
                        ("c3B", (100,100,100)*4)
                    )

    y = int(height * 0.9)
    plA = Map.players[Map.playerActive]
    #normMenu
    if menuSprites['normMenu'] == {}:
        first = True
        for a,i in enumerate(Map.unitTypes):
            menuSprites['normMenu'][a*2] = pyglet.text.Label(str(plA.ResUnByType[a]), "Arial.ttf", 25.0, x = int(width*0.81) + 50, y = y, batch = UIBatch)
            menuSprites['normMenu'][a*2 + 1] = pyglet.sprite.Sprite(unitImages[i[5]], x = int(width*0.81), y=y-5, batch = UIBatch)
            menuButtons['normMenu'][a] = (int(width*0.81), y-5,  int(width*0.81) + 50, y+45)
            y -= 50

        UPL = pyglet.text.Label("Upgrades: " + str(Map.players[Map.playerActive].resupgrades), "Arial.ttf",
                                18.0, x = int(width*0.81), y = int(height*0.1) + 150, color = (200,255,255,255), batch = UIBatch)
        menuSprites['normMenu']['UPL'] = UPL
        menuButtons['normMenu']['UPL'] = (UPL.x,UPL.y, UPL.x + UPL.content_width,UPL.y + UPL.content_height)
        TNL = pyglet.text.Label("Turn number: " + str(Map.turnNum), "Arial.ttf",
                                18.0, x = int(width*0.81), y = int(height*0.1) + 100, batch = UIBatch)
        menuSprites['normMenu']['TNL'] = TNL
        APL = pyglet.text.Label("Active Player: " + str(Map.playerActive), "Arial.ttf",
                                18.0, x = int(width*0.81), y = int(height*0.1) +  50, batch = UIBatch)
        menuSprites['normMenu']['APL'] = APL
        NPL = pyglet.text.Label("Next Player", "Arial.ttf",
                                25.0, x = int(width*0.81), y = int(height*0.1), batch = UIBatch)
        menuSprites['normMenu']['NPL'] = NPL
        menuButtons['normMenu']['NPL'] = (NPL.x,NPL.y, NPL.x + NPL.content_width,NPL.y + NPL.content_height)
        print(menuSprites)
    else:
        first = False
        for a,i in enumerate(Map.unitTypes):
            menuSprites['normMenu'][a*2].text = str(plA.ResUnByType[a])
            menuSprites['normMenu'][a*2].x = int(width*0.81) +50
            menuSprites['normMenu'][a*2].y = y
            menuSprites['normMenu'][a*2+1].x = int(width*0.81)
            menuSprites['normMenu'][a*2+1].y=y-5
            menuButtons['normMenu'][a] = (int(width*0.81), y-5,  int(width*0.81) + 50, y+45)
            y -= 50

        menuSprites['normMenu']['UPL'].x = int(width*0.81)
        menuSprites['normMenu']['UPL'].y = int(height*0.1) + 150
        menuSprites['normMenu']['UPL'].text = "Upgrades: " + str(Map.players[Map.playerActive].resupgrades)
        UPL = menuSprites['normMenu']['UPL']
        menuButtons['normMenu']['UPL'] = (UPL.x,UPL.y, UPL.x + UPL.content_width,UPL.y + UPL.content_height)

        menuSprites['normMenu']['TNL'].x = int(width*0.81)
        menuSprites['normMenu']['TNL'].y = int(height*0.1) + 100
        menuSprites['normMenu']['TNL'].text = "Turn Number: " + str(Map.turnNum)

        menuSprites['normMenu']['APL'].x = int(width*0.81)
        menuSprites['normMenu']['APL'].y = int(height*0.1) + 50
        menuSprites['normMenu']['APL'].text = "Active Player: " + str(Map.playerActive)

        menuSprites['normMenu']['NPL'].x = int(width*0.81)
        menuSprites['normMenu']['NPL'].y = int(height*0.1)
        NPL = menuSprites['normMenu']['NPL']
        menuButtons['normMenu']['NPL'] = (NPL.x,NPL.y, NPL.x + NPL.content_width,NPL.y + NPL.content_height)

    #gameSetup
    if first:
        NML = pyglet.text.Label("Regenerate Map", "Arial.ttf",
                                18.0, x = int(width*0.01), y = int(height*0.95), color = (200,255,255,255), batch = UIBatch)
        menuSprites['gameSetup']['NML'] = NML
        menuButtons['gameSetup']['NML'] = (NML.x,NML.y, NML.x + NML.content_width,NML.y + NML.content_height)

        LAL = pyglet.text.Label("Load autosave", "Arial.ttf",
                                18.0, x = int(width*0.01), y = int(height*0.95)-30, color = (200,255,255,255), batch = UIBatch)
        menuSprites['gameSetup']['LAL'] = LAL
        menuButtons['gameSetup']['LAL'] = (LAL.x,LAL.y, LAL.x + LAL.content_width,LAL.y + LAL.content_height)
    else:
        menuSprites['gameSetup']['NML'].x = int(width*0.01)
        menuSprites['gameSetup']['NML'].y = int(height*0.95)
        NML = menuSprites['gameSetup']['NML']
        menuButtons['gameSetup']['NML'] = (NML.x,NML.y, NML.x + NML.content_width,NML.y + NML.content_height)

        menuSprites['gameSetup']['LAL'].x = int(width*0.01)
        menuSprites['gameSetup']['LAL'].y = int(height*0.95)-30
        LAL = menuSprites['gameSetup']['LAL']
        menuButtons['gameSetup']['LAL'] = (LAL.x,LAL.y, LAL.x + LAL.content_width,LAL.y + LAL.content_height)

    x0 = int(width*0.81)
    y0 = int(height*0.1) + 180
    #Update y0 if the bottom UI block changes
    x1 = int(width*0.99)
    y1 = int(height * 0.9) - len(Map.unitTypes)*50 + 43
    scale = min(x1-x0, y1-y0)/100
    playerColorSprite.update(x0, int((y0 + y1)/2 - scale*37.5), scale = scale)
    playerColorSprite.color = plA.color

    #HP bars
    for pl in Map.players.values():
        for row in pl.units:
            for unit in row.values():
                if not(unit.new) or pl.ID == Map.playerActive:
                    x = int(unit.pos[0]*tileSize + camX)
                    y = int(unit.pos[1]*tileSize*tileYSize + camY + (tileSize-15)*tileYSize)
                    x+=1
                    '''shapesBatch.add(4, pyglet.gl.GL_QUADS, None,
                                ("v2i", (x,y, x,y-tileSize//5, x+tileSize//5,y-tileSize//5, x+tileSize//5, y)),
                                ("c3B", (pl.color)*4))'''
                    x += tileSize//2 -1
                    if unit.hp > unit.startHp:
                        upp = True
                        bars  = unit.startHp*2
                    else:
                        upp = False
                        bars = unit.startHp
                    nowCol= [255, 0, 0]
                    colors= []
                    step  = tileSize//bars//2
                    verts = []
                    lng = int(unit.hp)
                    colors.extend(nowCol*4)
                    verts.extend((x,y, x,y-3, x+step,y-3, x+step,y))
                    x += step
                    # if upp:
                    #     nowCol[0] -= 255//(max(1, bars//2 - 1))
                    #     nowCol[1] += 255//(max(1, bars//2 - 1))
                    for i in range(1,int(unit.hp)):
                        if upp:
                            if i < unit.startHp:
                                nowCol[0] -= 255//(max(1, bars//2 - 1))
                                nowCol[1] += 255//(max(1, bars//2 - 1))
                                #print("FIRST PART OF COLORING", nowCol)
                            else:
                                nowCol[0] = 0
                                if nowCol[1] < 1:nowCol[1] = 255
                                nowCol[1] -= 255//bars
                                nowCol[2] += 255//bars * 2
                                #print("SECOND PART OF COLORING", nowCol)
                        else:
                            nowCol[0] -= 255//max(1, bars - 1)
                            nowCol[1] += 255//max(1, bars - 1)
                            #print("NORMAL COLORING", nowCol)
                        colors.extend(nowCol*4)
                        verts.extend((x,y, x,y-3, x+step,y-3, x+step,y))
                        x += step

                    if int(unit.hp) != unit.hp:
                        colors.extend(nowCol*4)
                        step = tileSize//bars//4
                        verts.extend((x,y, x,y-3, x+step,y-3, x+step,y))
                        lng = int(unit.hp)+1

                    shapesBatch.add(4*lng, pyglet.gl.GL_QUADS, None,
                               ("v2i", verts),    ("c3B", colors))

    #tilesUsedHighlight
    if True:
        '''for y,row in enumerate(Map.tilesUsed):
            for x,tile in row.items():
                #print(tile, "TILE TO BE DRAWN")
                for a, pl in tile[0].items():
                    if len(pl) > 0:
                        shapesBatch.add(1, pyglet.gl.GL_POINTS, None,
                            ("v2i", (int(x*tileSize) + camX + a, int(y*tileSize*tileYSize) + camY)),
                            ("c3B", Map.players[a].color))
                    for unit in pl:
                        tempLabel = pyglet.text.Label(str(tile[0]), "Arial.ttf", 10.0,
                                    x = x*tileSize + camX, y = y*tileSize*tileYSize + camY,
                                    color = (255,255,255, 255), batch = None)
                        tempLabel.draw()'''


    #init mapButtons, unitSelected, UPL, draw orders
    if Map.turnNum == 0:
        pass
    else:
        if len(mapButtons) < 2:
            print("INITING MAPBUTTONS")
            mapButtons = InitMapButtons()

        if unitTypeSelected is not None:
            y = int(height * 0.9) - unitTypeSelected*50 - 5
            x = int(width*0.81)
            shapesBatch.add(4, pyglet.gl.GL_LINE_LOOP, None,
                            ("v2i", (x,y, x,y+50, x+50,y+50, x+50,y)),
                            ("c3B", (255,255,255)*4)
                            )

        if unitSelected[0] is not None:
            (x,y),mType = unitSelected
            unit = plA.units[y][x]
            if unit.orders != [] and unit.orders[len(unit.orders)-1][1] == 'move':
                x,y = unit.orders[len(unit.orders)-1][0]
            shapesBatch = MakeAvaibleTiles(x,y,mType, shapesBatch)

        UPL = menuSprites['normMenu']['UPL']
        if upgrade: UPL.size = 22.0
        else: UPL.size = 18.0

        #draw orders
        for row in plA.units:
            for unit in row.values():
                if unit.orders != []:
                    width = 2
                    x,y = unit.pos
                    if bType == 'units':
                        x1,y1 = mapButtonID[0:2]
                        if (x,y) == (x1,y1): width = 4
                    DrawOrders(unit.orders, width, (100,255,200), (255,100,100))

        #draw previous orders
        if showPrevOrders:
            for unit in Map.prevOrders:
                width = 2
                x,y = unit[0][0]
                if bType == 'units' or bType == 'otherUnits':
                    x1,y1 = mapButtonID[0:2]
                    if (x,y) == (x1,y1): width = 4
                DrawOrders(unit[:len(unit)-1], width, (150,150,255), (200,75,75), offset = (0.25, -0.1), markers = True, alive = unit[len(unit)-1])

    return shapesBatch
#  _______
# /      /                                                                            / / /
#<------<---------------------------------------------------------------------------<-<-< DRAW_UI ENDS
# \______\                                                                            \ \ \

def DrawOrders(orders, width, moveColor, attackColor, offset = (0,0), markers = False, alive = True):
    verts = []
    indices = []
    colors = []
    for a,i in enumerate(orders):
        x,y = i[0]
        verts.extend((int((x+0.5+offset[0])*tileSize) + camX, int((y+0.5+offset[1])*tileSize*tileYSize) + camY))
        if i[1] == 'move': colors.extend((moveColor))
        else: colors.extend((attackColor))
        if a < len(orders) - 1 and a > 0: indices.extend((a,a))
        else: indices.append(a)

    if markers:
        #draw start pos
        x,y = orders[0][0]
        verts.extend((int((x+0.5+offset[0])*tileSize) + camX, int((y+0.5+offset[1])*tileSize*tileYSize) + camY))
        colors.extend((100,255,100))
        indices.extend((a+1,a+1))

        #draw end pos if dead
        if not alive:
            index = len(orders)-1
            if orders[index][1] == 'attack': index -= 1
            x,y = orders[index][0]
            verts.extend((int((x+0.5+offset[0])*tileSize) + camX, int((y+0.5+offset[1])*tileSize*tileYSize) + camY))
            colors.extend((255,100,100))
            indices.extend((a+2,a+2))

    # print(indices, 'INDEXS')
    # print(verts, 'VERTEXS')
    # print(len(unit.orders)+1, 'LEN')
    gl.glLineWidth(width)
    pyglet.graphics.draw_indexed(len(verts)//2, pyglet.gl.GL_LINES,
                                 indices, ("v2i", verts), ("c3B", colors))
    gl.glLineWidth(1)

#------------------------------------------------------------------------------------> END_TURN BEGINS
def EndTurn():
    global mapButtons
    # tile = unitPos, orderIndex, times

    print("\n\n\n --- NEW TURN ---")

    #Processing the orders
    #Requesting the tiles
    Map.prevOrders = []
    for pl in Map.players.values():
        for row in pl.units:
            for unit in row.values():
                print()
                print(unit.pos,  "UNIT POSITION")
                print(unit.damage, "UNIT DAMAGE")
                unit.sprite.color = (255,255,255)

                tile = Map.tilesUsed[unit.pos[1]][unit.pos[0]][0][pl.ID]
                print(tile, "THE TILE OF MY PLAYER")
                if len(tile) == 0 or tile[0][0] != unit.pos:
                    tile.insert(0, [unit.pos, 0, [0,0]])

                ordersToDel = []
                for a,order in enumerate(unit.orders):
                    if len(order) > 2:
                        ordersToDel.append(a)
                for a in ordersToDel:
                    print("-------------------Cancelling order number", a)
                    unit.CancelRequests(Map.tilesUsed, pl.ID, index = a)
                    del unit.orders[a]

                time = 0
                timeStep = 1/(unit.startMP + 1)
                x,y = unit.pos
                ordersLen = len(unit.orders)
                if unit.orders[ordersLen-1][1] == 'move': index = ordersLen-1
                else:                                     index = ordersLen-2

                '''if unit.airDrop and x in Map.bases[y] and Map.bases[y][x][1] == pl.ID:
                    plIDs = [pp for pp in Map.players]
                    ox,oy = unit.orders[index][0]
                    Map.tilesUsed = unit.MakeRequests([(ox,oy)], pl.ID, Map.tilesUsed, plIDs)'''

                tx, ty = unit.orders[index][0]
                tile = Map.tilesUsed[ty][tx][0][pl.ID]
                #set last time to much
                for request in tile:
                    if request[0] == unit.pos:
                        request[2][1] = 'end'
                        break
                Map.tilesUsed[ty][tx][0][pl.ID] = tile

    for row in Map.tilesUsed: print(row, "ROW OF TILES_USED")

    #Executing orders
    print("#######################################################################\nPHASE ORDERS")
    for pl in Map.players.values():
        for row in pl.units:
            for unit in row.values():
                print("\n\n-----------------------------------------------------------------------\nUNIT FROM TILE", unit.pos, "AND PLAYER", pl.ID)
                x,y = unit.pos
                #print(onBase, pl.ID)
                Map.tilesUsed, ordersToDel, moveUnits = unit.DoOrders(Map.players,
                                            Map.tilesUsed,
                                            pl.ID,
                                            Map.OnBase(x,y, pl.ID))
                #print(ordersToDel)
                for i in ordersToDel:
                    (x,y), oI, plID = i
                    print("DELETE ORDERS OF UNIT AT", x, y, "STARTING AT INDEX", oI, "OF PLAYER", plID)
                    del Map.players[plID].units[y][x].orders[oI:]
                #print(moveUnits)
                for i in moveUnits:
                    unit = Map.players[i[2]].units[i[0][1]][i[0][0]]
                    unit.nowPos = unit.orders[i[1]][0]

    #Finishing everything + checking for health and upgrades
    print("#######################################################################\nPHASE FINISH")
    newTilesUsed = []
    for i in Map.boundaries: newTilesUsed.append({})
    newPls = {}
    for pl in Map.players.values():
        newUnits = []
        for row in pl.units:
            newUnits.append(row.copy())
        for row in pl.units:
            for unit in row.values():
                print()
                print("\n\n-----------------------------------------------------------------------\nUNIT FROM TILE", unit.pos, "AND PLAYER", pl.ID)
                print(Map.tilesUsed, "TILES USED - CHECKING ATTACKERS")
                for index,((x,y),type) in enumerate(unit.orders):
                    print(x,y, "ORDER POSITION")
                    if type == 'move' and x in Map.tilesUsed[y]:
                        print("ATTACKERS OF THIS TILE", Map.tilesUsed[y][x][1].items())
                        for a,playa in Map.tilesUsed[y][x][1].items():
                            print(playa, "PLAYER ATTACKING")
                            for u in playa:
                                xx,yy = u
                                aUnit = Map.players[a].units[yy][xx]
                                unit.hp -= aUnit.damage
                                unit.attackers[a] += aUnit.damage

                xx,yy = unit.nowPos
                x,y   = unit.pos

                #checking if unit should be downgraded
                if unit.damage > Map.unitTypes[unit.type][4] and unit.hp <= unit.startHp:
                        unit.damage = Map.unitTypes[unit.type][4]
                        pl.resupgrades += 1

                Map.prevOrders.append(unit.orders + [bool(unit.hp)])
                print(unit.orders, "MY ORDERS")
                if unit.hp > 0:
                    if unit.nowPos != unit.pos:
                        unit.new = False
                        print("\n", unit.hp , "GOIN' SOMEWHERE HERE", unit.nowPos)
                        #print(pl.units, "BEFORE")
                        xx,yy = unit.nowPos
                        unit.pos = unit.nowPos
                        if newUnits[y][x] is unit: del newUnits[y][x]
                        newUnits[yy][xx] = unit
                        print(newUnits, "AFTER")
                        if newUnits == pl.units: print("ALERT")
                    else: xx,yy = x,y
                    newUnits[yy][xx] = unit
                    unit = newUnits[yy][xx]
                    print(newUnits[yy][xx].pos)
                    if xx in Map.bases[yy]:
                        base = Map.bases[yy][xx]
                        if base[1] != pl.ID:
                            if base[2] == 'u':
                                if unit.hp <= unit.startHp:
                                    unit.hp = unit.startHp*2
                                    unit.damage = Map.unitTypes[unit.type][4] * 2
                                    #Map.bases[yy][xx][3].delete()
                                    Map.DelBuilding(x,y, decreaseNum = False)
                            elif unit.movePoints == unit.startMP:
                                otherPlID = Map.bases[yy][xx][1]
                                if otherPlID != -1: Map.DelBase(xx,yy, otherPlID)
                                Map.NewBase(xx,yy, pl.ID)
                        else: onBase = True

                    #Reseting the unit stats and issuing the FIRST ORDER
                    unit.movePoints = unit.startMP
                    unit.orders = []
                    timeStep = 1/(unit.startMP + 1)
                    x,y = unit.pos
                    unit.orders.insert(0, ((x,y), unitSelected[1]))
                    plIDs = [pp for pp in Map.players]
                    newTilesUsed = unit.MakeRequests([(x,y)], pl.ID, newTilesUsed, plIDs)
                    #if onBase:  = 1 #### AIRDROP
                    newUnits[y][x] = unit

                else:
                    if unit.sprite is not None: unit.sprite.delete()
                    del newUnits[y][x]
                    maxDmg = 0
                    plid = pl.ID
                    print(pl.ID, "UNIT - LOOKING FOR MOST DAMAGE")
                    for a,i in unit.attackers.items():
                        if i == maxDmg:
                            plid = pl.ID
                            print("INDEX", a, "SAME", i)
                        elif i > maxDmg:
                            maxDmg = i
                            plid = a
                            print("INDEX", a, "BIGGER", i)
                    print(plid)
                    Map.players[plid].ResUnByType[unit.type] += 1
                    xx,yy = unit.nowPos
                    if plid != pl.ID and Map.OnBase(xx,yy, pl.ID):
                        print("EMPTYING BASE")
                        Map.DelBase(xx,yy, pl.ID)
                        Map.NewBase(xx,yy, -1)
        newPls[pl.ID] = newUnits
    for a,i in Map.players.items():
        i.units = newPls[a]
    Map.tilesUsed = newTilesUsed


    mapButtons = {}

    #Check for death conditions
    toDel = []
    for pl in Map.players.values():
        print()
        print(pl.bases, len(pl.bases), "PLAYER", pl.ID)
        if len(pl.bases) < 1:
            if Map.deathCondition == "noBases":
                #addMessage("Player " + str(pl.ID) + " lost all their bases")
                toDel.append(pl.ID)
            else:
                live = False
                for i in pl.units:
                    if len(i) > 0: live = True; print("UNIT FOUND -> NOT DYING YET"); break
                if not live:
                    #addMessage("Player " + str(pl.ID) + " lost")
                    print("DELETING PLAYER")
                    toDel.append(pl.ID)
        elif Map.deathCondition == "no HomeBase":
            if pl.homeBase not in pl.bases:
                #addMessage("Player " + str(pl.ID) + " lost their home base")
                toDel.append(pl.ID)
    for i in toDel:
        Map.DelPlayer(i)

    Map.RedoIDs()

    #Check for win conditions
    if len(Map.players) > 1 and Map.winCondition != 'totalDomination':
            for pl in Map.players.values():
                for base in pl.bases:
                    plBasesLeft = Map.playerNum
                    sourcesLeft = Map.sourceNum
                    if base[2] == 's':
                        sourcesLeft -= 1
                    if base[2] == 'p':
                        plBasesLeft -= 1
                if sourcesLeft == 0 and Map.winCondition == 'allSources':
                    Map.Win(pl.ID)
                    break
                elif plBasesLeft == 0 and Map.winCondition == 'allHomeBases':
                    Map.Win(pl.ID)
                    break
                elif plBasesLeft == 0 and sourcesLeft == 0 and Map.winCondition == 'allBases':
                    Map.Win(pl.ID)
                    break

    else:
        Map.Win(list(Map.players.values())[0].ID)


#--------------------------------------------------------------------------------> WHICH_BUTTON BEGINS
def WhichButton(mpos, buttons, mapButtons):
    global camY, camX, tileSize, tileYSize, unitSelected
    y = int((mpos[1] - camY) // (tileSize*tileYSize))
    x = ((mpos[0] - camX)*2) // tileSize
    x /= 2
    if round(Map.boundaries[y%2][0]) != Map.boundaries[y%2][0]:
        if x == int(x): x -=0.5
    else: x = int(x)
    x = float(x)

    if mpos[0] > window.width * 0.81:
        for a,i in buttons['normMenu'].items():
            if ((mpos[0] > i[0]) and (mpos[1] > i[1]))  and  ((mpos[0] < i[2]) and (mpos[1] < i[3])): return  a,[-1,-1], 'menu'
    else:
        for a,i in buttons['gameSetup'].items():
            if ((mpos[0] > i[0]) and (mpos[1] > i[1]))  and  ((mpos[0] < i[2]) and (mpos[1] < i[3])): return  a,[-1,-1], 'mapS'

    if y > -1 and y < len(Map.boundaries):
        if len(mapButtons) > 1:
            if y in mapButtons['moves'] and x in mapButtons['moves'][y]: return -1, [x,y], 'moves'
            for plID,pl in mapButtons.items():
                if plID == Map.playerActive:
                    if x in pl['units'][y]: return -1, [x,y], 'units'
                    if x in pl['bases'][y]: return -1, [x,y], 'bases'
                elif plID in Map.players and x in pl['units'][y] and not(Map.players[plID].units[y][x].new): return -1, [x,y], 'otherUnits'
            #print(Map.turnNum)

        if Map.turnNum == 0 :
            if x in Map.bases[y]: return -1, [x,y], 'building'
            if x >= Map.boundaries[y][0] and x <= Map.boundaries[y][1]: return -1, [x,y], 'tile'

    return -1,[x,y], 'Default'

#<-----------------------------------------------------------------------------------WHICH_BUTTON ENDS
#--------------------------------------------------------------------------> MAKE_AVAIBLE_TILES BEGINS
def MakeAvaibleTiles(x,y, mType, batch):
    global mapButtons, camX, camY, tileSize, tileYSize, unitSelected
    pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
    pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)

    plA = Map.players[Map.playerActive]
    if mapButtons['moves'] == {}: new = True
    else: new = False
    X,Y = camX/tileSize,camY/(tileSize*tileYSize)
    u,v = unitSelected[0]
    unit = plA.units[v][u]

    if mType == 'move':
        if u in Map.bases[v] and unit.airDrop and Map.bases[v][u][1] == plA.ID: rang = 2
        else: rang = 1
        color = (40, 80, 220, 100)
    else:
        rang = unit.range
        color = (220, 80, 40, 100)

    for yy in range(-rang, rang+1):
        if new: mapButtons['moves'][y+yy] = {}
        maxX = rang-abs(yy)/2
        if y+yy > -1 and y+yy < len(Map.boundaries):
            for xx in Frange(-maxX, maxX+1):
                valid = True
                good  = True
                if mType == 'move':
                    for pl in Map.players.values():
                        if x+xx in pl.units[y+yy] and pl.ID != Map.playerActive:
                            if pl.units[y+yy][x+xx].new == False: valid = False
                            else:                                 good = False
                if (x+xx >= Map.boundaries[y+yy][0] and x+xx <= Map.boundaries[y+yy][1] and (yy != 0 or xx != 0)) and valid:

                    #if not(y+yy in mapButtons['moves']): print(y+yy, "NOT IN MAPBUTTONS Y", mapButtons['moves'])
                    #elif not(x+xx in mapButtons['moves'][y+yy]): print(x+xx, "NOT IN MAPBUTTONS X", mapButtons['moves'])

                    if good: mapButtons['moves'][y+yy][x+xx] = (x+xx,y+yy)
                    else:    mapButtons['moves'][y+yy][x+xx] = (x+xx,y+yy, False)
                    minX = (x+xx+X)
                    minY = (y+yy+Y)*tileYSize
                    batch.add(4,pyglet.gl.GL_QUADS, None,
                                    ("v2i", tuple(map(lambda a: int(a*tileSize),
                                                     (minX,minY, minX,minY + tileYSize,
                                                     minX + 1,minY + tileYSize, minX + 1,minY)))),
                                    ("c4B", (color)*4))
    return batch
#<---------------------------------------------------------------------------- MAKE_AVAIBLE_TILES ENDS

def Simplify(bases, players, tileSprites):
    newBases = []
    for y, row in enumerate(bases):
        newBases.append({})
        for x, base in row.items():
            newBases[y][x] = base[:3]

    newPlayers = []
    for pl in players.values():
        infoDict = {'bases': pl.bases, 'units': [], 'other': [pl.ID, pl.ResUnByType, pl.resupgrades, pl.color, pl.homeBase]}
        for y,row in enumerate(pl.units):
            infoDict['units'].append({})
            for x, unit in row.items():
                newUnit = {}
                newUnit['type'] = unit.type
                newUnit['other']= (unit.hp, unit.movePoints, unit.damage, unit.orders, unit.new)
                infoDict['units'][y][x] = newUnit
        newPlayers.append(infoDict)

    newTiles = []
    for a,row in enumerate(tileSprites):
        newTiles.append([])
        for tile in row:
            newTiles[a].append(tile.color)
    return newBases, newPlayers, newTiles

def Desimplify(players):
    newPlayers = {}
    for pl in players:
        ID, RUBT, RU, Col, HmB = pl['other']
        bases = pl['bases']
        units = []
        for y,row in enumerate(pl['units']):
            units.append({})
            for x, unit in row.items():
                _type = unit['type']
                hp, movePoints, dmg, orders, new = unit['other']
                units[y][x] = Map.NewUnit(_type, x,y, ID, hp= hp, movePoints= movePoints, dmg= dmg, orders= orders, new= new, save= False)
        PL = player.Player(ID, bases, RUBT, Col, units, RU, homeBase = HmB)
        newPlayers[PL.ID] = (PL)
    return newPlayers

def InitMapButtons():
    mapButtons = {}
    for a,pl in Map.players.items():
        mapButtons[a] = {'bases':[], 'units':[]}
        for i in range(0, len(Map.boundaries)):
            mapButtons[a]['bases'].append({})
            mapButtons[a]['units'].append({})
        print(pl.bases, "PLAYER.BASES")
        for i in pl.bases:
            mapButtons[a]['bases'][i[1]][i[0]] = ('base', i[0])
        for row in pl.units:
            for i in row.values():
                x,y = i.pos
                mapButtons[a]['units'][y][x] = ('unit', (x, y))
        #print(mapButtons[a])
    mapButtons['moves'] = {}
    return mapButtons

def SyncPlayerActive(playerActive, players):
    while playerActive not in players and playerActive <= Map.maxPlID:
        print("INCREASING")
        playerActive += 1
    return playerActive
######################################################################################################

@window.event
def on_draw():
    global Map, tileSize, tileYSize, camX, camY, change, frame, buildingImages, unitImages, batch, zoom, zframe, UIBatch, tileBatch, buttonID

    if Map.playerHere:
        if zoom or zframe < 3:
            for row in Map.tileSprites:
                for sprite in row:
                    sprite.scale = tileSize/100
            for i in Map.bases:
                for base in i.values():
                    if base[2] == 's':  sc = tileSize/128
                    elif base[2] == 'u':sc = tileSize/100 * 0.6
                    else:               sc = tileSize/100
                    if len(base) > 3: base[3].scale = sc
                    if len(base) > 4: base[4].scale = tileSize/100
            for pl in Map.players.values():
                for row in pl.units:
                    for unit in row.values():
                        if unit.sprite is not None: unit.sprite.scale = tileSize / 100


        if change or frame < 3:
            window.clear()
            #pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
            #                    ("v2i", (0,0, 0,window.height, window.width,window.height, window.width,0)),
            #                    ("c3B",(100,110,130)*4)
            #                )

            Map.DrawTiles(tileSize, tileYSize, camX, camY, buildingImages)
            tileBatch.draw()
            batch.draw()

            shapesBatch = DrawUI(Map.YSize, Map.XSize)
            shapesBatch.draw()
            UIBatch.draw()
    else:
        pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
                            ("v2i", (0,0, 0,window.height, window.width,window.height, window.width,0)),
                            ("c3B", [100]*12))
        if Map.game: text = "Press mouse when next player ready"
        else: text = "'Player " + str(Map.winningPlayer) + "' has won the game! \n press mouse to start the next game"

        Label = pyglet.text.Label(text = text, x = window.width/2, y = window.height/2,
                        font_name = "Arial.ttf", font_size = 30, anchor_x = 'center', anchor_y = 'center',
                        multiline = True, width = window.width*0.9, align = 'center')
        Label.draw()

    if change: frame = 0
    elif frame < 3: frame += 1
    change = False
    if zoom: zframe = 0
    elif zframe < 3: zframe += 1
    zoom = False
    pyglet.clock.MIN_SLEEP = 0.033
    pyglet.clock.tick()

@window.event #----------------------------------------------------------------------------> KEY PRESS
def on_key_press(symbol, modifiers):
    global showPrevOrders, unitTypeSelected, unitSelected, change, mapButtons, baseType
    key = pyglet.window.key

    if symbol == key.ESCAPE:
        print('NOT CLOSING')
        return pyglet.event.EVENT_HANDLED
    if symbol == key.SPACE:
        unitTypeSelected = None
        mapButtons['moves'] = {}
        unitSelected = [None, "move"]
        change = True
        showPrevOrders = False

    if symbol == key.U: baseType = 'u'
    if symbol == key.P: baseType = 'p'
    if symbol == key.S: baseType = 's'

    print(symbol, "SYMBOL")
    print(key.U)
    if symbol == 97:
        if unitSelected[1] == 'move':
            unitSelected[1] = 'attack'
        else:
            unitSelected[1] = 'move'
        mapButtons['moves'] = {}
        change = True


@window.event #------------------------------------------------------------------------> MOUSE RELEASE
def on_mouse_release(x,y, button, modifiers):
    global showPrevOrders, menuButtons, menuSprites, mapButtons, buttonID, mapButtonID, unitTypeSelected, change, zoom, unitSelected, upgrade, tileBatch, cursors, baseType, zoom
    if Map.playerHere:
        buttonID, mapButtonID, bType = WhichButton((x,y), menuButtons, mapButtons)
        mapButtonID.append(bType)
        window.set_mouse_cursor(cursors[bType])

        pl = Map.players[Map.playerActive]
        if buttonID != -1:
            if bType == 'menu':
                if buttonID == 'NPL':
                    wait = window.get_system_mouse_cursor(window.CURSOR_WAIT)
                    window.set_mouse_cursor(wait)
                    menuSprites['gameSetup']['LAL'].text = 'Load autosave'
                    if Map.playerActive == list(Map.players.values())[len(Map.players)-1].ID:
                        Map.playerActive = 0
                        Map.playerActive = SyncPlayerActive(Map.playerActive, Map.players)

                        with open("Autosave.pickle", 'wb') as autosave:
                            bases, players, tiles = Simplify(Map.bases, Map.players, Map.tileSprites)
                            toSaveDict = {'bases': bases, 'players': players, 'tiles': tiles,
                            'other': [0, Map.turnNum, Map.sides, Map.winCondition, Map.deathCondition, Map.tilesUsed, Map.prevOrders]}
                            pickle.dump(toSaveDict, autosave)

                        if Map.turnNum > 0: EndTurn()
                        Map.turnNum += 1
                    else:
                        Map.playerActive += 1
                        Map.playerActive = SyncPlayerActive(Map.playerActive, Map.players)
                    showPrevOrders = True
                    Map.playerHere = False
                    unitTypeSelected = None
                    mapButtons['moves'] = {}
                    unitSelected = [None, "move"]
                    upgrade = False
                    menuSprites['normMenu']['UPL'].font_size = 18.0
                    wait = window.get_system_mouse_cursor(window.CURSOR_DEFAULT)
                    window.set_mouse_cursor(wait)
                if Map.turnNum == 0:
                    if buttonID == 'UPL':
                        if button == 1: pl.resupgrades += 1
                        if button == 4: pl.resupgrades -= 1
                    if type(buttonID) is int and buttonID < len(Map.unitTypes):
                        if button == 1: pl.ResUnByType[buttonID] += 1
                        if button == 4 and pl.ResUnByType[buttonID] > 0: pl.ResUnByType[buttonID] -= 1
                else:
                    if buttonID == 'UPL':
                        print("CHANGING UPGRADE")
                        if upgrade:
                            print("        TO FALSE")
                            upgrade = False
                            menuSprites['normMenu']['UPL'].font_size = 18.0
                        elif pl.resupgrades > 0:
                            print("         TO TRUE")
                            upgrade = True
                            menuSprites['normMenu']['UPL'].font_size = 22.0
                    if type(buttonID) is int and buttonID < len(Map.unitTypes):
                        if button == 1: unitTypeSelected = buttonID
            else:
                if buttonID == 'NML':
                    a,b,c = Map.sides
                    w,h = Map.XSize, Map.YSize
                    Map.__init__(a,b,c, Map.sourceNum, Map.playerNum, Map.upNum)
                    MakeBaseSprites()
                    mapButtons = {}
                    Map.XSize,Map.YSize = w,h
                if buttonID == 'LAL':
                    if os.path.exists("Autosave.pickle"):
                        menuSprites['gameSetup']['LAL'].text = 'Load autosave'
                        with open("Autosave.pickle", 'rb') as autosave:
                            autosave  = pickle.load(autosave)
                            print(autosave)
                            bases, players, (playerActive, turnNum, (a,b,c), winCon, deathCon, tilesUsed, prevOrders) = autosave['bases'], autosave['players'], autosave['other']
                            if 'tiles' in autosave: tiles = autosave['tiles']
                            else: tiles = None
                            print(bases, "BASES HEY")
                            if True: #to make the thing clearer
                                w,h = Map.XSize, Map.YSize
                                tileBatch = pyglet.graphics.Batch()

                                Map.__init__(a,b,c, Map.sourceNum, Map.playerNum, Map.upNum, tilesUsed = tilesUsed,
                                             deathCondition= deathCon, winCondition= winCon, generate= False)
                                players = Desimplify(players)
                                Map.bases, Map.players, Map.playerActive, Map.turnNum = bases, players, playerActive, turnNum

                                newMax = 0
                                for i in Map.players:
                                    if i > newMax: newMax = i
                                Map.maxPlID = newMax
                                Map.prevOrders      = prevOrders
                                Map.playerActive    = SyncPlayerActive(Map.playerActive, Map.players)
                                Map.XSize,Map.YSize = w,h
                                if turnNum > 0: mapButtons= InitMapButtons()
                                MakeBaseSprites(tileSprites = tiles)
                            change = True
                            Map.playerHere = False
                            del bases, players, playerActive, turnNum
                    else: menuSprites['gameSetup']['LAL'].text = 'Nothing saved yet!'
                zoom = True
            change = True

        if mapButtonID[2] != 'Default':
            x,y = mapButtonID[:2]
            if button == 1:
                change = True
                if mapButtonID[2] == 'bases':
                    print('bases')
                    if unitTypeSelected is not None and pl.ResUnByType[unitTypeSelected] > 0:
                        pl.ResUnByType[unitTypeSelected] -= 1
                        if upgrade and pl.resupgrades > 0: pl.resupgrades -= 1
                        else: upgrade = False
                        Map.NewUnit(unitTypeSelected, x, y, pl.ID, upped = upgrade)
                        print("PASSED")

                #CANCEL ORDERS, SELECT UNIT

                elif mapButtonID[2] == 'units':
                    unit = pl.units[y][x]
                    if unitSelected[0] is None:
                        if not(unit.new) or button == 1:
                            if unit.movePoints == 0:
                                unit.CancelRequests(Map.tilesUsed, pl.ID)
                                del unit.orders[1:]
                                unit.movePoints = unit.startMP
                                mapButtons['moves'] = {}
                            unitSelected[0] = x,y

                    else:
                        unit.CancelRequests(Map.tilesUsed, pl.ID)
                        del unit.orders[1:]
                        unit.movePoints = unit.startMP
                        unitSelected[0] = x,y
                        mapButtons['moves'] = {}

                elif mapButtonID[2] == 'moves':
                    x,y = unitSelected[0]
                    unit = pl.units[y][x]
                    if unit.movePoints > 0:
                        xx,yy = mapButtonID[0],mapButtonID[1]
                        airDrop = False
                        if unit.airDrop and x in Map.bases[y] and Map.bases[y][x][1] == pl.ID and unitSelected[1] == 'move':
                            airDrop = True
                        if len(mapButtons['moves'][yy][xx]) < 3: unit.orders.append(((xx,yy), unitSelected[1]))
                        else:                                    unit.orders.append(((xx,yy), unitSelected[1], False))
                        if unitSelected[1] == 'move':
                            unit.movePoints -= 1
                            timeStep = 1/(unit.startMP + 1)
                            plIDs = [pp for pp in Map.players]
                            '''if airDrop:
                                Map.tilesUsed = unit.MakeRequests([(xx,yy)], pl.ID, Map.tilesUsed, plIDs
                                    orderIs = 1, reverse = True)
                                 -= timeStep'''
                            if True:
                                Map.tilesUsed = unit.MakeRequests([(xx,yy)], pl.ID, Map.tilesUsed, plIDs)
                        else:
                            unit.movePoints = 0
                        mapButtons['moves'] = {}
                        change = True
                        if unit.movePoints == 0: unitSelected = [None, "move"]

                print(Map.turnNum)
                if Map.turnNum == 0:
                    if mapButtonID[2] == 'tile':
                        if baseType == 'p':
                            Map.NewPlayer(x,y) ##MAKING NEW PLAYER
                        else:

                            Map.NewBuilding(x,y, -1, baseType)
                        MakeBaseSprite(x,y)
                        print(Map.bases[y][x], )

                        if baseType == 'u': zoom = True

            elif button == 4:
                change = True
                if mapButtonID[2] == 'units':
                    unit = pl.units[y][x]
                    if Map.OnBase(x,y, pl.ID) and unit.new:
                        pl.ResUnByType[unit.type] += 1
                        print(Map.tilesUsed)
                        Map.DelUnit(x,y, pl.ID)
                        print(Map.tilesUsed)
                        unitSelected[0] = None


                elif Map.turnNum == 0 and mapButtonID[2] == 'building':
                    base = Map.bases[y][x]
                    if base[2] != 'p' or len(Map.players) > 1:
                        if base[2] == 'p':
                            Map.DelPlayer(base[1], redoIDs = True)
                            Map.playerActive = 0
                        #base[3].delete()

                    Map.DelBuilding(x,y)

    else:
        Map.playerHere = True
        change = True
        zoom = True


@window.event
def on_resize(w,h):
    global change
    change = True
    Map.XSize, Map.YSize = w,h

@window.event
def on_mouse_motion(x,y, dx,dy):
    global menuButtons, buttonID, mapButtons, mapButtonID, bType, change, cursors
    if Map.playerHere:
        buttonID, mapButtonID, bType = WhichButton((x,y), menuButtons, mapButtons)
        mapButtonID.append(bType)

        window.set_mouse_cursor(cursors[bType])
        if bType == 'units': change = True
    else:
        wait = window.get_system_mouse_cursor(window.CURSOR_DEFAULT)
        window.set_mouse_cursor(wait)


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    global change, camX, camY, diffX, diffY
    if buttons == pyglet.window.mouse.MIDDLE:
        change = True
        diffX = dx
        diffY = dy
        camX += int(dx)
        camY += int(dy)

@window.event
def on_mouse_scroll(x, y, scroll_x, scroll_y):
    global tileSize, change, zoom, camX, camY
    change = True
    zoom = True
    tileSize += int(scroll_y * 10)
    if tileSize < 0: tileSize = 0
    camX -= int(scroll_y * 5 * max(Map.tiles))
    camY -= int(scroll_y * 5 * len(Map.boundaries))

pyglet.clock.schedule(update)
pyglet.app.run()
pyglet.app.exit()
