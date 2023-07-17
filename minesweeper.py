# Python Version 2.7.3
# File: minesweeper.py

from tkinter import *
from tkinter import messagebox as tkMessageBox
from collections import deque
import random
import platform
from datetime import datetime
from math import comb
import copy

import signal

 

SIZE_X = 16  #Rows
SIZE_Y = 30  #Columns

STATE_DEFAULT = 0
STATE_CLICKED = 1
STATE_FLAGGED = 2

BTN_CLICK = "<Button-1>"
BTN_FLAG = "<Button-2>" if platform.system() == 'Darwin' else "<Button-3>"
BTN_MIDDLE = "<Button-2>"


window = None

class Minesweeper:
    
    def __init__(self, tk):
        
        # DEBUG
        self.armed = False
        self.gamecount = 0
        self.woncount = 0
        self.earlylosscount = 0
        self.latelosscount = 0
        signal.signal(signal.SIGINT, self.siginthandler)

        # import images
        self.images = {
            "plain": PhotoImage(file = "images/tile_plain.gif"),
            "clicked": PhotoImage(file = "images/tile_clicked.gif"),
            "mine": PhotoImage(file = "images/tile_mine.gif"),
            "flag": PhotoImage(file = "images/tile_flag.gif"),
            "wrong": PhotoImage(file = "images/tile_wrong.gif"),
            "numbers": []
        }
        for i in range(1, 9):
            self.images["numbers"].append(PhotoImage(file = "images/tile_"+str(i)+".gif"))

        # set up frame
        self.tk = tk
        self.frame = Frame(self.tk)
        self.frame.pack()

        # set up labels/UI
        self.labels = {
            "time": Label(self.frame, text = "00:00:00"),
            "mines": Label(self.frame, text = "Mines: 0"),
            "flags": Label(self.frame, text = "Flags: 0")
        }
        self.labels["time"].grid(row = 0, column = 0, columnspan = SIZE_Y) # top full width
        self.labels["mines"].grid(row = SIZE_X+1, column = 0, columnspan = int(SIZE_Y/2)) # bottom left
        self.labels["flags"].grid(row = SIZE_X+1, column = int(SIZE_Y/2)-1, columnspan = int(SIZE_Y/2)) # bottom right
        
        self.buttons = {
            "solve": Button(self.frame, text = "solve"),
        }
        self.buttons["solve"].grid(row = SIZE_X+2, column = 0, columnspan = SIZE_Y) # bottom full width
        self.restart() # start game
        self.updateTimer() # init timer

    def setup(self):
        # create flag and clicked tile variables
        self.flagCount = 0
        self.correctFlagCount = 0
        self.clickedCount = 0
        self.startTime = None
        # For solver
        self.first_click = True
        self.cascaded = False

        # create buttons
        self.tiles = dict({})
        self.mines = 99
        self.hundredCount = 0
        self.borderedTiles = []
        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                if y == 0:
                    self.tiles[x] = {}

                id = str(x) + "_" + str(y)

                # tile image changeable for debug reasons:
                gfx = self.images["plain"]
                
                # Definition of a tile
                tile = {
                    "id": id,
                    "isMine": False,
                    "state": STATE_DEFAULT,
                    "coords": {
                        "x": x,
                        "y": y,
                    },
                    "button": Button(self.frame, image = gfx),
                    "mines": 0, # calculated after grid is built
                    "probability": -1, # calculated when solving
                    "isBorder": False, # calculated when solving
                    "solver_mine": False, # calculated when solving
                    "solver_safe": False, # calculated when solving
                    "nr_present_in_arrangement": 0, # calculated when solving
                    "combs": 0, # calculated when solving, I have no idea what to call this
                }

                tile["button"].bind(BTN_CLICK, self.onClickWrapper(x, y))
                tile["button"].bind(BTN_FLAG, self.onRightClickWrapper(x, y))
                tile["button"].bind(BTN_MIDDLE, self.onMiddleClickWrapper(x, y))
                tile["button"].grid( row = x+1, column = y ) # offset by 1 row for timer

                self.tiles[x][y] = tile
                
        # Populate the board with mines
        for _ in range(0, self.mines):
            x = random.randint(0, SIZE_X-1)
            y = random.randint(0, SIZE_Y-1)
            while self.tiles[x][y]["isMine"] == True:
                x = random.randint(0, SIZE_X-1)
                y = random.randint(0, SIZE_Y-1)
            self.tiles[x][y]["isMine"] = True
        #DEBUG
        #self.tiles[1][3]["isMine"] = True # Top right
        #self.tiles[2][1]["isMine"] = True

        # loop again to find nearby mines and display number on tile
        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                mc = 0
                for n in self.getNeighbors(x, y):
                    mc += 1 if n["isMine"] else 0
                self.tiles[x][y]["mines"] = mc
                
        # Bind button to solve
        self.buttons["solve"].bind(BTN_CLICK, self.onSolveWrapper())
        # Unclick it in case its clicked after a restart
        self.buttons["solve"].config(relief = RAISED)
        
    # Restarts the Whole Window    
    def restart(self):
        self.buttons["solve"].config(relief = RAISED)
        self.setup()
        self.updateLabels()

    def updateLabels(self):
        self.labels["flags"].config(text = "Flags: "+str(self.flagCount))
        self.labels["mines"].config(text = "Mines: "+str(self.mines))

    def siginthandler(self, signum, frame):
        print("won: " + str(self.woncount))
        print("earlyloss: " + str(self.earlylosscount))
        print("lateloss: " + str(self.latelosscount))
        print("avg time: " + str((datetime.now() - self.startTime).total_seconds()/self.gamecount))
        print("total: " + str(self.gamecount))
        exit(0)
        
    def gameOver(self, won):
        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                if self.tiles[x][y]["isMine"] == False and self.tiles[x][y]["state"] == STATE_FLAGGED:
                    self.tiles[x][y]["button"].config(image = self.images["wrong"])
                if self.tiles[x][y]["isMine"] == True and self.tiles[x][y]["state"] != STATE_FLAGGED:
                    self.tiles[x][y]["button"].config(image = self.images["mine"])

        self.tk.update()

        msg = "You Win! Play again?" if won else "You Lose! Play again?"
        """res = tkMessageBox.askyesno("Game Over", msg)
        if res:
            self.restart()
        else:
            self.tk.quit()"""
        self.gamecount += 1
        if won:
            self.woncount += 1
        if self.flagCount < 20:
            self.earlylosscount += 1
        elif self.flagCount >=80:
            self.latelosscount += 1
        if self.gamecount < 100:
            self.restart()
            self.solve()
        else:
            print("won: " + str(self.woncount))
            print("earlyloss: " + str(self.earlylosscount))
            print("lateloss: " + str(self.latelosscount))
            print("avg time: " + str((datetime.now() - self.startTime).total_seconds()/self.gamecount))
            print("total: " + str(self.gamecount))
            self.tk.quit()
            
        

    def updateTimer(self):
        ts = "00:00:00"
        if self.startTime != None:
            delta = datetime.now() - self.startTime
            ts = str(delta).split('.')[0] # drop ms
            if delta.total_seconds() < 36000:
                ts = "0" + ts # zero-pad
        self.labels["time"].config(text = ts)
        self.frame.after(100, self.updateTimer)

    def getNeighbors(self, x, y):
        neighbors = []
        coords = [
            {"x": x-1,  "y": y-1},  #top right
            {"x": x-1,  "y": y},    #top middle
            {"x": x-1,  "y": y+1},  #top left
            {"x": x,    "y": y-1},  #left
            {"x": x,    "y": y+1},  #right
            {"x": x+1,  "y": y-1},  #bottom right
            {"x": x+1,  "y": y},    #bottom middle
            {"x": x+1,  "y": y+1},  #bottom left
        ]
        for n in coords:
            try:
                neighbors.append(self.tiles[n["x"]][n["y"]])
            except KeyError:
                pass
        return neighbors

    def onClickWrapper(self, x, y):
        return lambda Button: self.onClick(self.tiles[x][y])

    def onRightClickWrapper(self, x, y):
        return lambda Button: self.onRightClick(self.tiles[x][y])
    
    def onMiddleClickWrapper(self, x, y):
        return lambda Button: self.onMiddleClick(self.tiles[x][y])
    
    def onMiddleClick(self, tile):
        print(tile["id"], tile["solver_mine"])

    def onClick(self, tile):
        if self.startTime == None:
            self.startTime = datetime.now()

        if tile["isMine"] == True:
            # end game
            tile["button"].config(bg="black")
            self.gameOver(False)
            return False
        
        # change image
        
        # Case: no mines around
        if tile["mines"] == 0:
            self.cascaded = True
            self.first_click = False
            tile["button"].config(image = self.images["clicked"])
            tile["solver_mine"] = False
            tile["solver_safe"] = False
            self.clearSurroundingTiles(tile["id"])
            
        # Case: mines around
        else:
            self.first_click = False
            tile["button"].config(image = self.images["numbers"][tile["mines"]-1])
            tile["solver_mine"] = False
            tile["solver_safe"] = False
            neighbours = self.getNeighbors(tile["coords"]["x"], tile["coords"]["y"])
            for neighbour in neighbours:
                if neighbour["state"] == STATE_DEFAULT:
                    neighbour["isBorder"] = True
            
        
        # if not already set as clicked, change state and count
        if tile["state"] != STATE_CLICKED:
            tile["state"] = STATE_CLICKED
            self.clickedCount += 1
            tile["isBorder"] = False
        if self.clickedCount == (SIZE_X * SIZE_Y) - self.mines:
            self.gameOver(True)
            return False
        return True

    def onRightClick(self, tile):
        if self.startTime == None:
            self.startTime = datetime.now()

        # if not clicked
        if tile["state"] == STATE_DEFAULT:
            tile["button"].config(image = self.images["flag"])
            tile["probability"] = 100
            self.hundredCount += 1
            tile["state"] = STATE_FLAGGED
            tile["button"].unbind(BTN_CLICK)
            # if a mine
            if tile["isMine"] == True:
                self.correctFlagCount += 1
            self.flagCount += 1
            self.updateLabels()
        # if flagged, unflag
        elif tile["state"] == STATE_FLAGGED:
            tile["button"].config(image = self.images["plain"])
            tile["state"] = 0
            tile["button"].bind(BTN_CLICK, self.onClickWrapper(tile["coords"]["x"], tile["coords"]["y"]))
            tile["probability"] = -1
            self.hundredCount -= 1
            # if a mine
            if tile["isMine"] == True:
                self.correctFlagCount -= 1
            self.flagCount -= 1
            self.updateLabels()

    def clearSurroundingTiles(self, id):
        queue = deque([id])

        while len(queue) != 0:
            key = queue.popleft()
            parts = key.split("_")
            x = int(parts[0])
            y = int(parts[1])

            for tile in self.getNeighbors(x, y):
                self.clearTile(tile, queue)

    def clearTile(self, tile, queue):
        if tile["state"] != STATE_DEFAULT:
            return

        if tile["mines"] == 0:
            tile["button"].config(image = self.images["clicked"])
            tile["solver_mine"] = False
            tile["solver_safe"] = False
            queue.append(tile["id"])
        else:
            tile["button"].config(image = self.images["numbers"][tile["mines"]-1])
            tile["solver_mine"] = False
            tile["solver_safe"] = False
            for neighbour in self.getNeighbors(tile["coords"]["x"], tile["coords"]["y"]):
                if neighbour["state"] == STATE_DEFAULT:
                    neighbour["isBorder"] = True

        tile["state"] = STATE_CLICKED
        # Set neighbours as border tiles
        neighbours = self.getNeighbors(tile["coords"]["x"], tile["coords"]["y"])
        for neighbour in neighbours:
            if neighbour["state"] == STATE_DEFAULT:
                neighbour["isBorder"] = True
        self.clickedCount += 1
        
    def onSolveWrapper(self):
        return lambda Button: self.solve()
    
    def solve(self):
        # First click is on a random corner. 
        # This has the highest chance of resulting in a cascade.
        # As the corner is the place that minimizes the number of adjacent tiles.
        if self.first_click:
            corners = [(0, 0), (0, SIZE_Y-1), (SIZE_X-1, 0), (SIZE_X-1, SIZE_Y-1)]
            random.shuffle(corners)
            for x,y in corners:
                if self.tiles[x][y]["state"] == STATE_DEFAULT:
                    if not self.onClick(self.tiles[x][y]): # return if we lose
                        return 
                    if self.cascaded:
                        break
                    

        # Now, we will run two rules here before the probability calculation.
        # Rule A: If a tile has the same number of adjacent mines as the number of unclicked tiles adjacent to it, then all of those tiles are mines.
        # Rule B: If a tile has the same number of adjacent squares that are flags, all of those tiles are safe.
        
        while self.ruleA() or self.ruleB():
            # Do nothing, rule functions do stuff themselves
            pass
        self.ruleC()
        
        
        # Now, we always want to click on the tiles that are adjacent to the exposed tiles.
        # Because logic. 
        # Therefore, our program will work like this:
        # 1. Find all exposed tiles.
        # 2. Find all bordered tiles.
        # 3. Generate all valid arrangements of mines in the bordered tiles.
        # 4. Get the number of mines in each arrangement
        # 5. Subtract the number of mines in a given arrangement from the total number of mines, then 
        #    perform a calculation where we choose the number of mines left from the 
        #    unbordered tiles. This is the total number of combinations where the mines are present
        #    in the given arrangement
        # 6. Repeat for all arrangements.
        # 7. Assign each cell the number of times it was determined as a mine
        # 8. Divide each number in the cell by the total number of arrangements, which is about 2.7 x 10^102
        # 9. Multiply result by 100 to get the probability of that cell being a mine.
        # 10. Flag all cells with probability of 100, then click on the cell with the lowest probability.
        
        
        # 1 and 2
        exposedTiles = []
        borderedTiles = []
        
        for x in range (0, SIZE_X):
            for y in range (0, SIZE_Y):
                if self.tiles[x][y]["state"] == STATE_CLICKED and self.tiles[x][y]["mines"] != 0:
                    exposedTiles.append(self.tiles[x][y])
                elif self.tiles[x][y]["state"] == STATE_DEFAULT and self.tiles[x][y]["isBorder"]:
                    borderedTiles.append(self.tiles[x][y])
                    
                    
        # DEBUG Color bordered tiles
        """for tile in borderedTiles:
            print(tile["id"])
            tile["button"].config(bg="red")
            
        print(len(borderedTiles))"""
                    
        # 3. 
        arrangements = []
        # Copy the bordered tiles, so we can deepcopy it in the recursive func
        borderedTilesCopy = [{k: tile[k] for k in tile.keys() - {"button"}} for tile in borderedTiles]
        
        
        print ("generating arrangements")
        self.generate_arrangements(exposedTiles, borderedTilesCopy, 0, arrangements, debug=False)
        print(len(arrangements), "arrangements generated")
        
        # Count unbordered tiles
        unbordered = 0
        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                if self.tiles[x][y]["state"] == STATE_DEFAULT and not self.tiles[x][y]["isBorder"]:
                    unbordered += 1
            
            
        print ("Calculating probabilities")
        # 4.
        combs = 0
        for arrangement in arrangements:
            #print ("arrangement: " + str(arrangement))
            minesPlaced = 0
            for tile in arrangement:
                if tile["solver_mine"]:
                    minesPlaced += 1
            remainingMines = 99 - minesPlaced - self.flagCount
            if remainingMines >= 0 and remainingMines <= unbordered:
                unborderedCombinations = comb(unbordered, remainingMines)
                for tile in arrangement:
                    if tile["solver_mine"]:
                        self.tiles[tile["coords"]["x"]][tile["coords"]["y"]]["combs"] += unborderedCombinations
                combs += unborderedCombinations
                # Calculate for unbordered
                for x in range(0, SIZE_X):
                    for y in range(0, SIZE_Y):
                        if self.tiles[x][y]["state"] != STATE_CLICKED and not self.tiles[x][y]["isBorder"]:
                            self.tiles[x][y]["combs"] += remainingMines / unbordered * unborderedCombinations
                        
        # Calculate probability of each cell by dividing the number of arrangements with mines in each cell by total arrangements     
        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                if self.tiles[x][y]["isBorder"] and self.tiles[x][y]["probability"] == -1:
                    #print(self.tiles[x][y]["id"] + " " + str(self.tiles[x][y]["combs"]) + " " + str(combs))
                    self.tiles[x][y]["probability"] = round(self.tiles[x][y]["combs"] / combs * 100);
                if self.tiles[x][y]["state"] != STATE_CLICKED and not self.tiles[x][y]["isBorder"] and self.tiles[x][y]["probability"] == -1:
                    self.tiles[x][y]["probability"] = round(self.tiles[x][y]["combs"] / combs * 100);
        
        print ("did probability calculation")
                
        # Click on the one with the lowest probability
        for tile in borderedTiles:
            x = tile["coords"]["x"]
            y = tile["coords"]["y"]
            #print (self.tiles[x][y]["id"] + " " + str(self.tiles[x][y]["probability"]))
            if self.tiles[x][y]["probability"] == 100:
                #self.tiles[x][y]["button"].config(bg="red")
                # Flag it
                self.tiles[x][y]["probability"] = 100
                self.hundredCount += 1
                self.tiles[x][y]["button"].config(image = self.images["flag"])
                self.tiles[x][y]["state"] = STATE_FLAGGED
                self.tiles[x][y]["probability"] = 100
                self.hundredCount += 1
                self.tiles[x][y]["button"].unbind(BTN_CLICK)
                # if a mine
                if self.tiles[x][y]["isMine"] == True:
                    self.correctFlagCount += 1
                self.flagCount += 1
                self.updateLabels()
            elif self.tiles[tile["coords"]["x"]][tile["coords"]["y"]]["probability"] == 0:
                #self.tiles[tile["coords"]["x"]][tile["coords"]["y"]]["button"].config(bg="green")
                pass
            elif self.tiles[tile["coords"]["x"]][tile["coords"]["y"]]["probability"] == -1:
                pass
                #self.tiles[tile["coords"]["x"]][tile["coords"]["y"]]["button"].config(bg="yellow")
        
        tile = min(borderedTiles, key=lambda x: x["probability"])
        # tile = random.choice(borderedTiles)
        if not self.onClick(tile):
            return
        
        # Call it again. Because we don't like loops. Praise Tail Recursion!
        self.solve()
                
        
    # Rule A: If a tile has the same number of adjacent mines as the number of unclicked tiles adjacent to it, then all of those tiles are mines.
    def ruleA(self):
        exposedTiles = []
        ruleApplied = False
        
        for x in range (0, SIZE_X):
            for y in range (0, SIZE_Y):
                if self.tiles[x][y]["state"] == STATE_CLICKED and self.tiles[x][y]["mines"] != 0:
                    exposedTiles.append(self.tiles[x][y])
        
        for tile in exposedTiles:
            neighbours = self.getNeighbors(tile["coords"]["x"], tile["coords"]["y"])
            nr_of_unflagged = len(list(filter(lambda x: x["state"] == STATE_DEFAULT, neighbours))) # Get unflagged tiles
            nr_of_flagged = len(list(filter(lambda x: x["state"] == STATE_FLAGGED, neighbours))) # Get flagged tiles
            # Apply rule
            if nr_of_unflagged == tile["mines"] - nr_of_flagged: 
                for neighbour in neighbours:
                    if neighbour["state"] == STATE_DEFAULT:
                        # Flag it
                        neighbour["probability"] = 100
                        self.hundredCount += 1
                        neighbour["button"].config(image = self.images["flag"])
                        neighbour["state"] = STATE_FLAGGED
                        neighbour["probability"] = 100
                        self.hundredCount += 1
                        neighbour["button"].unbind(BTN_CLICK)
                        # if a mine
                        if neighbour["isMine"] == True:
                            self.correctFlagCount += 1
                        self.flagCount += 1
                        self.updateLabels()
                        ruleApplied = True
            
        return ruleApplied # This means that the rule was applied at least once. So the function is worth repeating
    
    # Rule B: If a tile has the same number of adjacent squares that are flags, all of those tiles are safe.
    def ruleB(self):
        exposedTiles = []
        ruleApplied = False
        
        for x in range (0, SIZE_X):
            for y in range (0, SIZE_Y):
                if self.tiles[x][y]["state"] == STATE_CLICKED:
                    exposedTiles.append(self.tiles[x][y])
        
        for tile in exposedTiles:
            neighbours = self.getNeighbors(tile["coords"]["x"], tile["coords"]["y"])
            nr_of_flagged = self.mineCount(tile)
            if nr_of_flagged == tile["mines"]:
                for neighbour in neighbours:
                    if neighbour["state"] == STATE_DEFAULT:
                        # Click it
                        neighbour["probability"] = 0
                        if not self.onClick(neighbour):
                            return False
                        ruleApplied = True
        
        return ruleApplied
    
    # iterate through all tiles
    def ruleC(self):
        for x in range (0, SIZE_X):
            for y in range (0, SIZE_Y):
                if (self.tiles[x][y]["mines"] > 2):
                    count = 0
                    for neighbour in self.getNeighbors(x, y):
                        if neighbour["isBorder"] and self.count_state(neighbour, STATE_CLICKED) == 1:
                            count += 1
                    if count == self.count_state(self.tiles[x][y], STATE_DEFAULT) + self.count_state(self.tiles[x][y], STATE_FLAGGED):
                        probability = self.tiles[x][y]["mines"] / count * 100
                        for neighbour in self.getNeighbors(x, y):
                            neighbour["probability"] = probability
                        
                
    
    # Recursively generate all possible mine arrangements for bordered tiles
    def generate_arrangements(self, exposedTiles, borderedList, idx, arrangements, debug):
        if idx == 0:
            for tile in borderedList:
                x = tile["coords"]["x"]
                y = tile["coords"]["y"]
                self.tiles[x][y]["button"].config(bg = "SystemButtonFace")
                self.tk.update()
        x = borderedList[idx]["coords"]["x"]
        y = borderedList[idx]["coords"]["y"]
        if debug:
            for tile in borderedList:
                if tile["solver_mine"] == False and tile["solver_safe"] == False:
                    self.tiles[tile["coords"]["x"]][tile["coords"]["y"]]["button"].config(bg = "yellow")
                    self.tk.update()
        if self.can_be_mine(borderedList, borderedList[idx]):
            # Deep copy the current grid
            patternYes = copy.deepcopy(borderedList)
            patternYes[idx]["solver_mine"] = True
            if debug:
                print("patternYes")
                for tile in patternYes:
                    if tile["solver_mine"] == True or tile["probability"] == 100:
                        self.tiles[tile["coords"]["x"]][tile["coords"]["y"]]["button"].config(bg = "red")
                    elif tile["solver_safe"] == True:
                        self.tiles[tile["coords"]["x"]][tile["coords"]["y"]]["button"].config(bg = "green")
                    else:
                        self.tiles[tile["coords"]["x"]][tile["coords"]["y"]]["button"].config(bg = "blue")
                self.tk.update()
                print(patternYes[idx]["id"], "solver mine",patternYes[idx]["solver_mine"],"solver safe", patternYes[idx]["solver_safe"],"can be mine", self.can_be_mine(borderedList, patternYes[idx]))
                input("step patternYes")
            if idx < len(borderedList) - 1:
                self.generate_arrangements(exposedTiles, patternYes, idx + 1, arrangements, debug)
            else:
                if debug:
                    input("Bunu ekliyom okey mi patternYes")
                if self.validateArrangement(exposedTiles, patternYes):
                    """if debug:
                        for tile in patternYes:
                            if tile["solver_mine"] == True or tile["probability"] == 100:
                                self.tiles[tile["coords"]["x"]][tile["coords"]["y"]]["button"].config(bg = "red")
                            else:
                                self.tiles[tile["coords"]["x"]][tile["coords"]["y"]]["button"].config(bg = "blue")
                        self.tk.update()"""
                    arrangements.append(patternYes)
                if debug:
                    for x in range(0, SIZE_X):
                        for y in range(0, SIZE_Y):
                            self.tiles[x][y]["button"].config(bg = "SystemButtonFace")
        if self.can_be_non_mine(borderedList, borderedList[idx]):
            # Deep copy
            patternNo = copy.deepcopy(borderedList)
            patternNo[idx]["solver_safe"] = True
            if debug:
                print("patternNo")
                for tile in patternNo:
                    if tile["solver_mine"] == True or tile["probability"] == 100:
                        self.tiles[tile["coords"]["x"]][tile["coords"]["y"]]["button"].config(bg = "red")
                    elif tile["solver_safe"] == True:
                        self.tiles[tile["coords"]["x"]][tile["coords"]["y"]]["button"].config(bg = "green")
                    else:
                        self.tiles[tile["coords"]["x"]][tile["coords"]["y"]]["button"].config(bg = "blue")
                self.tk.update()
                print(patternNo[idx]["id"], "solver mine",patternNo[idx]["solver_mine"],"solver safe", patternNo[idx]["solver_safe"],"can be non mine", self.can_be_non_mine(borderedList, patternNo[idx]))
                input("step patternNo")
            if idx < len(borderedList) - 1:
                self.generate_arrangements(exposedTiles, patternNo, idx + 1, arrangements, debug)
            else:
                if debug:
                    print([{tile["id"]: (tile["solver_mine"], tile["solver_safe"])} for tile in patternNo])
                    inspect = input("Bunu ekliyom okey mi patternNo:" + borderedList[idx]["id"])
                    if inspect == "bruh":
                        for tile in patternNo:
                            if tile["solver_mine"] == True or tile["probability"] == 100:
                                self.tiles[tile["coords"]["x"]][tile["coords"]["y"]+4]["button"].config(bg = "red")
                            elif tile["solver_safe"] == True:
                                self.tiles[tile["coords"]["x"]][tile["coords"]["y"]+4]["button"].config(bg = "green")
                            else:
                                self.tiles[tile["coords"]["x"]][tile["coords"]["y"]+4]["button"].config(bg = "blue")
                        self.tk.update()
                        for tile in patternNo:
                            print("nominecount:", self.no_mine_count(patternNo, borderedList[idx]), idx, borderedList[idx])
                            print(tile["coords"]["x"], tile["coords"]["y"], tile["solver_mine"], tile["solver_safe"]) 
                        self.can_be_non_mine(borderedList, borderedList[idx])
                        input("go inspect")
                    #t.sleep(0.5)
                if self.validateArrangement(exposedTiles, patternNo):
                    """if debug:
                        for tile in patternNo:
                            if tile["solver_mine"] == True or tile["probability"] == 100:
                                self.tiles[tile["coords"]["x"]][tile["coords"]["y"]]["button"].config(bg = "red")
                            else:
                                self.tiles[tile["coords"]["x"]][tile["coords"]["y"]]["button"].config(bg = "blue")
                        self.tk.update()"""
                    arrangements.append(patternNo)
                if debug:
                    for x in range(0, SIZE_X):
                        for y in range(0, SIZE_Y):
                            self.tiles[x][y]["button"].config(bg = "SystemButtonFace")
            self.tk.update()
            
    def can_be_mine(self, borderedTiles, tile):
        
        """    if (j > 0) {
        if (mineGrid[i][j-1].open == true && mineGrid[i][j-1].neighbors <= mineCount(grid, i, j-1) + probabilityhundredCount(mineGrid, i, j-1)) {
            return false;
        }
    }"""
        for neighbour in self.getNeighbors(tile["coords"]["x"], tile["coords"]["y"]):
            if neighbour["state"] == STATE_CLICKED and neighbour["mines"] != 0:
                if neighbour["mines"] <= self.mineCount(neighbour) + self.probability_hundred_count(borderedTiles, neighbour):
                    tile["solver_mine"] = False
                    return False
        return True
    
    
    def can_be_non_mine(self, borderedTiles, tile):
        """    if (j > 0) {
        if (mineGrid[i][j-1].neighbors >= mineGrid[i][j-1].edgeCount - noMineCount(grid, i, j-1) - probabilityZeroCount(mineGrid, i, j-1)) {
            return false;
        }
        
        Neighbors is the "mines" variable
    }"""
        for neighbour in self.getNeighbors(tile["coords"]["x"], tile["coords"]["y"]):
            if neighbour["state"] == STATE_CLICKED and neighbour["mines"] != 0:
                tmp = self.count_state(neighbour, STATE_DEFAULT) + self.count_state(neighbour, STATE_FLAGGED) - self.no_mine_count(borderedTiles, neighbour)
                if neighbour["mines"] >= tmp:
                    return False
        return True
                
        
    def mineCount(self, tile):
        count = 0
        for neighbour in self.getNeighbors(tile["coords"]["x"], tile["coords"]["y"]):
            if neighbour["state"] == STATE_FLAGGED or neighbour["probability"] == 100:
                count += 1
        return count
    
    
    def no_mine_count(self, borderedTiles, tile):
        # Get the number of safe tiles placed by the solver around the tile
        count = 0
        for btile in borderedTiles:
            if self.armed:
                print("no mine count comparing", btile["id"],"and", tile["id"],", isnei", self.isNeighbour(btile, tile),"issafe", btile["solver_safe"])
            if self.isNeighbour(btile, tile) and btile["solver_safe"] == True:
                count += 1
        if self.armed:
            print("no mine count returning", count)
        return count
    
    def count_state(self, tile, state):
        count = 0
        for neighbour in self.getNeighbors(tile["coords"]["x"], tile["coords"]["y"]):
            if neighbour["state"] == state:
                count += 1
        return count
        
    def probability_hundred_count(self, borderedTiles, tile):
        # Get the number of mines placed by the solver around the tile
        count = 0
        for btile in borderedTiles:
            if self.isNeighbour(tile, btile) and btile["solver_mine"] == True:
                count += 1
        
        return count
    
    def validateArrangement(self, exposedTiles, arrangement):
        # Check if the arrangement is valid by checking if it satisfies the exposed tiles
        return True
        for numtile in exposedTiles:
            count = 0
            for neighbour in self.getNeighbors(numtile["coords"]["x"], numtile["coords"]["y"]):
                for tile in arrangement:
                    if [neighbour["coords"]["x"], neighbour["coords"]["y"]] == [tile["coords"]["x"], tile["coords"]["y"]]:
                        if tile["solver_mine"] == True:
                            count += 1
            if count != numtile["mines"] - self.count_state(numtile, STATE_FLAGGED):
                return False
        return True
        
    
    # Determine if two tiles are neighbours, i.e. they are adjacent
    def isNeighbour(self, tile1, tile2):
        x1, y1 = tile1["coords"]["x"], tile1["coords"]["y"]
        x2, y2 = tile2["coords"]["x"], tile2["coords"]["y"]
        
        # Check if the absolute difference in x and y coordinates is no greater than 1
        if abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1 and (x1 != x2 or y1 != y2):
            return True
        else:
            return False
        
### END OF CLASSES ###

def main():
    # create Tk instance
    window = Tk()
    # set program title
    window.title("Minesweeper")
    # create game instance
    minesweeper = Minesweeper(window)
    # run event loop
    window.mainloop()

if __name__ == "__main__":
    main()
