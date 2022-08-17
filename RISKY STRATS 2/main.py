import pygame
import os
import time
import json
import random
pygame.init()
screen = pygame.display.set_mode(size = (2560, 1440), flags = pygame.FULLSCREEN)
largerFont = pygame.font.Font(os.getcwd() + "\\fonts\\Helvetica Neue Medium Extended.ttf", 50)
font = pygame.font.Font(os.getcwd() + "\\fonts\\Helvetica Neue Medium Extended.ttf", 20)
smallerFont = pygame.font.Font(os.getcwd() + "\\fonts\\Helvetica Neue Medium Extended.ttf", 10)

#Nodes
playerFaction = 0
factionData = [["blue", 0, (128, 128, 255), {}, None], ["red", 0, (255, 0, 0), {}, None]]
loadedMap = []

#different types for each node
NODE_REGULAR = 0 #does nothing
NODE_FACTORY = 1 #generates 1 unit a step
NODE_FORT = 2 #adds 20% attack to the owner of a tile
NODE_CAPITOL = 3 #generates 2 units a step
NODE_ARTILLERY = 4 #adds 80% attack to all nearby tiles for the owner of the artillery
NODE_PLANT = 5 #makes all factories and capitols adjacent

#combat bonuses
BONUS_FORT = 0.2
BONUS_ARTILLERY = 0.5

#cost for every item in store
shop = {
    NODE_FACTORY: 500,
    NODE_FORT: 400,
    NODE_PLANT: 2500,
    NODE_ARTILLERY: 3000
}

shopNames = {
    NODE_FACTORY: "Factory",
    NODE_FORT: "Fort",
    NODE_PLANT: "Power Plant",
    NODE_ARTILLERY: "Artillery"
}

#different send amounts for each key
sends = {
    pygame.K_q: 26,
    pygame.K_e: 502,
    pygame.K_r: 2501,
    pygame.K_f: 50000
}

keybindTostring = {
    pygame.K_q: "Q",
    pygame.K_e: "E",
    pygame.K_r: "R",
    pygame.K_f: "F"
}

def mergeLists(list1, list2): #merging function 
    counter1 = 0
    counter2 = 0
    newList = []

    lenList1 = len(list1)
    lenList2 = len(list2)
    cond = True

    while cond:
        item1 = list1[counter1] #god tier code
        item2 = list2[counter2]
        if item1.current < item2.current:
            newList.append(item1)
            counter1 += 1

            if counter1 == lenList1:
                for i in range(counter2, lenList2, 1):
                    newList.append(list2[i])

                cond = False

        else:
            newList.append(item2)
            counter2 += 1

            if counter2 == lenList2:
                for i in range(counter1, lenList1, 1):
                    newList.append(list1[i])

                cond = False

    return newList

def troopSort(troopTable): #merge sort function designed to sort troops based on progress
    if len(troopTable) <= 1: #already sorted
        return troopTable
    
    mergeCache = []
    for troop in troopTable:
        mergeCache.append([troop])

    while len(mergeCache) > 1:
        newMergeCache = []
        mergeLen = len(mergeCache)
        for i in range(0, mergeLen, 2):
            idxA = i
            idxB = i + 1

            if idxB == mergeLen: #odd number merge
                newMergeCache[len(newMergeCache) - 1] = mergeLists(newMergeCache[len(newMergeCache) - 1], mergeCache[idxA])
            else: #regular merge
                newMergeCache.append(mergeLists(mergeCache[idxA], mergeCache[idxB]))

        mergeCache = newMergeCache

    return mergeCache[0]

class testClass:
    def __init__(self):
        self.current = 1

troopSort([testClass])

def valueBoundary(a, b, v):
    if a > b:
        c = a
        a = b
        b = c

    return a <= v and v <= b

class Node:
    def __init__(self, x, y, owner, troops, nodeType, ID):
        self.x = x
        self.y = y
        self.owner = owner
        self.connections = [] #what other nodes the node is connected to
        self.connectors = {} #connector objects corresponding to connections to other nodes (used for navigating)
        self.troops = {owner: troops}
        self.safe = True
        self.id = ID
        self.nodeType = nodeType
        self.selected = False
        self.hovering = False
        factionData[owner][1] += 1

    def drawNode(self):
        #drawing troop numbers
        occupants = 0
        offset = 40
        for idx in self.troops:
            troops = self.troops[idx]
            text = font.render(str(troops), True, factionData[idx][2])
            textRect = text.get_rect()
            textRect.center = (self.x, self.y - offset)
            offset += 20
            screen.blit(text, textRect)
            occupants += 1

        self.safe = occupants == 1
            
        #drawing the node
        nodeType = self.nodeType
        nodeColor = factionData[self.owner][2]
        if self.selected:
            nodeColor = (255, 255, 255)
        elif self.hovering or not self.safe:
            nodeColor = (200, 200, 200)
            
        if nodeType == NODE_REGULAR: #circle
            pygame.draw.circle(surface = screen, radius = 20, color = nodeColor, center = (self.x, self.y))
        elif nodeType == NODE_FACTORY: #square
            pygame.draw.rect(surface = screen, color = nodeColor, rect = pygame.Rect(self.x - 15, self.y - 15, 30, 30))
        elif nodeType == NODE_FORT: #hexagon
            radius = 18
            half = radius / 2.3
            hexagon = [
                (self.x - radius, self.y), (self.x - half, self.y - radius), (self.x + half, self.y - radius),
                (self.x + radius, self.y), (self.x + half, self.y + radius), (self.x - half, self.y + radius)
            ]
            pygame.draw.polygon(surface = screen, color = nodeColor, points = hexagon)
        elif nodeType == NODE_CAPITOL: #diamond
            radius = 18
            diamond = [
                (self.x - radius, self.y), (self.x, self.y - radius), (self.x + radius, self.y), (self.x, self.y + radius)
            ]
            pygame.draw.polygon(surface = screen, color = nodeColor, points = diamond)
        elif nodeType == NODE_ARTILLERY: #triangle
            triangle = [(self.x - 20, self.y - 18), (self.x, self.y + 18), (self.x + 20, self.y - 18)]
            pygame.draw.polygon(surface = screen, color = nodeColor, points = triangle)

        elif nodeType == NODE_PLANT: #target
            pygame.draw.circle(surface = screen, radius = 10, color = nodeColor, center = (self.x, self.y))
            pygame.draw.circle(surface = screen, radius = 20, color = nodeColor, center = (self.x, self.y), width = 5)

    def gameStep(self):
        #adding troops to troop producing tiles
        if self.safe:
            capitol = self.nodeType == NODE_CAPITOL
            factory = self.nodeType == NODE_FACTORY

            if capitol or factory:
                increase = 0
                if capitol:
                    increase = 2
                else:
                    increase = 1

                for connection in self.connections:
                    if connection.owner == self.owner and connection.nodeType == NODE_PLANT:
                        increase += 2

                self.troops[self.owner] += increase

        else: #combat system
            strength =  {}
            totalTroops = 0
            fIdx = -1
            for faction in factionData: #getting all the strength for each faction contesting the tile
                fIdx += 1
                totalTroops += self.troops[fIdx]
                strength[fIdx] = self.troops[fIdx]

            for node in self.connections: #finding all artillery tiles
                if node.owner in strength and node.nodeType == NODE_ARTILLERY:
                    totalTroops += self.troops[node.owner] * BONUS_ARTILLERY #generate virtual troops for the artillery piece
                    strength[node.owner] += self.troops[node.owner] * BONUS_ARTILLERY

            totalTroops += (self.nodeType == NODE_FORT and self.troops[self.owner] * BONUS_FORT) or 0 #virtual troops for fort bonus
            strength[self.owner] += (self.nodeType == NODE_FORT and self.troops[self.owner] * BONUS_FORT) or 0 #fort bonus

            
            bloodiness = totalTroops ** 0.5 #maximum loss that can happen
            remainingFactions = []

            for faction in strength:
                if self.troops[faction] <= 0:
                    self.troops.pop(faction) #bug fix
                else:
                    troopCount = strength[faction]
                    proportion = self.troops[faction] / troopCount
                    loss = 1 - troopCount / totalTroops
                    loss = round(loss * proportion * bloodiness)
                    self.troops[faction] -= loss
                    if self.troops[faction] <= 0: #faction eliminated from battle
                        self.troops.pop(faction)
                    else:
                        remainingFactions.append(faction)

            #checking if the battle has been completed
            if len(remainingFactions) == 1:
                self.owner = remainingFactions[0]
                self.safe = True
            elif len(remainingFactions) == 0: #tiebreaker
                self.troops[self.owner] = 1

    def buyItem(self, idx):
        if self.safe:
            cost = shop[idx]
            owner = self.owner
            if self.troops[owner] >= cost:
                self.troops[owner] -= cost
                self.nodeType = idx
        
class Connection:
    def __init__(self, node1, node2, length):
        self.node1 = node1
        self.node2 = node2
        self.length = length
        self.leftChannel = [] #node1 -> node2
        self.rightChannel = [] #node2 -> node1
        node1.connections.append(node2)
        node1.connectors[node2.id] = self
        node2.connections.append(node1)
        node2.connectors[node1.id] = self

    def gameStep(self, dt): #deal with all mobile troops within connectors

        idxTable = [] #indexes of mobile troops to remove after step
        idx = -1
        for mobileTroop in self.leftChannel:
            idx += 1
            if mobileTroop.update:
                mobileTroop.current += dt * mobileTroop.direction
                mobileTroop.update = False
                #interpolation variables for the purposes of display troop movement progress
                interpolateX = self.node1.x - self.node2.x
                interpolateY = self.node1.y - self.node2.y
                progress = max(min(mobileTroop.current / self.length, 1), 0)
                troopPosition = (self.node2.x + interpolateX * progress, self.node2.y + interpolateY * progress)
                pygame.draw.circle(surface = screen, radius = 10, color = factionData[mobileTroop.owner][2], center = troopPosition)
                text = font.render(str(mobileTroop.count), True, factionData[mobileTroop.owner][2])
                textRect = text.get_rect()
                textRect.center = (troopPosition[0], troopPosition[1] - 40)
                mobileTroop.x = troopPosition[0]
                mobileTroop.y = troopPosition[1]
                screen.blit(text, textRect)

                if progress == 1: #progress to the next node
                    mobileTroop.travel += mobileTroop.direction
                    idxTable.append(idx)
                    if mobileTroop.travel == 0 or mobileTroop.travel == len(mobileTroop.path): #mobileTroop has successfully completed its path
                        ttable = mobileTroop.path[min(mobileTroop.travel, len(mobileTroop.path) - 1)].troops
                        if not mobileTroop.owner in ttable:
                            ttable[mobileTroop.owner] = 0

                        ttable[mobileTroop.owner] += mobileTroop.count
                    else:
                        currentNode = mobileTroop.path[mobileTroop.travel - mobileTroop.direction]
                        headingNode = mobileTroop.path[mobileTroop.travel]

                        connector = currentNode.connectors[headingNode.id]
                        mobileTroop.current = 0
                        if connector.node2 == currentNode:
                            connector.leftChannel.append(mobileTroop)
                        else:
                            connector.rightChannel.append(mobileTroop)
                elif progress == 0: #retreated successfully
                    idxTable.append(idx)
                    ttable = mobileTroop.path[min(mobileTroop.travel - 1, len(mobileTroop.path) - 1)].troops
                    if not mobileTroop.owner in ttable:
                        ttable[mobileTroop.owner] = 0

                    ttable[mobileTroop.owner] += mobileTroop.count

        idx = len(idxTable)
        while idx != 0:
            idx -= 1
            self.leftChannel.pop(idxTable[idx])

        idxTable = [] #indexes of mobile troops to remove after step
        idx = -1
        for mobileTroop in self.rightChannel:
            idx += 1
            if mobileTroop.update:
                mobileTroop.current += dt * mobileTroop.direction
                mobileTroop.update = False
                #interpolation variables for the purposes of display troop movement progress
                interpolateX = self.node2.x - self.node1.x
                interpolateY = self.node2.y - self.node1.y
                progress = max(min(mobileTroop.current / self.length, 1), 0)
                troopPosition = (self.node1.x + interpolateX * progress, self.node1.y + interpolateY * progress)
                pygame.draw.circle(surface = screen, radius = 10, color = factionData[mobileTroop.owner][2], center = troopPosition)
                text = font.render(str(mobileTroop.count), True, factionData[mobileTroop.owner][2])
                textRect = text.get_rect()
                textRect.center = (troopPosition[0], troopPosition[1] - 40)
                screen.blit(text, textRect)
                mobileTroop.x = troopPosition[0]
                mobileTroop.y = troopPosition[1]

                if progress == 1: #progress to the next node
                    mobileTroop.travel += mobileTroop.direction
                    idxTable.append(idx)
                    if mobileTroop.travel == 0 or mobileTroop.travel == len(mobileTroop.path): #mobileTroop has successfully completed its path
                        ttable = mobileTroop.path[min(mobileTroop.travel, len(mobileTroop.path) - 1)].troops
                        if not mobileTroop.owner in ttable:
                            ttable[mobileTroop.owner] = 0

                        ttable[mobileTroop.owner] += mobileTroop.count
                    else:
                        currentNode = mobileTroop.path[mobileTroop.travel - mobileTroop.direction]
                        headingNode = mobileTroop.path[mobileTroop.travel]
                        connector = currentNode.connectors[headingNode.id]
                        mobileTroop.current = 0
                        if connector.node2 == currentNode:
                            connector.leftChannel.append(mobileTroop)
                        else:
                            connector.rightChannel.append(mobileTroop)

                elif progress == 0:
                    idxTable.append(idx)
                    ttable = mobileTroop.path[min(mobileTroop.travel - 1, len(mobileTroop.path) - 1)].troops
                    if not mobileTroop.owner in ttable:
                        ttable[mobileTroop.owner] = 0

                    ttable[mobileTroop.owner] += mobileTroop.count

        idx = len(idxTable)
        while idx != 0:
            idx -= 1
            self.rightChannel.pop(idxTable[idx])

        #mfw i didn't plan this in the game architecture and i'm now making a bad patch job
        if len(self.leftChannel) > 0 and len(self.rightChannel) > 0:
            leftSorted = troopSort(self.leftChannel)
            rightSorted = troopSort(self.rightChannel)

            furthestTroop = leftSorted[-1]
            idx = -1
            while len(rightSorted) * -1 - 1 != idx:
                troop = rightSorted[idx]
                if abs(furthestTroop.current - self.length + troop.current) < 0.5 and troop.direction == 1 and furthestTroop.direction == 1: #collision detected
                    if troop.owner != furthestTroop.owner: #enemy troop collision
                        if troop.count > furthestTroop.count: #leftChannel troop is sent back
                            furthestTroop.direction *= -1
                            #furthestTroop.current = self.length * 0.9 - troop.current
                        else: #rightChannel troop is sent back
                            troop.direction *= -1
                            #troop.current = self.length * 0.9 - furthestTroop.current
                    idx -= 1
                else:
                    break
            

class MobileTroop: #making a troop class so troops can find their path and move accordingly
    def __init__(self, owner, count):
        self.owner = owner
        self.count = count
        self.direction = 1 #determines whether a mobile troop is retreating or advancing
        self.current = 0 #current progress on the path
        self.travel = 1 #how far troop is in the path
        self.update = True #preventing double stepping when updating troop movement
        self.x = 0
        self.y = 0
        self.path = []

    def calculatePath(self, current, target): #i love pathfinding!
        if current.id != target.id:
            iterationTable = [current]
            pathMap = {}
            iteration = 0
            iterate = True
            while iterate:
                iterate = False #will be toggled to true if no dead end was found
                iteration += 1 #increase the distance
                newIterationTable = []
                for node in iterationTable:
                    for connected in node.connections:
                        if connected.id == target.id: #arrived at target
                            pathMap[connected.id] = iteration
                            self.path.append(target)
                            currentNode = target
                            #print(f"EXPECTED LENGTH: {iteration}") #legacy debug code
                            for i in range(iteration):
                                for backtrack in currentNode.connections: #checking all neighboring nodes to the currentNode
                                    if backtrack.id in pathMap:
                                        if pathMap[backtrack.id] < pathMap[currentNode.id]: #its a valid backtrack node (real)
                                            self.path.append(backtrack)
                                            currentNode = backtrack
                                            break

                            self.path.append(current)
                            self.path.reverse()

                            connector = current.connectors[currentNode.id]
                            if connector.node1 == currentNode:
                                connector.leftChannel.append(self)
                            else:
                                connector.rightChannel.append(self)

                            current.troops[self.owner] -= self.count
                            return
                        elif connected.owner == self.owner and connected.safe and not connected.id in pathMap: #passing through friendly territory
                            newIterationTable.append(connected)
                            iterate = True
                            pathMap[connected.id] = iteration

                iterationTable = newIterationTable #replacing the iteration table

class AIController: #Code object which can autonomously control a specified faction with specified competency
    def __init__(self, faction, difficulty):
        self.faction = faction
        self.difficulty = difficulty
        self.objectives = {}
        self.troopTransit = {}

    def gameStep(self):
        data = factionData[self.faction]
        nodes = data[3]

        nodeGarrison = {} #required amount of troops required to defend each node
        nodeMultiplier = {} #combat multiplier for defender of node
        attackStrength = {} #base troop strength for the largest attacker of a node
        attackMultiplier = {} #combat multiplier for greatest enemy faction per node
        targets = {} #neighbours that are not sufficiently defended against a possible attack

        for idx in nodes:
            node = nodes[idx]
            defenseStrength = node.troops[self.faction] #base defense of the node
            defenseMultiplier = 1 + (node.nodeType == NODE_FORT * BONUS_FORT) #how much extra strength the defending node gets from bonuses
            threats = {} #all neighbouring factions that exist
            biggestThreat = 0 #how many troops the largest neighbouring faction has
            bThreatMultiplier = 1
            threatMultiplier = {} #combat bonuses each enemy faction gets on the node
            friendlyNeighbours = [] #nearby friendly nodes to collaborate with regarding the defense

            for neighbour in node.connections: #calculating the strength of all neighbouring nodes
                if neighbour.owner == self.faction:
                    defenseMultiplier += (neighbour.nodeType == NODE_ARTILLERY) * BONUS_ARTILLERY #checking artillery bonus
                    friendlyNeighbours.append(neighbour)
                else:
                    if not neighbour.owner in threats:
                        threats[neighbour.owner] = 0
                        threatMultiplier[neighbour.owner] = 1

                    threatMultiplier[neighbour.owner] += (neighbour.nodeType == NODE_ARTILLERY) * BONUS_ARTILLERY
                    ftroops = (self.faction in neighbour.troops and neighbour.troops[self.faction]) or 0
                    threats[neighbour.owner] += max(ftroops, 0)

            if node.safe:
                for jdx in node.connectors: #checking for possible inbound threats
                    connection = node.connectors[jdx]

                    otherNode = (connection.node2 == node and connection.node1) or connection.node2
                    if otherNode.owner != self.faction:
                        outbound = (connection.node2 == node and connection.leftChannel) or connection.rightChannel #outbound
                        inbound = (connection.node2 == node and connection.rightChannel) or connection.leftChannel #inbound

                        boundAttack = 0
                        boundDefense = 0
                        
                        for troop in outbound: #check who the mobiletroop belongs to
                            if troop.owner == self.faction:
                                boundAttack += troop.count
                            else:
                                boundDefense += troop.count

                        for troop in inbound:
                            if troop.owner == self.faction:
                                boundDefense += troop.count
                            else:
                                boundAttack += troop.count

                        try:
                            threats[otherNode.owner] = max(0, boundDefense + otherNode.troops[otherNode.owner] - boundAttack)
                        except:
                            pass

                for faction in threats: #find which faction poses the greatest danger to the node
                    strength = threats[faction] * threatMultiplier[faction]
                    if strength > biggestThreat:
                        biggestThreat = strength
                        bThreatMultiplier = threatMultiplier[faction]
                        attackStrength[idx] = threats[faction]

                nodeGarrison[idx] = (defenseStrength * defenseMultiplier - biggestThreat) / defenseMultiplier
                nodeMultiplier[idx] = defenseMultiplier
                attackMultiplier[idx] = bThreatMultiplier
            else: #retreat from all losing battles
                for faction in node.troops:
                    if faction != self.faction:
                        if not faction in threatMultiplier:
                            threatMultiplier[faction] = 1
                            
                        strength = node.troops[faction] * threatMultiplier[faction]
                        biggestThreat = max(strength, biggestThreat)

                if biggestThreat > defenseStrength * defenseMultiplier: #retreat from losing battle
                    if node.troops[self.faction] > 1 and len(friendlyNeighbours) > 0:
                        retreatingTroop = MobileTroop(self.faction, node.troops[self.faction] - 1)
                        retreatingTroop.calculatePath(node, friendlyNeighbours[0])

        for idx in nodeGarrison: #moving troops around
            node = nodes[idx]
            netValue = nodeGarrison[idx]
            if netValue < 0: #node is not properly defended
                #find various buildings which may be constructed to recitify the issue
                if not node.nodeType == NODE_FORT and node.troops[self.faction] > 2400:
                    node.troops[self.faction] -= 400 #it is economical to turn the node into a fort
                    node.nodeType = NODE_FORT
                    nodeMultiplier[idx] += 0.2
                    nodeGarrison[idx] = (node.troops[self.faction] * nodeMultiplier[idx] - attackStrength[idx] * attackMultiplier[idx]) / nodeMultiplier[idx] #recalculating the amount of troops needed to defend the node

                for neighbour in node.connections:
                    if neighbour.owner == self.faction:
                        if neighbour.safe and neighbour.nodeType != NODE_ARTILLERY and node.troops[self.faction] > 3000:
                            if True: #this is causing me too many headaches so i've patched it out
                                continue
                            
                            netMobilize = nodeGarrison[neighbour.id] - 3000
                            if netMobilize > 0: #purchase the artillery piece
                                neighbour.nodeType = NODE_ARTILLERY
                                neighbour.troops[self.faction] -= 3000
                                for bordering in neighbour.connections: #update the nodeGarrison for all neighbours of the neighbour
                                    if bordering.owner == self.faction:
                                        nodeMultiplier[bordering.id] += 0.5
                                        nodeGarrison[bordering.id] = (bordering.troops[self.faction] * nodeMultiplier[bordering.id] - attackStrength[bordering.id] * attackMultiplier[bordering.id]) / nodeMultiplier[bordering.id]
                                nodeGarrison[neighbour.id] = (neighbour.troops[self.faction] * nodeMultiplier[neighbour.id] - attackStrength[neighbour.id] * attackMultiplier[neighbour.id]) / nodeMultiplier[neighbour.id]

            elif netValue > 1: #this node could potentially be used to attack another node
                leastResistance = None #always choose the node with the least resistance to attack
                leastStrength = 0
                leastTroops = 0
                
                for neighbour in node.connections: #get defense multiplier for each potential target
                    if neighbour.safe and neighbour.owner != self.faction:
                        multiplier = (neighbour.nodeType == NODE_FORT and 1.2) or 1
                        amultiplier = 1
                        for bordering in neighbour.connections:
                            if bordering.owner == neighbour.owner: #defense multiplier
                                multiplier += (bordering.nodeType == NODE_ARTILLERY) * 0.5
                            elif bordering.owner == self.faction: #attack multiplier
                                amultiplier += (bordering.nodeType == NODE_ARTILLERY) * 0.5

                        dstrength = neighbour.troops[neighbour.owner] * multiplier
                        astrength = netValue * amultiplier

                        stronk = astrength - dstrength

                        if stronk > 0:
                            if leastStrength == None or stronk > leastStrength:
                                leastStrength = astrength - dstrength
                                leastResistance = neighbour

                if leastResistance != None: #preparing to attack an enemy node
                    
                    attackingTroop = MobileTroop(self.faction, min(int(nodeGarrison[node.id] - 1), node.troops[self.faction] - 1))
                    attackingTroop.calculatePath(node, leastResistance)

            
#Custom graphical object designed for inputs
textBoxes = []
selectingTextBox = False
selectedTextBox = None
class TextBox:
    def __init__(self, rectColor, textColor, rect, text, unfocused):
        self.rect = rect
        self.rectColor = rectColor
        self.textColor = textColor
        self.text = text
        self.unfocused = unfocused #binding an event when the textbox is unfocused
        textBoxes.append(self)

    def render(self): #draw all elements
        pygame.draw.rect(surface = screen, color = self.rectColor, rect = self.rect)
        surface = font.render(self.text, True, self.textColor)
        textRect = surface.get_rect()
        textRect.center = ((self.rect.left + self.rect.right) / 2, (self.rect.top + self.rect.bottom) / 2)
        screen.blit(surface, textRect)

#map data loading function
def loadMap(mapName):
    #Locating the file and reading from the file
    directory = os.getcwd()
    file = open(f"{directory}\\mapdata\\{mapName}", "r")
    serial = json.loads(file.read())
    mapData = {"nodes": [], "connections": []}
    ID = -1

    for i in serial["nodes"]:
        ID += 1
        mapData["nodes"].append(Node(i[0], i[1], i[2], i[3], i[4], ID))

    for i in serial["connections"]:
        mapData["connections"].append(Connection(mapData["nodes"][i[0]], mapData["nodes"][i[1]], i[2]))
         
    file.close()
    return mapData

FPSDELAY = 1 / 60
def drawMap(mapData):
    for connection in mapData["connections"]:
        for troop in connection.leftChannel:
            troop.update = True

        for troop in connection.rightChannel:
            troop.update = True
            
    for connection in mapData["connections"]:
        node1 = connection.node1
        node2 = connection.node2
        line = pygame.draw.line(surface = screen, color = (255, 255, 255), start_pos = (node1.x, node1.y), end_pos = (node2.x, node2.y), width = 5)
        connection.gameStep(FPSDELAY)
        
    for node in mapData["nodes"]:
        node.drawNode()


shopSizeX = 150
shopSizeY = 100
def drawShop(position): #making the shop gui
    pygame.draw.rect(surface = screen, color = factionData[playerFaction][2], rect = pygame.Rect((position[0], position[1]), (shopSizeX, shopSizeY)))

    place = position[1]
    for item in shop:
        text = smallerFont.render(f"{shopNames[item]}: {shop[item]}", True, (255, 255, 255))
        textRect = text.get_rect()
        textRect.center = (position[0] + shopSizeX / 2, place + 12.5)
        screen.blit(text, textRect)
        place += 25
    
        

#loading all map files onto the mapdata list
mapData = []
for root, dirs, files in os.walk(os.getcwd() + "\\mapdata"):
    for file in files:
        mapData.append(file)
    
updates = []
iTime = time.time()
fTime = time.time()

mouseDown = False
startPos = (0, 0)
endPos = (0, 0)
hoveringNode = None

selectedNodes = []
shopVisible = False
shopNode = None
shopPosition = (0,0)

clicky = {}

i = 345
def MAKEBUTTONSTOP(b, index): #creates a textbox which can change the amount of troops
    def eventResponse(self): #function which is invoked when the textbox is unselected
        try:
            sends[b] = int(self.text) #setting the send amount to the text of the textbox
        except:
            pass
    tObj = TextBox(factionData[playerFaction][0], (255, 255, 255), pygame.Rect(index, 600, 140, 50), str(sends[bind]), eventResponse)
    
for bind in sends: #creating the textboxes :D
    MAKEBUTTONSTOP(bind, i)
    i += 150
    

def gameMain():#main map loader
    loadedMap = loadMap(mapData[random.randint(1, len(mapData)) - 1]) #setting up the game

    AIControllers = [] #creating necessary AIControllers
    for faction in range(len(factionData)):
        if faction != playerFaction:
            AIControllers.append(AIController(faction, 2))
        
    updates = []
    iTime = time.time()
    fTime = time.time()

    mouseDown = False
    startPos = (0, 0)
    endPos = (0, 0)
    hoveringNode = None

    selectedNodes = []
    shopVisible = False
    shopNode = None
    shopPosition = (0,0)

    selectedTextBox = None
    selectingTextBox = False

    clicky = {}

    i = 345
    
    while True: #main game loop
        t = time.time()
        if t - iTime >= 0.2: #game tick
            
            for node in loadedMap["nodes"]: #adding troops to nodes
                node.gameStep()
                    
            iTime = t

        if t - fTime >= FPSDELAY: #render tick
            screen.fill(0)
            if mouseDown: #selection rectangle rendering
                position = pygame.mouse.get_pos()
                selectRect = pygame.draw.rect(surface = screen, color = (255, 255, 255), rect = pygame.Rect(startPos, (position[0] - startPos[0], position[1] - startPos[1])), width = 5)
                
            drawMap(loadedMap)
            if shopVisible:
                drawShop(shopPosition)

            for tb in textBoxes:
                tb.render()

            index = 345
            for bind in sends: #displaying the textlabels corresponding to the bind textbox
                backdrop = pygame.Rect(index, 545, 140, 50)
                pygame.draw.rect(surface = screen, color = factionData[playerFaction][0], rect = backdrop)
                surface = font.render(keybindTostring[bind], True, (255, 255, 255))
                textRect = surface.get_rect()
                textRect.center = ((backdrop.left + backdrop.right) / 2, (backdrop.top + backdrop.bottom) / 2)
                screen.blit(surface, textRect)
                index += 150

            pygame.display.update()

            fTime = t

        #display which node the player is hovering their mouse over
        mousePos = pygame.mouse.get_pos()
        if hoveringNode != None:
            hoveringNode.hovering = False
        hoveringNode = None

        for faction in factionData: #keeping track of what nodes are owned by certain faction
            faction[3] = {}

        aliveFactions = {}
            
        for node in loadedMap["nodes"]:
            if valueBoundary(node.x - 20, node.x + 20, mousePos[0]) and valueBoundary(node.y - 20, node.y + 20, mousePos[1]):
                hoveringNode = node
                hoveringNode.hovering = True

            factionData[node.owner][3][node.id] = node
            aliveFactions[node.owner] = True

        if len(aliveFactions) == 1 and playerFaction in aliveFactions: #a winner is you
            print("a winner is you")
            return 2
        elif not playerFaction in aliveFactions: # a loser is you
            print("a loser is you")
            return 3

        for controller in AIControllers:
            controller.gameStep()
            
        for event in pygame.event.get(): #determines whether to send units or not
            if event.type == pygame.MOUSEBUTTONDOWN: #begin drawing rectangle
                if event.button == 1:
                    startPos = event.pos
                    mouseDown = True
                    if shopVisible:
                        shopVisible = valueBoundary(shopPosition[0], shopPosition[0] + shopSizeX, mousePos[0]) and valueBoundary(shopPosition[1], shopPosition[1] + shopSizeY, mousePos[1])
                        if shopVisible: #finding out which item the player is going to buy
                            msCords = mousePos[1] - shopPosition[1]
                            if msCords <= 50:
                                if msCords <= 25: #factory
                                    shopNode.buyItem(NODE_FACTORY)
                                else: #fort
                                    shopNode.buyItem(NODE_FORT)
                            else:
                                if msCords <= 75: #power plant
                                    shopNode.buyItem(NODE_PLANT)
                                else: #artillery
                                    shopNode.buyItem(NODE_ARTILLERY)

                    selectingTextBox = False
                    if selectedTextBox != None:
                        selectedTextBox.unfocused(selectedTextBox) #starting an event
                        
                    selectedTextBox = None
                    for tb in textBoxes:
                        selectingTextBox = valueBoundary(tb.rect.left, tb.rect.right, mousePos[0]) and valueBoundary(tb.rect.top, tb.rect.bottom, mousePos[1])
                        if selectingTextBox:
                            selectedTextBox = tb
                            break
                elif event.button == 3:
                    shopVisible = hoveringNode != None and hoveringNode.owner == playerFaction
                    if shopVisible:
                        shopNode = hoveringNode
                        shopPosition = event.pos
            elif event.type == pygame.MOUSEBUTTONUP: #find all rectangles that need to be selected
                if event.button == 1:
                    endPos = event.pos
                    mouseDown = False
                    for node in selectedNodes: #unselecting old nodes
                        node.selected = False

                    selectedNodes.clear()

                    for node in loadedMap["nodes"]:
                        if valueBoundary(startPos[0], endPos[0], node.x) and valueBoundary(startPos[1], endPos[1], node.y) and playerFaction in node.troops:
                            node.selected = True
                            selectedNodes.append(node)

            elif event.type == pygame.KEYDOWN: #type into textbox if textbox is selected, otherwise do regular inputs
                if selectingTextBox:
                    if event.key == pygame.K_BACKSPACE:
                        selectedTextBox.text = selectedTextBox.text[0:len(selectedTextBox.text) - 1]
                    elif event.key == pygame.K_RETURN:
                        selectedTextBox.unfocused(selectedTextBox)
                        selectedTextBox = None
                        selectingTextBox = False
                    else:
                        selectedTextBox.text += event.unicode
                else:
                    if event.key == pygame.K_ESCAPE:
                        return 1
                    else:
                        clicky[event.key] = True
                        if event.key in sends and hoveringNode != None:
                            for node in selectedNodes: #going through all selected nodes
                                if playerFaction in node.troops: #node may be conquered while it is selected
                                    sendAmount = min(node.troops[playerFaction] - 1, sends[event.key])
                                    if sendAmount > 0: #creating the troop object and sending it on a journey
                                        troopObject = MobileTroop(playerFaction, sendAmount)
                                        troopObject.calculatePath(node, hoveringNode)
                                    
            elif event.type == pygame.KEYUP:
                if event.key in clicky:
                    clicky.pop(event.key)
                    
                if event.key == pygame.K_b:
                    mousePos = pygame.mouse.get_pos()
                    for connection in loadedMap["connections"]: #finding all the mobiletroops
                        for troop in connection.leftChannel:
                            if valueBoundary(startPos[0], mousePos[0], troop.x) and valueBoundary(startPos[1], mousePos[1], troop.y):
                                troop.direction *= -1

                        for troop in connection.rightChannel:
                            if valueBoundary(startPos[0], mousePos[0], troop.x) and valueBoundary(startPos[1], mousePos[1], troop.y):
                                troop.direction *= -1
#title screen and tutorial
def titleScreen():
    selectedOption = 0
    loadedOption = None
    optionText = ["Play", "Tutorial", "About", "Quit"]
    tutorialText = [
        "Control all nodes on the map to win",
        "You control the blue faction",
        "To select nodes, hold left click and drag the mouse over an area",
        "To send troops, hover your mouse over a node and press 'Q', 'E', 'R', or 'F'",
        "To open up the shop, hover over a node and right click",
        "To buy a building, click the option and ensure the node has enough troops for it",
        "To make troops retreat, drag select an area and press 'B'",
        "To return to the title screen, press 'ESC'"
    ]
    aboutText = [
        "Version 0.5.0",
        "Risky Strats Python Edition by Carlton Qian",
        "ICS201, Ms. Wong",
    ]

    iTime = time.time()
    
    while True:
        if time.time() - iTime >= FPSDELAY: #rerender the title screen
            screen.fill(0)
            title = largerFont.render("Risky Strats: Python Edition", True, (255, 255, 255))
            titleSize = largerFont.size("Risky Strats: Python Edition")
            titleRect = title.get_rect()
            titleRect.center = (titleSize[0] / 2 + 30, titleSize[1] / 2 + 30)
            screen.blit(title, titleRect)

            starter = 450
            for i in range(len(optionText)): #rendering all the title screen options
                option = optionText[i]
                text = largerFont.render(option, True, (selectedOption == i and (255, 0, 0)) or (255, 255, 255))
                textSize = largerFont.size(option)
                textRect = text.get_rect()
                textRect.center = (textSize[0] / 2 + 30, starter)
                screen.blit(text, textRect)
                starter += 60

            if loadedOption != None:
                starter = 450
                textTable = aboutText
                if loadedOption: #switch between tutorial and about screen
                    textTable = tutorialText

                for line in textTable:
                    text = font.render(line, True, (255, 255, 255))
                    textSize = font.size(line)
                    textRect = text.get_rect()
                    textRect.center = (textSize[0] / 2 + 350, starter)
                    screen.blit(text, textRect)
                    starter += 30

            pygame.display.update() 
            
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: #leaving the game
                    pygame.quit()
                elif event.key == pygame.K_RETURN: #selecting option
                    if selectedOption < 2:
                        if selectedOption < 1: #play
                            return
                        else: #tutorial
                            loadedOption = True
                    else:
                        if selectedOption < 3: #about
                            loadedOption = False
                        else: #quit
                            pygame.quit()
                elif event.key == pygame.K_UP: #control keys
                    selectedOption = max(selectedOption - 1, 0)
                elif event.key == pygame.K_DOWN:
                    selectedOption = min(selectedOption + 1, len(optionText) - 1)

while True: #omg gam so simple!!!!!
    titleScreen()
    exitCode = gameMain()
    if exitCode == 2: #a winner is you
        screen.fill(0)
        text = largerFont.render("You win!", True, (255, 255, 255))
        textRect = text.get_rect()
        textRect.center = (640, 360)
        screen.blit(text, textRect)

        text = font.render("Press any key to continue", True, (255, 255, 255))
        textRect = text.get_rect()
        textRect.center = (640, 410)
        screen.blit(text, textRect)

        pygame.display.update()

        cond = True
        while cond: #awaiting input from the user
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    cond = False
                    break
                
    elif exitCode == 3: #a loser is you
        screen.fill(0)
        text = largerFont.render("You lose!", True, (255, 255, 255))
        textRect = text.get_rect()
        textRect.center = (640, 360)
        screen.blit(text, textRect)

        text = font.render("Press any key to continue", True, (255, 255, 255))
        textRect = text.get_rect()
        textRect.center = (640, 410)
        screen.blit(text, textRect)

        pygame.display.update()

        cond = True
        while cond: #awaiting input from the user
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    cond = False
                    break
                
