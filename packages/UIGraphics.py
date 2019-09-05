#Delete references to menuSprites or menuButtons if not used in Source_of_power

from weakref import ref

class LabelStack:
    def __init__(self, name, pos, batchRef):
        self.name   = name
        self.minPos = pos
        self.maxPos = pos
        self.labels = []
        self.batchRef  = batchRef
        menuButtons['normMenu'][self.name] = self.minPos + self.maxPos

    def UpdateMenuButtons(self):
        menuButtons['normMenu'][self.name] = self.minPos + self.maxPos

    #varToKeep must be a ref object
    def AddInfoLabel( stri, varToKeep, size = 18, color = (255,255,255,255), font = "Arial.ttf", yOffset = 5):
        global menuSprites
        NL = pyglet.text.Label(stri + ": " + str(varToKeep()), font,
                               size, x = self.maxPos[0], y = self.maxPos[1], color = color, batch = self.batchRef())
        self.maxPos[0] = max(self.maxPos[0], NL.content_width)
        self.maxPos[1] += NL.content_height + 5
        menuSprites['normMenu'][name] = NL
        self.UpdateMenuButtons()
        self.labels.append(('INFO', NL))

    def AddSimpleButton( stri, size = 18, color = (255,255,255,255), font = "Arial.ttf", onClickFunction, funcArgsRefs):
        global menuButtons
        NL = pyglet.text.Label(stri, font, size, x = self.maxPos[0], y = self.maxPos[1], color = color, batch = self.batchRef())
        self.maxPos[0] = max(self.maxPos[0], NL.content_width)
        self.maxPos[1] += NL.content_height + 5
        menuSprites['normMenu'][name] = NL
        self.UpdateMenuButtons()
        self.labels.append(('BUTTON', NL, onClickFunction, funcArgsRefs))

    def OnClick(mPos, mButton):
        for label in self.labels:
            if label[0] == 'BUTTON'
                x,y = label[1].x,label[1].y
                x1,y1 = x + label.content_width, y + label.content_height
                mx,my = mpos
                if mx > x and mx < x1 and my > y and my < y1:
                    onClickFunction(mPos, mButton, funcArgsRefs())
                    break
