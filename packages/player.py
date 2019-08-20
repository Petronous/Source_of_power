import pyglet
from pyglet import gl
from random import randint as rand



class Unit:
    def __init__(self, initList, hp, movePoints, orders, new):
        global UIBatch, tileSize
        pos, startHp, airDrop, Range, startMP, dmg, img, type_ = initList

        self.type      = type_
        self.pos       = pos
        self.nowPos    = pos
        self.startHp   = startHp
        self.hp        = hp
        self.airDrop   = airDrop
        self.range     = Range
        self.startMP   = startMP
        self.movePoints= movePoints
        self.damage    = dmg
        self.orders    = orders
        self.sprite    = pyglet.sprite.Sprite(img, x = pos[0], y = pos[1], batch = None)
        gl.glTexParameteri(self.sprite._texture.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(self.sprite._texture.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        self.new       = new
        self.attackers = {}

    def MakeRequests(self, ordersPos, plID, tilesUsed, plIDs, orderIs = None, last = None):
        timeStep = 0
        print("\nUNIT FROM", self.pos, "IS REQUESTING")
        for a,i in enumerate(ordersPos):
            xx,yy = i
            if not(xx in tilesUsed[yy]):
                tilesUsed[yy][xx] = [{},{}]
                for b in plIDs:
                    tilesUsed[yy][xx][0][b] = []
                    tilesUsed[yy][xx][1][b] = []
                #print(Map.tilesUsed[yy][xx], "BEFORE")
            if orderIs == None: index = len(self.orders)-1
            else: index = orderIs[a]
            #if reverse: times = []
            #else:
            if last == None or index != last: times = [index, index]
            elif index == last:               times = [index, 'end']
            print("APPENDING", [self.pos, index, times], "TO TILE AT", xx, yy)
            tilesUsed[yy][xx][0][plID].append(
                [self.pos, index, times])
        return tilesUsed

    def CancelRequests(self, tilesUsed, plID, first = False, index = None):
        if first: begin = 1
        else: begin = 0
        if index is None:
            for i in self.orders[begin:]:
               if i[1] == 'move':
                   x,y = i[0]
                   if x in tilesUsed[y]:
                       print(tilesUsed[y][x][0][plID], "SHOW TU AT UNIT POSITION")
                       for b,a in enumerate(tilesUsed[y][x][0][plID]):
                           if a[0] == self.pos:
                               print(a, "THE REQUEST TO BE DELETED")
                               tilesUsed[y][x][0][plID].pop(b)
        else:
            i = self.orders[index]
            x,y = i[0]
            if x in tilesUsed[y]:
                print(tilesUsed[y][x][0][plID], "SHOW TU AT UNIT POSITION")
                for b,a in enumerate(tilesUsed[y][x][0][plID]):
                    print(a, "THE REQUEST TO BE DELETED")
                    if a[0] == self.pos: tilesUsed[y][x][0][plID].pop(b)
        return tilesUsed

    def BackOff(self, plID, order, oindex, tilesUsed):
        tile = tilesUsed[order[0][1]][order[0][0]]
        tileIndex, inTile = PosIndex(order[0], plID, self.pos, tilesUsed)
        if inTile: tile[0][plID].pop(tileIndex)
        print(self.orders, "ORDERS")
        del self.orders[oindex:]
        print(self.nowPos, "MY NOWPOS")

        pNowPos = self.orders[max(oindex-1, 0)][0]
        tile = tilesUsed [pNowPos]
        if (tile[2] != plID or MaxEndsIndex(tile[0])[plID] > 0)  and  len(self.orders) > 1:
            self.nowPos = pNowPos
            tilesUsed, ordersToDel, moveUnits = self.BackOff(plID, self.orders[oindex-1], oindex-1, tilesUsed)
        else:
            #Stop units from going in if orders canceled
            print('cancelling #############################################')
            tilesUsed, ordersToDel, moveUnits = self.CancelOthers(players, tilesUsed, ordersToDel, time, plID, moveUnits)
        return tilesUsed, ordersToDel, moveUnits

    def CancelOthers(self, players, tilesUsed, ordersToDel, time, plID, moveUnits):
        tUs = tilesUsed[self.nowPos[1]][self.nowPos[0]]
        for i in tUs[0][plID]:
            if i[0] != self.pos and (i[2][1] == 'end'):
                print(i[1], "I[1] IN CANCEL_OTHERS")
                ordersToDel.append((i[0], i[1], plID))
                moveUnits.append((i[0], i[1]-1, plID))
                targetUnit = players[plID].units[i[0][1]][i[0][0]]
                targetUnit.nowPos = targetUnit.orders[i[1]-1][0]
                tilesUsed, ordersToDel, moveUnits = targetUnit.CancelOthers(players, tilesUsed, ordersToDel, i[1]-1, plID, moveUnits)

        return tilesUsed, ordersToDel, moveUnits

    def DoOrders(self, players, tilesUsed, plID, onBase):
        print()
        # tile = unitPos, orderIndex, times
        timeStep = 0
        ordersToDel = []
        moveUnits = []
        for pl in players:
            self.attackers[pl] = 0
        '''if len(self.orders) < 2:
            time = 0
            timeStep = 1/(self.startMP + 1)
            tilesUsed, ordersToDel = self.DoTile(players, 0, (self.pos, 'move'), tilesUsed, ordersToDel, plID, time, moveUnits)'''
        '''if self.airDrop and onBase:
            toFor = list(enumerate(self.orders))
            toFor.reverse()
            plIDs = [pp for pp in players]
            for index,i in toFor:
                if i[1] == 'move':
                    x,y = self.orders[index][0]
                    print(index, "MY TIME NOW #######################################")
                    inTile = PosIndex((x,y), plID, self.pos, tilesUsed)[1]
                    if not(inTile):
                        tilesUsed = self.MakeRequests([(x,y)], plID, tilesUsed, plIDs,
                                                      orderIs = [index], last = index)
                    tilesUsed, ordersToDel, go = self.DoTile(players, index, i, tilesUsed,
                                                             ordersToDel, plID,
                                                             moveUnits)
                    if go:
                        print("I WENT SOMEWHERE")
                        break
                    else:
                        print("BACKING OFF")
                        x,y = self.orders[index-1][0]
                        tilesUsed = self.MakeRequests([(x,y)], plID, tilesUsed, plIDs,
                                                      orderIs = [index], last = index)'''
        #else:
        if True:
            for index, i in enumerate(self.orders):
                print('\n DOING ORDER NUMBER', index)
                if i[1] == 'move':
                    tilesUsed, ordersToDel, go = self.DoTile(players, index, i, tilesUsed,
                                                             ordersToDel, plID, moveUnits)


        if len(self.orders) > 0:
            o = self.orders[len(self.orders)-1]
            if o[1] == 'attack':
                x,y = o[0]
                if x in tilesUsed[y]: tilesUsed[y][x][1][plID].append(self.pos)

        return tilesUsed, ordersToDel, moveUnits

    def DoTile(self, players, index, i, tilesUsed, ordersToDel, plID, moveUnits):
        time = index
        timeStep = 0
        x,y = i[0]
        xx,yy = self.pos
        print(i[0], "DESIRED POSITION")
        # tileUsed
        tUs = tilesUsed[y][x]
        tileIndex, inTile = PosIndex(i[0], plID, self.pos, tilesUsed)
        # tile         = [moves{0: requests, 1: requests ...}, attacks{0: requests, 1: requests ...},   pl, maxx]
        #                                                                                               ^   ^ Only added by DoTile
        # request/unit = [unitPos, orderIndex, times]
        if i[1] == 'move':
                go = True
                maxU = 0
                print(tUs[0], "REQUESTS FOR TILE")

                #FIND THE MAJORITY
                if len(tUs) == 2:
                    pl, maxx = MaxEndsIndex(tUs[0])
                    tUs.append(pl)
                    tUs.append(maxx)
                else:
                    pl = tUs[2]
                    maxx = tUs[3]

                #DELETE THE MINORITIES
                for b,us in tUs[0].items():
                    if b != pl:
                        for u in us:
                            if u[2][1] == 'end':
                                tUs[0][b].pop(PosIndex((x,y), b, u[0], tilesUsed)[0])
                                print("REQUESTING DELETE_UNIT_REQUEST", u, "OF PLAYER", b)
                                ordersToDel.append((u[0], u[1], b))

                #CHECK IF GO
                print(PosIndex(i[0], plID, self.pos, tilesUsed)[0], "MY INDEX",  tUs[0][plID], "THE TILE")
                print(tUs[0][plID][PosIndex(i[0], plID, self.pos, tilesUsed)[0]], "MY TILE")
                myTime = tUs[0][plID][PosIndex(i[0], plID, self.pos, tilesUsed)[0]][2][1]
                if len(self.orders) > 1:
                    if pl != -1 or myTime != 'end':
                        for otherTileIndex,unit in enumerate(tUs[0][plID]):
                            if unit[0] != self.pos:
                                sTime, eTime = unit[2]
                                print("MY TIME", time, "ITS TIME", sTime, eTime)
                                print(unit[0], self.pos)
                                if eTime == 'end' and myTime == 'end' and tileIndex > otherTileIndex:
                                    go = False
                                    print("NOT GO!!!!!!!!!!!!!!!!")

                    else:
                        go = False
                        print("NOT GO NO PLAYER!!!!!!!!!!!!!!!!!!")

                #GOIN' OR NOT
                if go: self.nowPos = [x,y]
                else: tilesUsed, ordersToDel, moveUnits = self.BackOff(plID, i, index, tilesUsed,)



        tilesUsed[y][x] = tUs
        return tilesUsed, ordersToDel, go


class Player:
    def __init__(self, ID, bases, RUByType, color, activeUnits = [], resUpgrades = 0, homeBase = None):
        self.ID          = ID
        self.bases       = bases
        if homeBase is None: self.homeBase = bases[0]
        else:                self.homeBase = homeBase
        self.ResUnByType = RUByType
        self.units       = activeUnits
        self.resupgrades = resUpgrades
        self.color       = color

def PosIndex(tilePos, plID, unitPos, tilesUsed, type = 0):
    x,y = tilePos
    if x in tilesUsed[y]:
        plTile = tilesUsed[y][x][type][plID]
        for a,i in enumerate(plTile):
            if i[0] == unitPos: return a, True
    return -1, False

def MaxEndsIndex(attempts, endsOnly = False):
    ends = {}
    for plID, pl in attempts.items():
        ends[plID] = 0
        for unit in pl:
            if unit[2][1] == 'end': ends[plID] += 1

    if endsOnly: return ends

    index = -1
    maxx  = -1
    for plID, plends in ends.items():
        if plends >  maxx: index = plID; maxx = plends
        elif plends == maxx: index = -1
    return index, maxx


if __name__ == '__main__':
    UIBatch = pyglet.graphics.Batch()
    tileSize = 100
