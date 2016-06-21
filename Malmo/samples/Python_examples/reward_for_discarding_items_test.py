# --------------------------------------------------------------------------------------------------------------------
# Copyright (C) Microsoft Corporation.  All rights reserved.
# --------------------------------------------------------------------------------------------------------------------
# Sample to demonstrate use of the RewardForDiscardingItem mission handler, and the DiscardCurrentItem command.
# Leaves a trail of bread-crumbs.

import MalmoPython
import os
import random
import sys
import time
import json

def GetMissionXML(summary):
    ''' Build an XML mission string that uses the RewardForCollectingItem mission handler.'''
    
    return '''<?xml version="1.0" encoding="UTF-8" ?>
    <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ProjectMalmo.microsoft.com Mission.xsd">
        <About>
            <Summary>''' + summary + '''</Summary>
        </About>

        <ServerSection>
            <ServerHandlers>
                <FlatWorldGenerator generatorString="3;7,220*1,5*3,2;3;,biome_1" />
                <DrawingDecorator>
                    <DrawCuboid x1="-50" y1="226" z1="-50" x2="50" y2="226" z2="50" type="carpet" colour="RED" face="UP"/>
                </DrawingDecorator>
                <ServerQuitFromTimeUp timeLimitMs="15000"/>
                <ServerQuitWhenAnyAgentFinishes />
            </ServerHandlers>
        </ServerSection>

        <AgentSection mode="Survival">
            <Name>The Full Caterpillar</Name>
            <AgentStart>
                <Placement x="0" y="227" z="0"/>
                <Inventory>
                    <InventoryItem slot="0" type="cookie" quantity="64"/>
                    <InventoryItem slot="1" type="fish" quantity="64"/>
                </Inventory>
            </AgentStart>
            <AgentHandlers>
                <RewardForDiscardingItem>
                    <Item reward="-2" type="cookie"/>
                    <Item reward="10" type="fish"/>
                </RewardForDiscardingItem>
                <InventoryCommands/>
                <ChatCommands/>
                <ContinuousMovementCommands turnSpeedDegs="240"/>
            </AgentHandlers>
        </AgentSection>

    </Mission>'''
  

def SetVelocity(vel): 
    agent_host.sendCommand( "move " + str(vel) )

def SetTurn(turn):
    agent_host.sendCommand( "turn " + str(turn) )

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately

validate = True
# Create a pool of Minecraft Mod clients.
# By default, mods will choose consecutive mission control ports, starting at 10000,
# so running four mods locally should produce the following pool by default (assuming nothing else
# is using these ports):
my_client_pool = MalmoPython.ClientPool()
my_client_pool.add(MalmoPython.ClientInfo("127.0.0.1", 10000))
my_client_pool.add(MalmoPython.ClientInfo("127.0.0.1", 10001))
my_client_pool.add(MalmoPython.ClientInfo("127.0.0.1", 10002))
my_client_pool.add(MalmoPython.ClientInfo("127.0.0.1", 10003))

agent_host = MalmoPython.AgentHost()
try:
    agent_host.parse( sys.argv )
except RuntimeError as e:
    print 'ERROR:',e
    print agent_host.getUsage()
    exit(1)
if agent_host.receivedArgument("help"):
    print agent_host.getUsage()
    exit(0)

if agent_host.receivedArgument("test"):
    num_reps = 1
else:
    num_reps = 30000

for iRepeat in range(num_reps):
    my_mission = MalmoPython.MissionSpec(GetMissionXML("Let them eat fish/cookies #" + str(iRepeat)),validate)
    launchedMission=False
    while not launchedMission:
        try:
            # Set up a recording - MUST be done once for each mission - don't do this outside the loop!
            my_mission_record = MalmoPython.MissionRecordSpec()
            # And attempt to start the mission:
            agent_host.startMission( my_mission, my_client_pool, my_mission_record, 0, "itemDiscardTestExperiment" )
            launchedMission=True
        except RuntimeError as e:
            print "Error starting mission",e
            print "Is the game running?"
            exit(1)

    world_state = agent_host.getWorldState()
    while not world_state.is_mission_running:
        time.sleep(0.1)
        world_state = agent_host.getWorldState()

    reward = 0.0    # keep track of reward for this mission.
    turnCount = 0   # for keeping track of turn.
    discardTimer = 0
    # start running:
    agent_host.sendCommand("move 1")

    # main loop:
    while world_state.is_mission_running:
        world_state = agent_host.getWorldState()
        if world_state.number_of_rewards_since_last_state > 0:
            # A reward signal has come in - see what it is:
            delta = world_state.rewards[0].value
            reward+=delta
            if delta==10:
                agent_host.sendCommand("chat " + random.choice(["Have a fish!", "Free trout!", "Fishy!", "Bleurgh, catch"]))
            elif delta==-2:
                agent_host.sendCommand("chat " + random.choice(["Cookies!", "Free cookies!", "Have a cookie.", "I'll just leave this here."]))

        if turnCount > 0:
            turnCount -= 1
            if turnCount == 0:
                agent_host.sendCommand("turn 0")
        
        if turnCount == 0 and random.random() > 0.8:
            agent_host.sendCommand("turn " + str(random.random() - 0.5))
            turnCount = random.randint(1,10)

        discardTimer+=1
        if discardTimer > 5:
            # Chuck an item:
            agent_host.sendCommand("discardCurrentItem")
            discardTimer = 0
            # And select the next item to chuck:
            hotbar="1" if (random.random() > 0.5) else "2"
            agent_host.sendCommand("hotbar." + hotbar + " 1")
            agent_host.sendCommand("hotbar." + hotbar + " 0")

        time.sleep(0.1)
        
    # mission has ended.
    print "Mission " + str(iRepeat+1) + ": Reward = " + str(reward)
    for error in world_state.errors:
        print "Error:",error.text
    time.sleep(0.5) # Give the mod a little time to prepare for the next mission.