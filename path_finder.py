import string
import sys
import copy
import math
import time
ti = time.time()

dim_y = 0
dim_x = 0
allowed_steps = 0
goal_location = [] #Will store location of goal(s)
character_location = (0,0)
level = [] #Will store the level. "" is an empty square, "b" is an immobile block, "m" is a movable block, "c" is the character, "w" is a winning block.
level_reset = [] #Will store a copy of initial level for resetting
tofinish_array = None

def imp_level(filename):
    """This function imports a level from the text version exported from the level editor."""
    global level
    global goal_location
    global character_location
    global dim_x
    global dim_y
    global allowed_steps
    with open(filename,"r") as infile:
        level_in = infile.read()
        level_in = level_in.split("<>")
        for command in level_in: #Loop through level building commands, deal with them
            command = command.lstrip().rstrip() #Get rid of whitespace and newlines.
            if(command[:14] == "_root.drawGrid"):
                dim_y,dim_x = command[14:-2].split(",")[-2:] #The coordinate system he set up is nothing short of mind-bogglingly silly
                dim_y = int(dim_y)
                dim_x = int(dim_x)
                level = [[" "]*dim_x for i in range(dim_y)]
            elif(command[:18] == "_root.allowedSteps"):
                allowed_steps = int(command[-4:-1]) #Supports only 10-999 steps, should fix if I care
            elif(command[:21] == "_root.setWinningBlock"):
                temp_x,temp_y = command[22:-2].split(",")[:]
                level[int(temp_y)][int(temp_x)] = "w"
                goal_location.append((int(temp_x),int(temp_y)))
            elif(command[:20] == "_root.placeCharacter"):
                temp_x,temp_y = command[21:-2].split(",")[:]
                level[int(temp_y)][int(temp_x)] = "c"
                character_location = (int(temp_x),int(temp_y))
            elif(command[:15] == "blockArray.push"):
                temp = command[28:].split(",")
                if len(temp) == 2:
                    temp_x = temp[0]
                    temp_y = temp[1][:-2]
                    level[int(temp_y)][int(temp_x)] = "b"
                else:
                    #assert(temp[2][1:8] == "Movable") #If not, I dunno what kind of weird game you're playing...
                    temp_x = temp[0]
                    temp_y = temp[1]
                    level[int(temp_y)][int(temp_x)] = "m"
            else:
                #print "Command skipped:"
                #print command.__repr__()
                pass
    level_reset = copy.deepcopy(level) #copy of initial level for resetting purposes.
###End imp_level

def print_array(a):
    """Prints the array in a slightly legible manner"""
    for line in a:
        for square in line:
            print square,"\t",
        print

def reset_level():
    """Resets level to original state."""
    level = copy.deepcopy(level_reset)

def update_level(temp_level,path):
    """updates level as it would be if moves in path variable are executed. DOES NOT CHECK FOR LEGALITY OF MOVES, more efficient to check before calling this function."""
    for i in xrange(1,len(path)):
        difference = (path[i][0]-path[i-1][0],path[i][1]-path[i-1][1])
        temp_level[path[i-1][1]][path[i-1][0]] = " "
        if(temp_level[path[i][1]][path[i][0]] == "m"):
            temp_level[path[i][1]+difference[1]][path[i][0]+difference[0]] = "m"
        temp_level[path[i][1]][path[i][0]] = "c"
    return temp_level
        

def distance(a,b):
    """Returns the manhattan distance between two squares. Used to weight directions when brute forcing. Input should be 2 tuples of form (x,y)."""
    if not(( 0 <= a[0] < dim_x) and (0 <= b[0] < dim_x) and (0 <= a[1] < dim_y) and (0 <= b[1] < dim_y)):
        return allowed_steps+2
    return abs(b[0]-a[0])+abs(b[1]-a[1])

def generate_tofinish(tmp_level,b):
    """Generates an array which gives the distances from all accessible points on the board to point b, accounting for black block locations, but not pink."""
    global tofinish_array
    tmp_level = copy.deepcopy(tmp_level) #Because I'm scared
    for i in xrange(dim_x):
        for j in xrange(dim_y):
            if tmp_level[j][i] == "m":
                tmp_level[j][i] = " "

    tofinish_array = [[allowed_steps+2]*dim_x for i in range(dim_y)] #Initialize to all be too far
    for i in xrange(dim_x):
        for j in xrange(dim_y):
            if tmp_level[j][i] == "b":
                continue
            else:
                t1,t2,tofinish_array[j][i],t3 = brute_force((j,i),b,tmp_level,quiet=True)
    print_array(tofinish_array)
     

def distance_to_finish(a):
    """Returns the distance from point a to the finish, including black blocks but not pink."""
    global tofinish_array
    if not(( 0 <= a[0] < dim_x) and (0 <= a[1] < dim_y)):
        return allowed_steps+2
    return tofinish_array[a[1]][a[0]]

###Find adjacent accessible points###
def adjacent(a,temp_level):
    """returns a list of all accessible points adjacent to point a = (x,y) in the level map passed to it."""
    global dim_x
    global dim_y
    adj_list = [(a[0]-1,a[1]),(a[0]+1,a[1]),(a[0],a[1]-1),(a[0],a[1]+1)]
    to_remove = []
    for point in adj_list:
        difference = (point[0]-a[0],point[1]-a[1]) #Vector difference of the points
        if (not((0 <= point[0] < dim_x)and(0 <= point[1] < dim_y))) or (temp_level[point[1]][point[0]] == "b") or ((temp_level[point[1]][point[0]] == "m") and (not((0 <= point[0]+difference[0] < dim_x)and(0 <= point[1]+difference[1] < dim_y)) or not(temp_level[point[1]+difference[1]][point[0]+difference[0]] in " wc"))): #Checks if point is accessible.
            to_remove.append(point)
    for point in to_remove:
        adj_list.remove(point)
    return adj_list

def adjacent_without_pinks(a,temp_level):
    """returns a list of all accessible points adjacent to point a = (x,y), treating pinks as empty spaces."""
    global dim_x
    global dim_y
    adj_list = [(a[0]-1,a[1]),(a[0]+1,a[1]),(a[0],a[1]-1),(a[0],a[1]+1)]
    to_remove = []
    for point in adj_list:
        difference = (point[0]-a[0],point[1]-a[1]) #Vector difference of the points
        if (not((0 <= point[0] < dim_x)and(0 <= point[1] < dim_y))) or (temp_level[point[1]][point[0]] == "b"): #Checks if point is accessible.
            to_remove.append(point)
    for point in to_remove:
        adj_list.remove(point)
    return adj_list

###end adjacent###

def brute_force(a=None,b=None,brute_level=None,quiet=False,forbidden=[],target_steps=None,distance_map=None,best=None,path=None,position_hash_array=None):
    """Attemps to find by brute force a path between the two points, will cease when it finds a path of length target_steps. If points are not provided, defaults to character location and goal location."""
    global level
    global goal_location
    global character_location
    global dim_x
    global dim_y
    global allowed_steps
    global tofinish_array
    if(a == None):
        a = character_location
    if(b == None):
        b = goal_location[0]
    if(brute_level == None):
        brute_level = copy.deepcopy(level) #A copy we can do things with        
    if(target_steps == None):
        target_steps = allowed_steps
    if(distance_map == None): #only occurs on first layer call, initialization
        distance_map = [[allowed_steps + 2]*dim_x for i in range(dim_y)] #We prune if a square is more than the allowed number of steps away, so for comparison purposes this suffices
        distance_map[a[1]][a[0]] = 0 #zero distance from the beginning
        best = allowed_steps + 2     
        path = []
        position_hash_array = [[[]]*dim_x for i in range(dim_y)] #Tracks the hash of position at each point along path
        position_hash_array[a[1]][a[0]] = hash(brute_level.__repr__())

    best_path = []
    path.append(a)
   #Check four points around, recursively call brute force from the ones that we can get to for less cost than before, starting with the point which has the least distance from point b
    to_check = adjacent(a,brute_level)
    to_check = [x for x in to_check if x not in forbidden] #Forbidden is for when we are doing black boxes, don't want to step outside the rooms
    to_check.sort(key = lambda x: distance(x,b)) #Sorts the list so that the first to be checked are the closest to point b
    for point in to_check:
        difference = (point[0]-a[0],point[1]-a[1]) #Vector difference of the points
        if((a[0]+difference[0],a[1]+difference[1]) == b):
            if(distance_map[b[1]][b[0]] > len(path)+1):
                distance_map[b[1]][b[0]] = len(path)
                path.append(point)
                best = len(path)-1 #-1 because path includes start.
                if(quiet == False):
                    print "Success!",best,path
                return distance_map,brute_level,best,path
        elif(distance(point,b) > min(allowed_steps,best)-(len(path))): #If the goal is farther from player (manhattan distance) than the number of steps we have left, or the best distance so far, no point continuing.
            continue
        elif ((brute_level[a[1]+difference[1]][a[0]+difference[0]] == "b") or ((brute_level[a[1]+difference[1]][a[0]+difference[0]] == "m") and not(((0 <= a[0]+2*difference[0]< dim_x) and(0 <= a[1]+2*difference[1]< dim_y)) and ((brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] == " ") or (brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] == "w"))))): #If point cannot be moved to, check next on list.
            continue
        elif(brute_level[point[1]][point[0]] in " mwc"): #We know point is not a blocked movable or block, check if winning or empty or movable (which must not be blocked, and if so, try moving there.
            distance_map[a[1]+difference[1]][a[0]+difference[0]] = len(path) #Add distance to map
            something_moved = False #Boolean which is true if we moved something to get onto this square. For backtracking.
            if(brute_level[point[1]][point[0]] == "m"): #If there was a movable here
                if(brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] == " "):
                    brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] = "m" #Move it on over
                elif(brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] == "w"):
                    brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] = "mw" #Move it on over              
                else:
                    print "Error."
                    brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] = "m " #Move it on over                    
                something_moved = True
            brute_level[point[1]][point[0]] = "c" #update character location
            brute_level[a[1]][a[0]] = " " #remove old character
            temp_hash = hash(brute_level.__repr__())

            if ((distance_map[point[1]][point[0]] <= len(path)+1)) and ((temp_hash == position_hash_array[point[1]][point[0]])): #If this path isn't faster than previously, and same things have been moved
                pass #We will just put map back to normal and try next path.
            else:
                position_hash_array[point[1]][point[0]] = temp_hash
                
                #recursively call from this new location
                temp_map,temp_level,temp_best,temp_path = brute_force((a[0]+difference[0],a[1]+difference[1]),b,brute_level,quiet,forbidden,target_steps,distance_map,best,copy.deepcopy(path),copy.deepcopy(position_hash_array))
                if(temp_best < best): #If we found a better path
                    best = temp_best
                    distance_map = temp_map
                    best_path = temp_path
                    if(best == target_steps): #If we found a path of target length, done.
                        return distance_map,brute_level,best,best_path

            #undo map updating!
            if(something_moved): #If there was a movable here
                if(brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] == "m"):
                    brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] = " " #Move it on over
                elif(brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] == "mw"):
                    brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] = "w" #Move it on over                    
                brute_level[point[1]][point[0]] = "m" #update current character location
            else:
                brute_level[point[1]][point[0]] = " " #update current character location
            brute_level[a[1]][a[0]] = "c" #move back to old character location


        else:
            print "FUCK FUCK FUCK FUCK FUCK" #WHAT BROKE NOW?!
            print to_check, point
            print path
            print_array(brute_level)
            print_array(distance_map)
            exit(1)    
    return distance_map,brute_level,best,best_path #Even though it returns level, level isn't updated, problem is it's hard to know when I should keep level updates and when to throw them away. Solution: Just call update_level elsewhere for now.

def brute_force2(a=None,b=None,brute_level=None,quiet=False,forbidden=[],target_steps=None,distance_map=None,best=None,path=None,position_hash_array=None):
    """Attemps to find by brute force a path between the two points, will cease when it finds a path of length target_steps. If points are not provided, defaults to character location and goal location. Almost identical to brute_force, except distance heuristic includes black blocks. generate_tofinish must be called first."""
    global level
    global goal_location
    global character_location
    global dim_x
    global dim_y
    global allowed_steps
    global tofinish_array
    if(a == None):
        a = character_location
    if(b == None):
        b = goal_location[0]
    if(brute_level == None):
        brute_level = copy.deepcopy(level) #A copy we can do things with        
    if(target_steps == None):
        target_steps = allowed_steps
    if(distance_map == None): #only occurs on first layer call, initialization
        distance_map = [[allowed_steps + 2]*dim_x for i in range(dim_y)] #We prune if a square is more than the allowed number of steps away, so for comparison purposes this suffices
        distance_map[a[1]][a[0]] = 0 #zero distance from the beginning
        best = allowed_steps + 2     
        path = []
        position_hash_array = [[[]]*dim_x for i in range(dim_y)] #Tracks the hash of position at each point along path
        position_hash_array[a[1]][a[0]] = hash(brute_level.__repr__())

    best_path = []
    path.append(a)
   #Check four points around, recursively call brute force from the ones that we can get to for less cost than before, starting with the point which has the least distance from point b
    to_check = adjacent(a,brute_level)
    to_check = [x for x in to_check if x not in forbidden] #Forbidden is for when we are doing black boxes, don't want to step outside the rooms
    to_check.sort(key = lambda x: distance(x,b)) #Sorts the list so that the first to be checked are the closest to point b
    for point in to_check:
        difference = (point[0]-a[0],point[1]-a[1]) #Vector difference of the points
        if((a[0]+difference[0],a[1]+difference[1]) == b):
            if(distance_map[b[1]][b[0]] > len(path)+1):
                distance_map[b[1]][b[0]] = len(path)
                path.append(point)
                best = len(path)-1 #-1 because path includes start.
                if(quiet == False):
                    print "Success!",best,path
                return distance_map,brute_level,best,path
        elif(distance_to_finish(point) > min(allowed_steps,best)-(len(path))): #If the goal is farther from player (manhattan distance, black squares included) than the number of steps we have left, or the best distance so far, no point continuing.
            continue
        elif ((brute_level[a[1]+difference[1]][a[0]+difference[0]] == "b") or ((brute_level[a[1]+difference[1]][a[0]+difference[0]] == "m") and not(((0 <= a[0]+2*difference[0]< dim_x) and(0 <= a[1]+2*difference[1]< dim_y)) and ((brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] == " ") or (brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] == "w"))))): #If point cannot be moved to, check next on list.
            continue
        elif(brute_level[point[1]][point[0]] in " mwc"): #We know point is not a blocked movable or block, check if winning or empty or movable (which must not be blocked, and if so, try moving there.
            distance_map[a[1]+difference[1]][a[0]+difference[0]] = len(path) #Add distance to map
            something_moved = False #Boolean which is true if we moved something to get onto this square. For backtracking.
            if(brute_level[point[1]][point[0]] == "m"): #If there was a movable here
                if(brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] == " "):
                    brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] = "m" #Move it on over
                elif(brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] == "w"):
                    brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] = "mw" #Move it on over              
                else:
                    print "Error."
                    brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] = "m " #Move it on over                    
                something_moved = True
            brute_level[point[1]][point[0]] = "c" #update character location
            brute_level[a[1]][a[0]] = " " #remove old character
            temp_hash = hash(brute_level.__repr__())

            if ((distance_map[point[1]][point[0]] <= len(path)+1)) and ((temp_hash == position_hash_array[point[1]][point[0]])): #If this path isn't faster than previously, and same things have been moved
                pass #We will just put map back to normal and try next path.
            else:
                position_hash_array[point[1]][point[0]] = temp_hash
                
                #recursively call from this new location
                temp_map,temp_level,temp_best,temp_path = brute_force((a[0]+difference[0],a[1]+difference[1]),b,brute_level,quiet,forbidden,target_steps,distance_map,best,copy.deepcopy(path),copy.deepcopy(position_hash_array))
                if(temp_best < best): #If we found a better path
                    best = temp_best
                    distance_map = temp_map
                    best_path = temp_path
                    if(best == target_steps): #If we found a path of target length, done.
                        return distance_map,brute_level,best,best_path

            #undo map updating!
            if(something_moved): #If there was a movable here
                if(brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] == "m"):
                    brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] = " " #Move it on over
                elif(brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] == "mw"):
                    brute_level[a[1]+2*difference[1]][a[0]+2*difference[0]] = "w" #Move it on over                    
                brute_level[point[1]][point[0]] = "m" #update current character location
            else:
                brute_level[point[1]][point[0]] = " " #update current character location
            brute_level[a[1]][a[0]] = "c" #move back to old character location


        else:
            print "FUCK FUCK FUCK FUCK FUCK" #WHAT BROKE NOW?!
            print to_check, point
            print path
            print_array(brute_level)
            print_array(distance_map)
            exit(1)    
    return distance_map,brute_level,best,best_path #Even though it returns level, level isn't updated, problem is it's hard to know when I should keep level updates and when to throw them away. Solution: Just call update_level elsewhere for now.
###End brute_force###
        

###Black Boxes Technique###
###This attempts to solve the level by compartmentalizing it into "rooms", which have few entrances and exits, and then creating a graph of the paths between these rooms, and finding routes by solving this graph and then solving rooms. This is an attempt to emulate my thought process on many levels.
###Not entirely debugged or commented, still in progress###
def find_black_box(start_point=None,dont_check=[]):
    if(start_point == None):
        print "Error: find_black_box needs a start point"
    to_expand = [start_point]
    expanded = []
    boundary_points = []
    exits = []
    while(len(to_expand) != 0):
        next_to_expand = []
        for point in to_expand:
            adj_list = adjacent_without_pinks(point,level)
            if len(adj_list) == 2:
                boundary_points.append(point) #This point is next to a "door" out of region
                exits.extend(adj_list)
            else:
                next_to_expand.extend(adj_list) #Otherwise, expand these points next
        expanded.extend(to_expand)
        to_expand = list(set([x for x in next_to_expand if ((x not in expanded) and (x not in boundary_points) and (x not in dont_check))])) #list->set->list is my ugly but short way to get rid of duplicates.  
    exits = [x for x in exits if x not in expanded] #Holy shit I just reached semantic satiation with the word expand
    return expanded,exits

def reduced_traverse(start_node,end_node,node_connections,best_paths,temp_level,path=[]):
    """An A* sort of algorithm for the reduced graph."""
    print "At: ",start_node, path
    to_check = node_connections[start_node]
    to_check.sort(key = lambda x: distance(x,end_node)) #Sorts the list so that the first to be checked are the closest to start
    ret_best = allowed_steps+2
    ret_path = []
    if len(path)+distance(start_node,end_node) > allowed_steps: 
        return ret_best, ret_path       
    for node in to_check:
        if node in path:
            continue
        if len(node_connections[node]) < 2: #Ignore nodes that have no connections (all accessible nodes have at least one connection, the one that we access them from)
            continue
        print "Trying:",node
        print_array(temp_level)
        temp2_level = copy.deepcopy(temp_level)
        start2node_path = [] #Path from start node to node we are checking
        if((start_node,node) in best_paths):
            start2node_path = best_paths[(start_node,node)]
        else:
            temp3_level = copy.deepcopy(temp2_level)
            forbid = [x for x in to_check if x != node]

            if len(path) > 2:
                forbid.append(path[-2])

            temp_dist,temp3_level,temp_best,start2node_path = brute_force(start_node,node,temp3_level,forbidden=forbid,target_steps=0) #temp3_level is discarded 
            if(start2node_path == []):
                print "Error finding path..."
                continue
            best_paths[(start_node,node)] = start2node_path
        print "S2N:",start2node_path
        temp2_level = update_level(temp2_level,start2node_path)
        temp_path = copy.deepcopy(path)
        temp_path.extend(start2node_path)
        ret_best,ret_path = reduced_traverse(node,end_node,node_connections,best_paths,temp2_level,temp_path)
        if ret_best == allowed_steps: #WOO
            return ret_best,ret_path 
    else:
        return ret_best, ret_path

def black_boxes():
    """Searches level (ignoring pinks) to find areas that are mostly sequestered by blacks. It then treats the entrances and exits to these as a reduced graph, and attempts to brute force paths between the most likely seeming points in this reduced graph."""
    #Find sequestered areas
    expanded_regions = []
    nodes = [] #Nodes of the reduced graph
    node_connections = {} #Dictionary indexed by nodes, which lists all the nodes that the node is connected to.
    goal_room_entrances = []
    global goal_location
    global character_location
    nodes_to_check = [character_location] #Nodes to check on next iteration
    while(len(nodes_to_check) != 0):
        next_nodes = []
        nodes.extend(nodes_to_check)
        for point in nodes_to_check:
            t1,t2 = find_black_box(point,dont_check=expanded_regions)
            next_nodes.extend(t2)
            expanded_regions.extend(t1)
            expanded_regions.extend(t2)
            if point in node_connections:
                node_connections[point].extend(t2)
            else:
                node_connections[point] = t2
            for point2 in t2:
                if point2 in node_connections:
                    node_connections[point2].extend([point])
                else:
                    node_connections[point2] = [point]   
            if goal_location[0] in t1 or goal_location[0] in t2:
                goal_room_entrances = t2
        nodes_to_check = list(set([x for x in next_nodes if x not in nodes]))

    for node in node_connections.keys():
        node_connections[node] = list(set(node_connections[node]))

    best_paths = {} #Indexed by ordered pairs of nodes, stores the best path from node a to b as given by brute_force
    for entrance in goal_room_entrances:
        best,best_path = reduced_traverse(character_location,entrance,node_connections,best_paths,level)
        if(best == allowed_steps):
            print "Success!",best,best_path
            break
    else: 
        print "No path found..."
    exit(0)
###End Black Boxes Technique###

    
    
    
    

                
###Actually run something###
if len(sys.argv) != 2:
    print "Input Error: Give a level filename to solve"
    exit(2)

imp_level(sys.argv[1]) #Import the level


#Brute force attempt
for goal in goal_location:
    #generate_tofinish(level,goal)
    t1,t2,best,t4 = brute_force(character_location,goal)
    if best == allowed_steps:
        break
else:
    print "Path not found."
    print "Execution time:",time.time()-ti
    exit(0)
print best,t4
print_array(t1)
print "Execution time:",time.time()-ti


exit(0)
