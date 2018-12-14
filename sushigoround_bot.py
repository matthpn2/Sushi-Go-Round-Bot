import pyautogui
import time
import os
import random
import copy
import sys

# food order constraints
ONIGIRI = "onigiri"
GUNKAN_MAKI = "gunkan_maki"
CALIFORNIA_ROLL = "california_roll"
SALMON_ROLL = "salmon_roll"
SHRIMP_SUSHI = "shrimp_sushi"
UNAGI_ROLL = "unagi_roll"
DRAGON_ROLL = "dragon_roll"
COMBO = "combo"

ALL_ORDER_CONSTRAINTS = {
                            "LEVEL_1": (ONIGIRI, GUNKAN_MAKI, CALIFORNIA_ROLL),
                            "LEVEL_2": (ONIGIRI, GUNKAN_MAKI, CALIFORNIA_ROLL, SALMON_ROLL),
                            "LEVEL_3": (ONIGIRI, GUNKAN_MAKI, CALIFORNIA_ROLL, SALMON_ROLL, SHRIMP_SUSHI),
                            "LEVEL_4": (ONIGIRI, GUNKAN_MAKI, CALIFORNIA_ROLL, SALMON_ROLL, SHRIMP_SUSHI, UNAGI_ROLL),
                            "LEVEL_5": (ONIGIRI, GUNKAN_MAKI, CALIFORNIA_ROLL, SALMON_ROLL, SHRIMP_SUSHI, UNAGI_ROLL, DRAGON_ROLL),
                            "LEVEL_6": (ONIGIRI, GUNKAN_MAKI, CALIFORNIA_ROLL, SALMON_ROLL, SHRIMP_SUSHI, UNAGI_ROLL, DRAGON_ROLL, COMBO),
                            "LEVEL_7": (ONIGIRI, GUNKAN_MAKI, CALIFORNIA_ROLL, SALMON_ROLL, SHRIMP_SUSHI, UNAGI_ROLL, DRAGON_ROLL, COMBO)
}

# ingredient constraints
SHRIMP = "shrimp"
RICE = "rice"
NORI = "nori"
ROE = "roe" 
SALMON = "salmon"
UNAGI = "unagi"

RECIPE = {
             ONIGIRI:           {RICE: 2, NORI: 1},
             GUNKAN_MAKI:       {RICE: 1, NORI: 1, ROE: 2},
             CALIFORNIA_ROLL:   {RICE: 1, NORI: 1, ROE: 1},
             SALMON_ROLL:       {RICE: 1, NORI: 1, SALMON: 2},
             SHRIMP_SUSHI:      {RICE: 1, NORI: 1, SHRIMP: 2},
             UNAGI_ROLL:        {RICE: 1, NORI: 1, UNAGI: 2},
             DRAGON_ROLL:       {RICE: 2, NORI: 1, ROE: 1, UNAGI: 2},
             COMBO:             {RICE: 2, NORI: 1, ROE: 1, SALMON: 1, UNAGI: 1, SHRIMP: 1}
}

# game messages
LEVEL_WIN_MESSAGE = "win"            # checkForGameOver() returns this value if the level has been won
LEVEL_FAIL_MESSAGE = "try again"     # checkForGameOver() returns this value if the level has failed

# settings
MIN_INGREDIENTS = 4                 # if an ingredient gets below this value, order more
PLATE_CLEARING_FREQ = 8             # plates are cleared every PLATE_CLEARING_FREQ number of seconds
NORMAL_RESTOCK_TIME = 7             # NORMAL_RESTOCK_TIME seconds it takes to restock inventory
TIME_TO_REMAKE = 25                 # if an order goes unfilled for TIME_TO_REMAKE seconds, remake it

# global variables
LEVEL = 1                           # current level being played on

INVENTORY = { 
                SHRIMP: 5,
                RICE:   10,
                NORI:   10,
                ROE:    10,
                SALMON: 5,
                UNAGI:  5
}

ORDERING_COMPLETE = {
                        SHRIMP: None,
                        RICE:   None,
                        NORI:   None,
                        ROE:    None,
                        SALMON: None,
                        UNAGI:  None
}                                   # unix timestamp of when an ordered ingredient will arrive

ROLLING_COMPLETE = 0                # unix timestamp of when mat rolling will complete
LAST_PLATE_CLEARING = 0             # unix timestamp of last time plates were cleared
LAST_GAME_OVER_CHECK = 0            # unix timestamp when last checked for Game Over / You Win message

# coordinates of game objects
GAME_REGION = ()                    # (left, top, width, height) value coordinates of entire game window
ENLARGED_REGION = ()                # (left, top, width, height) value coordinates of enlarged game window for MACOS use

INGRED_COORDS = None
PHONE_COORDS = None
TOPPING_COORDS = None
ORDER_BUTTON_COORDS = None
RICE1_COORDS = None
RICE2_COORDS = None
NORMAL_DELIVER_BUTTON_CORDS = None
MAT_COORDS = None

def gameRun():
    '''
        This runs the entire program, which requires the Sushi Go Round game window to be visible on the 
        screen with the PLAY button in sight.
    '''
    print("Program has started. Press Ctrl-C to abort any time.")
    print("To interrupt mouse movement, move mouse abruptly to upper left corner.\n")

    getGameRegion()
    setupCoordinates()
    navigateStartGameMenu()
    startServing()

def imagePath(filename):
    '''
        A shortcut for joining the "images/" file path by returning the filename with "images/" prepended.
    '''
    return os.path.join("images", filename)

def getGameRegion():
    '''
        Finds the game window by searching for the top-right corner image, stored in the top_right_corner.png,
        and assigns it to GAME_REGION. The game must be at the start screen with the PLAY button in sight.
    '''
    global GAME_REGION, ENLARGED_REGION
    
    # locate the top-right corner by finding the (left, top, width, height) tuple of integer coordinates
    print("Finding the game region...")
    region = pyautogui.locateOnScreen(imagePath("top_right_corner.png"), grayscale=True)
    if region is None:
        raise Exception("Couldn't find the game on screen. Make sure it's visible.")

    # calculate the region of the entire game window
    topRightX = int(region[0]/2) + int(region[2]/2)     # left + width
    topRightY = int(region[1]/2)                        # top

    GAME_REGION = (topRightX - 640, topRightY, 640, 480)                                            # game screen is always 640 x 480
    ENLARGED_REGION = (GAME_REGION[0]*2, GAME_REGION[1]*2, GAME_REGION[2]*2, GAME_REGION[3]*2)      # enlarged game screen for MACOS use
    
    print(f"Game region found at {GAME_REGION}.")
    print(f"Enlarged region found at {ENLARGED_REGION}.")

    pyautogui.click(GAME_REGION[0], GAME_REGION[1])
    print("Clicked on the game region window.\n")

def setupCoordinates():
    '''
        Pre-program and set the coordinate-related global variables of the various buttons in the game's user
        interface, which will always be in the same location. The coordinates are all relative to the game window
        whose coordinates are set in GAME_REGION. To find the coordinates manually, use pyautogui.displayMousePosition()
        function to display XY coordinates of the mouse cursor.
    '''
    global INGRED_COORDS, PHONE_COORDS, TOPPING_COORDS, ORDER_BUTTON_COORDS, RICE1_COORDS, RICE2_COORDS, NORMAL_DELIVER_BUTTON_CORDS, MAT_COORDS, LEVEL

    INGRED_COORDS = {
                        SHRIMP: (GAME_REGION[0] + 30, GAME_REGION[1] + 335),
                        RICE:   (GAME_REGION[0] + 90, GAME_REGION[1] + 335),
                        NORI:   (GAME_REGION[0] + 35, GAME_REGION[1] + 385),
                        ROE:    (GAME_REGION[0] + 90, GAME_REGION[1] + 385),
                        SALMON: (GAME_REGION[0] + 35, GAME_REGION[1] + 425),
                        UNAGI:  (GAME_REGION[0] + 90, GAME_REGION[1] + 425)
    }

    PHONE_COORDS = (GAME_REGION[0] + 580, GAME_REGION[1] + 360)
    TOPPING_COORDS = (GAME_REGION[0] + 513, GAME_REGION[1] + 269)

    ORDER_BUTTON_COORDS = {
                              SHRIMP:   (GAME_REGION[0] + 490, GAME_REGION[1] + 222),
                              UNAGI:    (GAME_REGION[0] + 570, GAME_REGION[1] + 222),
                              NORI:     (GAME_REGION[0] + 490, GAME_REGION[1] + 278),
                              ROE:      (GAME_REGION[0] + 570, GAME_REGION[1] + 278),
                              SALMON:   (GAME_REGION[0] + 490, GAME_REGION[1] + 330)
    }

    RICE1_COORDS = (GAME_REGION[0] + 500, GAME_REGION[1] + 290)
    RICE2_COORDS = (GAME_REGION[0] + 538, GAME_REGION[1] + 281)

    NORMAL_DELIVER_BUTTON_CORDS = (GAME_REGION[0] + 489, GAME_REGION[1] + 293)
    MAT_COORDS = (GAME_REGION[0] + 193, GAME_REGION[1] + 380)

    LEVEL = 1

def navigateStartGameMenu():
    '''
        Performs the mouse clicks to navigate from the start screen, with the PLAY button visible, to the
        beginning of the first level of the game.
    '''
    # click on the PLAY button
    print("Looking for the PLAY button...")
    while True:
        position = pyautogui.locateCenterOnScreen(imagePath("play_button.png"), region=ENLARGED_REGION, grayscale=True)
        if position is not None:
            break
    pyautogui.click(position[0]/2, position[1]/2)
    print("Clicked on the PLAY button.\n")

    # click on the CONTINUE button
    pressContinueButton("continue_button.png")

    # click on the SKIP button
    print("Looking for the SKIP button...")
    position = pyautogui.locateCenterOnScreen(imagePath("yellow_skip_button.png"), region=ENLARGED_REGION, grayscale=True)
    if position is None:
        position = pyautogui.locateCenterOnScreen(imagePath("red_skip_button.png"), region=ENLARGED_REGION, grayscale=True)
    pyautogui.click(position[0]/2, position[1]/2)
    print("Clicked on the SKIP button.\n")

    # click on the CONTINUE button again
    pressContinueButton("continue_button.png")

def pressContinueButton(continueButton):
    '''
        Performs the search and mouse clicks on the continue button.
    '''
    print("Looking for the CONTINUE button...")
    position = pyautogui.locateCenterOnScreen(imagePath(continueButton), region=ENLARGED_REGION, grayscale=True)
    pyautogui.click(position[0]/2, position[1]/2)
    print("Clicked on the CONTINUE button.\n")

def getOrders(levelNumber):
    '''     
        Scans the region of the game screen for customer orders, which appear as dish images in word bubbles
        above their heads, and matches them to their respective order images. Returns a dictionary with a 
        (left, top, width, height) tuple of integer keys and other constant values.
    '''
    print("Getting customer orders...\n")
    orders = {}
    for orderType in ALL_ORDER_CONSTRAINTS[f"LEVEL_{levelNumber}"]:
        allOrders = pyautogui.locateAllOnScreen(imagePath(f"{orderType}_order.png"), region=((GAME_REGION[0] + 32)*2, (GAME_REGION[1] + 46)*2, 1120, 105))
        for ao in allOrders:
            orders[ao] = orderType
    return orders

def getOrdersDifference(currentOrders, oldOrders):
    '''
        Figures out which of the orders have been seen before and possible already fulfilled by finding the 
        difference between the passed order dictionaries. Returns a tuple of two dictionaries. The first dictionary
        is the "ADDED" dictionary of orders added to currentOrders since oldOrders. The second dictionary is the
        "REMOVED" dictionary of orders in oldOrders but removed in newOrders.
    '''
    addedOrders = {}
    removedOrders = {}

    # find all orders in currentOrders that are NEW and NOT FOUND in oldOrders
    for ord in currentOrders:
        if ord not in oldOrders:
            addedOrders[ord] = currentOrders[ord]

    # find all orders in oldOrders that were REMOVED and NOT FOUND in newOrders
    for ord in oldOrders:
        if ord not in currentOrders:
            removedOrders[ord] = oldOrders[ord]
    return addedOrders, removedOrders

def makeOrder(orderType):
    '''
        Create the dish order by clicking on the correct ingredients and clicking on the rolling mat. Returns
        None for a successfully made order or a list of ingredients constant if that needed ingredient is
        missing.
    '''
    global ROLLING_COMPLETE, INGRED_COORDS, INVENTORY

    # wait until the mat is clear, where mat is done rolling and there is room on the conveyor belt
    while time.time() < ROLLING_COMPLETE and pyautogui.locateOnScreen(imagePath("clear_mat.png"), region=((GAME_REGION[0] + 115)*2, (GAME_REGION[1] + 295)*2, 440, 350), grayscale = True) is None:
        time.sleep(0.1)

    # check that all the necessary ingredients are available in the inventory, otherwise return a list of ingredient constants
    need_ingredients = []
    for ingredient, amount in RECIPE[orderType].items():
        if INVENTORY[ingredient] < amount:
            print(f"More {ingredient} is needed to make {orderType}.")
            need_ingredients.append(ingredient)

    if need_ingredients != []:
        return need_ingredients 

    # click on each of the necessary ingredients and subtract from inventory stock
    for ingredient, amount in RECIPE[orderType].items():
        for i in range(amount):
            pyautogui.click(INGRED_COORDS[ingredient])
            INVENTORY[ingredient] -= 1

    # click on ROLLING MAT to complete the order
    time.sleep(0.1)
    pyautogui.click(MAT_COORDS)
    print(f"Made a {orderType} order.")

    # update the timestamp of when the mat rolling will be finished, +1.5 seconds
    ROLLING_COMPLETE = time.time() + 1.5

def orderIngredient(ingredients):
    '''
        Navigate the menu buttons in the lower right corner of the game window and order more ingredients.
    '''
    for ingredient in ingredients:
        print(f"Ordering more {ingredient} as the inventory says {INVENTORY[ingredient]} left...")

        # click on the PHONE
        pyautogui.click(PHONE_COORDS)

        # handle pressing buttons for ordering rice and check to make sure previous rice order hasn't been made
        if ingredient == RICE and ORDERING_COMPLETE[RICE] is None:
            # click on RICE
            pyautogui.click(RICE1_COORDS)

            # check to see if we can't afford the rice
            if pyautogui.locateOnScreen(imagePath("cant_afford_rice.png"), region=((GAME_REGION[0] + 498)*2, (GAME_REGION[1] + 242)*2, 180, 150)):
                print("Can't afford rice, cancelling order.")
                # click on the CANCEL PHONE and try ordering the remaining needed ingredients
                pyautogui.click(GAME_REGION[0] + 585, GAME_REGION[1] + 335)

                # if ingredient is not the last in the list, continue ordering; otherwise, return
                if ingredient != ingredients[-1]:
                    continue
                return
            
            # otherwise, purchase rice with normal delivery
            pyautogui.click(RICE2_COORDS)
            pyautogui.click(NORMAL_DELIVER_BUTTON_CORDS)

            # set the expected delivery time in ORDERING_COMPLETE
            ORDERING_COMPLETE[RICE] = time.time() + NORMAL_RESTOCK_TIME
            print(f"Ordered more {RICE}.")

        # handle pressing buttons for ordering non-rice ingredients and check to make sure previous non-rice order hasn't been made
        elif ORDERING_COMPLETE[ingredient] is None:
            # click on the NON-RICE ingredient
            pyautogui.click(TOPPING_COORDS)

            # check to see if we can't afford the non-rice ingredient
            if pyautogui.locateOnScreen(imagePath(f"cant_afford_{ingredient}.png"), region=((GAME_REGION[0] + 446)*2, (GAME_REGION[1] + 187)*2, 360, 360)):
                print(f"Can't afford {ingredient}, cancelling order.")
                # click on CANCEL PHONE and try ordering the remaining needed ingredients
                pyautogui.click(GAME_REGION[0] + 597, GAME_REGION[1] + 337)

                # if ingredient is not the last in the list, continue ordering; otherwise, return
                if ingredient != ingredients[-1]:
                    continue
                return

            # otherwise, purchase the non-rice with normal delivery
            pyautogui.click(ORDER_BUTTON_COORDS[ingredient])
            pyautogui.click(NORMAL_DELIVER_BUTTON_CORDS)

            # set the expected delivery time in ORDERING COMPLETE
            ORDERING_COMPLETE[ingredient] = time.time() + NORMAL_RESTOCK_TIME
            print(f"Ordered more {ingredient}.")

        # else, the order has already been made
        else:
            pyautogui.click(GAME_REGION[0] + 589, GAME_REGION[1] + 341)
            print(f"Already ordered {ingredient}.")

def updateInventory():
    '''
        Check if the timestamps in ORDERING_COMPLETE indicate that the ordered ingredients have arrived
        and update INVENTORY with new values. Shrimp, unagi and salmon deliveries always add 5. Nori, roe
        and rice always add 10.
    '''
    for ingredient in INVENTORY:
        # check if ingredient order was made and completed
        if ORDERING_COMPLETE[ingredient] is not None and time.time() > ORDERING_COMPLETE[ingredient]:
            # reset ingredient order to None
            ORDERING_COMPLETE[ingredient] = None

            if ingredient in (SHRIMP, UNAGI, SALMON):
                INVENTORY[ingredient] += 5
            elif ingredient in (NORI, ROE, RICE):
                INVENTORY[ingredient] += 10
            print(f"Updated inventory with added {ingredient}.")
    print(f"Current inventory stock: {INVENTORY}")

def clearPlates():
    '''
        Blindly clicks on all six plates where there could be dirty plates to be cleaned up, as
        there is no penalty for clicking when there isn't a dirty plate ot be cleaned.
    '''
    global LAST_PLATE_CLEARING
    print("Clearing customer plates...\n")
    for p in range(6):
        pyautogui.click(GAME_REGION[0] + 83 + (p * 101), GAME_REGION[1] + 203)

    # set the timestamp of the last time the plates were cleared
    LAST_PLATE_CLEARING = time.time()
    
def checkGameOver():
    '''
        Checks the screen for "You win" or "You Fail" message. If the game is over, the program try again and return
        LEVEL_FAIL_MESSAGE. Otherwise, if the level has been beaten, click on the "You Win" window and return LEVEL_WIN_MESSAGE.
    '''
    # check for "YOU WIN" message
    message = pyautogui.locateOnScreen(imagePath("you_win.png"), region=((GAME_REGION[0] + 188)*2, (GAME_REGION[1] + 94)*2, 524, 120))
    if message is not None:
        pyautogui.click(pyautogui.center(message)[0]/2, pyautogui.center(message)[1]/2)
        print("Move on to next level.\n")
        return LEVEL_WIN_MESSAGE

    # check for "YOU FAIL" message
    message = pyautogui.locateOnScreen(imagePath("sorry_you_failed.png"), region=((GAME_REGION[0] + 188)*2, (GAME_REGION[1] + 94)*2, 524, 120))
    if message is not None:
        pyautogui.click(pyautogui.center(message)[0]/2, pyautogui.center(message)[1]/2)
        print("Level has failed. Trying again.\n")
        return LEVEL_FAIL_MESSAGE

def startServing():
    '''
        The main logic of the game functions which handles all of the following aspects of gameplay:
            1. Seeing which orders are being requested from the customers.
            2. Creating the dishes to fill the orders.
            3. Ordering more ingredients when there is a low stock.
            4. Checking if customers haven't received their orders in a long time and remake those orders.
            5. Clearing finished customer plates.
            6. Checking if ordered ingredients have arrived.
            7. Checking if the game has been lost or if the level has been passed yet.
    '''
    global LAST_GAME_OVER_CHECK, INVENTORY, ORDERING_COMPLETE, LEVEL

    # reset all game state variables
    oldOrders = {}
    backOrders = {}
    remakeOrders = {}
    remakeTimes = {}

    LAST_GAME_OVER_CHECK = time.time()

    ORDERING_COMPLETE = {
                            SHRIMP: None,
                            RICE:   None,
                            NORI:   None,
                            ROE:    None,
                            SALMON: None,
                            UNAGI:  None
    }

    while True:
        # checking if the game has been lost or if level has been won yet once every 12 iterations
        if time.time() - 12 > LAST_GAME_OVER_CHECK:
            result = checkGameOver()

            # if level has been beaten
            if result == LEVEL_WIN_MESSAGE:
                # reset global variables
                INVENTORY = { 
                                SHRIMP: 5,
                                RICE: 10,
                                NORI: 10,
                                ROE: 10,
                                SALMON: 5,
                                UNAGI: 5
                }

                ORDERING_COMPLETE = {
                                        SHRIMP: None,
                                        RICE: None,
                                        NORI: None,
                                        ROE: None,
                                        SALMON: None,
                                        UNAGI: None
                }

                backOrders = {}
                remakeOrders = {}
                currentOrders = {}
                oldOrders = {}

                # allow user to view end-level stats for 7 seconds before moving on to the next level
                print(f"Level {LEVEL} is complete.\n")
                LEVEL += 1
                time.sleep(7)

                # end the program if the game has been won
                if LEVEL == 8: sys.exit()

                # click buttons to continue to next level
                pressContinueButton("continue_button.png")

                # click on second continue button if game isn't finished yet
                if LEVEL <= 7: pressContinueButton("continue_arrow.png")
            
            # if level has been loss
            elif result == LEVEL_FAIL_MESSAGE:
                # reset global variables
                INVENTORY = { 
                                SHRIMP: 5,
                                RICE: 10,
                                NORI: 10,
                                ROE: 10,
                                SALMON: 5,
                                UNAGI: 5
                }

                ORDERING_COMPLETE = {
                                        SHRIMP: None,
                                        RICE: None,
                                        NORI: None,
                                        ROE: None,
                                        SALMON: None,
                                        UNAGI: None
                }

                backOrders = {}
                remakeOrders = {}
                currentOrders = {}
                oldOrders = {}

                # allow user to take in the loss for 3 seconds before trying again
                time.sleep(3)

                # navigate through until level begins again
                pressContinueButton("continue_button.png")
                pressContinueButton("partial_continue_button.png")

                print("Looking for the YES button...")
                position = pyautogui.locateCenterOnScreen(imagePath("yes_button.png"), region=ENLARGED_REGION)
                pyautogui.click(position[0]/2, position[1]/2)
                print("Clicked on the YES button.\n")

                pressContinueButton("continue_arrow.png")

        # see which orders are being requested from the customers
        currentOrders = getOrders(LEVEL)

        # check for which orders are NEW and which have been COMPLETED since LAST scan
        addedOrders, removedOrders = getOrdersDifference(currentOrders, oldOrders)
        if addedOrders != {}:
            print(f"New orders: {list(addedOrders.values())}.")
            # set times for when dish should be remade if it is still being requested by customer
            for ord in addedOrders:
                remakeTimes[ord] = time.time() + TIME_TO_REMAKE

        if removedOrders != {}:
            print(f"Removed orders: {list(removedOrders.values())}.")
            # remove times for orders that were completed
            for ord in removedOrders:
                del remakeTimes[ord]

        # check if any remake times have past and add to remakeOrders
        for ord, remakeTime in copy.copy(remakeTimes).items():
            if time.time() > remakeTime:
                # reset remakeTime
                remakeTimes[ord] = time.time() + TIME_TO_REMAKE
                remakeOrders[ord] = currentOrders[ord]
                print(f"{currentOrders[ord]} added to remakeOrders.\n")

        # attempt to create the dishses to fill the orders
        for pos, ord in addedOrders.items():
            result = makeOrder(ord)

            # order more ingredients when there is a low stock
            if result is not None:
                orderIngredient(result)

                # place the failed order in backOrders
                backOrders[pos] = ord
                print(f"Ingredients for {ord} are not available. Putting it on back order.\n")
        
        # clear finished customer plates once every 10 iterations or if more than 8 seconds since last plate clearing
        if random.randint(1, 10) == 1 or time.time() - PLATE_CLEARING_FREQ > LAST_PLATE_CLEARING:
            clearPlates()
            time.sleep(0.5)

        # check if ordered ingredients have arrived
        updateInventory()

        # check if customers haven't received their orders in a long time and remake those orders
        for pos, ord in copy.copy(backOrders).items():
            result = makeOrder(ord)

            # if order is made, remove from backOrders
            if result is None:
                del backOrders[pos]
                print(f"Filled back order for {ord}.\n")
            
            elif result is not None:
                orderIngredient(result)

        for pos, ord in copy.copy(remakeOrders).items():
            # if order is no longer needed, remove it from remakeOrders
            if pos not in currentOrders:
                del remakeOrders[pos]
                print(f"Cancelled remake order for {ord}.\n")
                continue
            
            # else attempt to remake the order
            result = makeOrder(ord)
            
            # if order is made, remove from remakeOrders
            if result is None:
                del remakeOrders[pos]
                print(f"Filled remake order for {ord}.\n")
            
            elif result is not None:
                orderIngredient(result)
        
        # check if any ingredients have less than 4 in stock once every 5 iterations
        if random.randint(1,5) == 1:
            for ingredient, amount in INVENTORY.items():
                if amount < MIN_INGREDIENTS:
                    orderIngredient([ingredient])
        oldOrders = currentOrders

if __name__ == "__main__":
    gameRun()

# For more information, proceed to PyAutoGUI documentation at https://pyautogui.readthedocs.io/en/latest/ .
#                                  SushiGoRound game page at https://www.miniclip.com/games/sushi-go-round/en/ 
#                                  Tutorial page at https://inventwithpython.com/blog/2014/12/17/programming-a-bot-to-play-the-sushi-go-round-flash-game/ .