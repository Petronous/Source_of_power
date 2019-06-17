#Delete references to menuSprites or menuButtons if not used in Source_of_power

from weakref import ref

class LabelStack:
    def __init__(self, pos, batchRef):
        self.minPos = pos
        self.maxPos = pos
        self.labels = []
        self.batchRef  = batchRef
  
    #varToKeep must be a ref object
    def AddInfoLabel(name, stri, varToKeep, size = 18, color = (255,255,255,255)):
        global menuSprites
        NL = pyglet.text.Label("stri: " + str(varToKeep()), "Arial.ttf",
                                    size, x = self.maxPos[0], y = self.maxPos[1], color = color, batch = self.batchRef())
        menuSprites['normMenu'][name] = NL
        self.maxPos[0] += NL.content_width
        self.maxPos[1] += NL.content_height
        self.labels.append(('INFO', NL))

    def AddSimpleButton(name, stri, varToKeep, size = 18, color = (255,255,255,255), onClickFunction, funcArgsRefs):
        global menuButtons
        NL = pyglet.text.Label("stri: " + str(varToKeep()), "Arial.ttf",
                                    size, x = self.maxPos[0], y = self.maxPos[1], color = color, batch = self.batchRef())
        self.maxPos[0] += NL.content_width
        self.maxPos[1] += NL.content_height
        menuSprites['normMenu'][name] = NL
        menuButtons['normMenu']['NL'] = (NL.x,NL.y, NL.x + NL.content_width,NL.y + NL.content_height)
