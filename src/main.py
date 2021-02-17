from time import sleep
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from win32gui import *


class BridgesTrayIcon(QSystemTrayIcon):
    def __init__(self):
        super(BridgesTrayIcon, self).__init__()


class App:
    def __init__(self):

        self.app = QApplication([])
        self.menu = QMenu()
        self.buttons = []
        self.quitButton = QAction()
        self.allButton = QAction()

        # Give it tray abilities
        self.app.setQuitOnLastWindowClosed(False)
        # Adding an icon
        self.icon = QIcon("assets/icon.png")

        # Adding item on the menu bar
        self.tray = BridgesTrayIcon()
        self.tray.setIcon(self.icon)
        self.tray.setVisible(True)

        # Adding options to the System Tray
        self.tray.setContextMenu(self.menu)
        self.menu.aboutToShow.connect(self.populateMenu)

        self.app.exec()

    def populateMenu(self):
        # What do we need to add
        winList = []
        EnumWindows(handleEnumWindows, winList)

        # clear some values
        self.buttons = []
        self.menu.clear()

        # Add All Apps
        for i in range(len(winList)):
            self.buttons.append(QAction(f"{winList[i]}"))
            self.buttons[i].triggered.connect(lambda randomBool, name=winList[i]: moveWindow(name, 1))

        for i in range(len(self.buttons)):
            self.menu.addAction(self.buttons[i])

        # Close all apps
        self.allButton = QAction("Move All Windows")

        self.allButton.triggered.connect(lambda randomBool, tempList=winList: moveAllWindows(tempList))
        self.menu.addAction(self.allButton)

        # To quit the app
        self.quitButton = QAction("Quit")
        self.quitButton.triggered.connect(self.app.quit)
        self.menu.addAction(self.quitButton)


def moveAllWindows(winList):
    for i in range(len(winList)):
        moveWindow(winList[i], 1)


def moveWindow(name, time):
    # init variable
    handle = FindWindow(None, name)
    runs = 1
    enable = True

    # Get the windows initial position
    ileft, itop, iright, ibottom = GetWindowRect(handle)

    # How much per loop are we going to move the window
    # Based off of the x-axis difference divided by the total amount of frames @ 60 fps
    xIncrement = ileft / (60 * time)

    # Check if the window is against the y-axis, if it is don't worry about animating for now, avoid dividing by 0
    if ileft == 0:
        MoveWindow(handle, 0, 0, iright - ileft, ibottom - itop, True)
        return

    # See below
    m = itop / ileft

    # So this is just using some basic algebra but its written like poop
    # Create a line from the origin (top-left of main-screen) using our old friend y = mx + b
    # In our line b is our y intercept and since we're going for the origin its 0 and we can forget it exists
    # We can calculate m (the slope of the diagonal) with rise over run. (keeping in mind that pos y is down-screen)
    # We're going to a new x cord for our window that's 'xIncrement' closer to the origin
    # We do this by setting the newX cord to xIncrement * interations I don't remember why but its important
    # Now that we have our new x position, we can snap the window to our diagonal line by multiplying by y
    # Our newY = m * newX
    # If our new cords are both 0 we can stop looping
    # The abs() check is to necessary due to there being a chance we lose a couple pixels due to float to int casting
    # So it check if we're going to over-shoot the origin and if so, we effectively set to 0.
    # It feels like I should sleep 1/60th of a second to match framerate, but that looks choppy idk why 1/120 fixes it.
    # TODO Maybe replace this with a for loop, a while loop feels icky
    while enable:
        nleft, ntop, nright, nbottom = GetWindowRect(handle)

        if abs(ileft) < abs(xIncrement):
            xIncrement = ileft

        xOffset = int(xIncrement * runs)
        newX = ileft - xOffset
        newY = int(m * newX)

        if newX == 0 and newY == 0:
            enable = False

        MoveWindow(handle, newX, newY, iright - ileft, ibottom - itop, True)
        runs += 1
        sleep(1 / 120)


def isPhantomWindow(handle):
    # Is it even fucking trying to act real?
    windowText = GetWindowText(handle)
    if windowText == "":
        return True

    if not IsWindowVisible(handle):
        return True

    # Do the window be looking thicc or nah?
    a, b, c, d = GetClientRect(handle)
    if c + d == 0:
        return True

    # I'm scared of phantom windows. These two windows programs will show as Top Level even when not opened.
    # If they are legit, they have this child window: "Windows.UI.Core.CoreWindow"
    # https://stackoverflow.com/questions/16973995/whats-the-best-way-do-determine-if-an-hwnd-represents-a-top-level-window
    if windowText in ["Microsoft Store", "Settings"]:
        if "Windows.UI.Core.CoreWindow" not in childWindows(handle):
            return True
        else:
            return False

    # Handles keyboard stuff but really likes to show up as a TLW
    if windowText == "Microsoft Text Input Application":
        return True
    # Is always there
    if windowText == "Program Manager":
        return True


def childWindows(handle):
    titles = []
    EnumChildWindows(handle, handleChildEnum, titles)
    return titles


def handleChildEnum(handle, titles):
    windowText = GetClassName(handle)
    if windowText == "":
        return True
    else:
        titles.append(windowText)


def handleEnumWindows(handle, returnList):
    # bGet title
    windowText = GetWindowText(handle)
    if isPhantomWindow(handle):
        return True

    # print(windowText)
    returnList.append(windowText)


def main():
    mainThread = App()
    mainThread.populateMenu()


if __name__ == "__main__":
    main()
    input()
