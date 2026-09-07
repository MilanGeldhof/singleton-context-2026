import time
import os
from collections import defaultdict
from psychopy import gui, data, core, visual, event
import pandas as pd
import numpy as np
import pyxid2

# working version with new things after feedback preregistration
# This code was tested in PsychoPy version: 2023.2.2 and 2024.2.4

# -----------------------------------------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------------------------------------
def message(message_text="test", duration=0, height=None, pos=(0.0, 0.0), bold=False):
    win_color = round(win.color[0])  # get first value only, works for this case

    message_on_screen = visual.TextStim(win, text="OK", wrapWidth=1500)
    message_on_screen.color = text_color_for_background[background_colors_psychopy_version.index(win_color)]
    message_on_screen.text = message_text
    message_on_screen.height = height
    message_on_screen.pos = pos
    message_on_screen.bold = bold

    message_on_screen.draw()
    win.flip()
    time.sleep(duration)

def conscience_detection():
    win.flip()  # remove previous stimuli

    text1 = ("Ga vanaf nu verder met toetsenbord en muis.\n\n"
             "Als laatste willen we nog korte vraag stellen over het experiment.\n\n"
             "Kwam de (afleidende) figuur met de unieke KLEUR vaker voor op bepaalde locaties dan andere?\n\n"
             "Druk op 'J' voor Ja of op 'N' voor Nee")

    text2 = ("Klik op de locatie waar de figuur met de unieke KLEUR het vaakst voorkwam bij DEZE achtergrondkleur.\n\n"
             "De geselecteerde locatie zal groen kleuren als bevestiging van jouw keuze.\n\n"
             "Volg gerust je intuïtie als je twijfelt.\n\n\n"
             "Klik op de tekst rechtsonder om door te gaan.")

    message(message_text=text1)
    keys = event.waitKeys(keyList=['j', 'n'])

    aware_binary = 1 if keys[0] == 'j' else 0
    data = defaultdict(dict)
    mouse = event.Mouse(visible=True, win=win)

    # place numbers on screen so they can click on it
    coordinates = [(960,360), (1116,450), (1116,630), (960,720), (804,630), (804,450)] # Size = 180
    coordinates = [(x - screen_res[1] / 2, y - screen_res[0] / 2) for x, y in coordinates]

    for index_color in range(2):
        selected_locations = set()

        win.color = background_colors[index_color]
        psychopy_version_of_color = round(win.color[0])
        text_color = text_color_for_background[background_colors_psychopy_version.index(psychopy_version_of_color)]

        text_inst_end = visual.TextStim(win, text=text2, height=19, pos=(-500, 0), color=text_color)

        nummer1 = visual.Circle(win, size=size_circle, pos=coordinates[0], color=text_color)
        nummer2 = visual.Circle(win, size=size_circle, pos=coordinates[1], color=text_color)
        nummer3 = visual.Circle(win, size=size_circle, pos=coordinates[2], color=text_color)
        nummer4 = visual.Circle(win, size=size_circle, pos=coordinates[3], color=text_color)
        nummer5 = visual.Circle(win, size=size_circle, pos=coordinates[4], color=text_color)
        nummer6 = visual.Circle(win, size=size_circle, pos=coordinates[5], color=text_color)
        
        end_box = visual.TextStim(win, text='Klik HIER als je klaar bent', height=35, pos=(600, -450), color=text_color)

        # Keep track of which numbers were already clicked in the previous frame
        numbers = [nummer1, nummer2, nummer3, nummer4, nummer5, nummer6]
        selected_location = None
        while True:
            text_inst_end.draw()
            for nummer in numbers:
                nummer.draw()
            end_box.draw()
            win.flip()

            
            # End loop if end_box clicked
            if mouse.isPressedIn(end_box):
                break

            # Check mouse clicks and toggle
            for i, nummer in enumerate(numbers, start=1):
                if mouse.isPressedIn(nummer):
                    
                    # Only act if it wasn't clicked in the previous frame
                    if i != selected_location:
                        # Reset previously selected circle
                        if selected_location is not None:
                            numbers[selected_location - 1].color = text_color  # revert old to white
                        nummer.color = 'green'
                        selected_location = i
                    else:
                        nummer.color = text_color  # revert to white
                        selected_location = None
                    
                    while any(mouse.getPressed()):
                        pass  # Just wait. Don't toggle, don't move.
                        
        data[str(index_color)] = selected_location
        
    picks_for_one = data['1']
    picks_for_zero = data['0']
    
    return aware_binary, picks_for_one, picks_for_zero

def singleton_display(trial=None):
    global last_responses

    # raw from https://www.sr-research.com/circular-coordinate-calculator/ with center at 960, 540 and radius of 180, then adjusted to psychopy coordinates
    # make new veriable every call since i will remove coordinates later
    coordinates_for_stimuli = [(960,360), (1116,450), (1116,630), (960,720), (804,630), (804,450)] # Size = 180
    coordinates_for_stimuli = [(x - screen_res[1] / 2, y - screen_res[0] / 2) for x, y in coordinates_for_stimuli]

    coordinates_lines = coordinates_for_stimuli.copy()

    # ColorContext 0 -> singleton/distractor is red
    target_color = colors_singleton_stimuli[int(trial['ColorSingleton'])], 
    distractor_color = colors_singleton_stimuli[int(1 - trial['ColorSingleton'])]
    
    target_diamond.color = target_color
    base_circle.color = target_color
    distractor_circle.color = distractor_color

    target_circle.color = target_color
    base_diamond.color = target_color
    distractor_diamond.color = distractor_color

    mask_diamond.color = background_colors[int(trial['BackgroundContext'])]
    mask_circle.color = background_colors[int(trial['BackgroundContext'])]

    PositionTarget = coordinates_for_stimuli[int(trial['TargetLoc'] - 1)]

    # fixation period
    fixation_period = 0.0001 if config_info['Debug / speed mode'] == 'Yes' else trial['FixationPeriod']

    fixation_dot.draw()
    win.flip()
    time.sleep(fixation_period)

    # clear buffer, needs to be after fixation period
    if not use_keyboard:
        CedrusBox.flush_serial_buffer()
        CedrusBox.clear_response_queue()

    # determine shape of target
    if trial['ShapeSingleton'] == 1:
        target_diamond.pos = PositionTarget
        target_diamond.draw()

        mask_diamond.pos = PositionTarget
        mask_diamond.draw()

        if int(trial['DistLoc']) != 0:
            PositionDistractor = coordinates_for_stimuli[int(trial['DistLoc'] - 1)]
            distractor_circle.pos = PositionDistractor
            distractor_circle.draw()

            mask_circle.pos = PositionDistractor
            mask_circle.draw()

            coordinates_for_stimuli.remove(PositionDistractor)

        coordinates_for_stimuli.remove(PositionTarget)
        for rest in coordinates_for_stimuli:  # show the other locations based on remaining coordinates
            base_circle.pos = rest
            base_circle.draw()

            mask_circle.pos = rest
            mask_circle.draw()

    else:
        target_circle.pos = PositionTarget
        target_circle.draw()

        mask_circle.pos = PositionTarget
        mask_circle.draw()

        if int(trial['DistLoc']) != 0:
            PositionDistractor = coordinates_for_stimuli[int(trial['DistLoc'] - 1)]
            distractor_diamond.pos = PositionDistractor
            distractor_diamond.draw()

            mask_diamond.pos = PositionDistractor
            mask_diamond.draw()

            coordinates_for_stimuli.remove(PositionDistractor)

        coordinates_for_stimuli.remove(PositionTarget)
        for rest in coordinates_for_stimuli:  # toon de andere locaties op basis van resterende coordinaten
            base_diamond.pos = rest
            base_diamond.draw()

            mask_diamond.pos = rest
            mask_diamond.draw()

    # show lines
    for line_pos in coordinates_lines:
        if line_pos == PositionTarget:
            orientation = int(trial['LineOriTarget'])
            orientation_target_line = int(trial['LineOriTarget'])
        else:
            orientation = np.random.choice([0, 90])
        line_shape.ori = orientation
        line_shape.pos = line_pos
        line_shape.draw()

    if response_counterbalance == 0:
        if orientation_target_line == 0:
            CorResp = 0
        else:
            CorResp = 6
    else:
        if orientation_target_line == 0:
            CorResp = 6
        else:
            CorResp = 0

    fixation_dot.draw()
    win.flip()

    # get resp with respbox --------------
    if config_info['Debug / speed mode'] == 'No' and not use_keyboard:
        timer = core.Clock()
        CedrusBox.reset_timer()

        valid_key = False
        while timer.getTime() < max_wait and not valid_key:

            # everytime a key is pressed or time limit is reached this while loop stops
            while not CedrusBox.has_response() and timer.getTime() < max_wait:
                CedrusBox.poll_for_response()

            if CedrusBox.has_response():  # is resp is given
                response = CedrusBox.get_next_response()

                if response['pressed'] == True and response['key'] in allowed_resp_keys:
                    valid_key = True  # to end loop
                    key = response['key']
                    RT = response['time']
            else:  # in case of timeout
                key = None
                RT = None

        last_responses.append(key)

        if all(x == 3 for x in last_responses[-3:]):  # if 3x the middle button close exp
            print('\n\n-------------------------------------------------')
            print('Exit Experiment')
            print('-------------------------------------------------\n\n')
            core.quit()

        correctness = 1 if key == CorResp else 0
    elif use_keyboard:
        key_map = {
            's': 0, 
            'd': 1, 
            'f': 2, 
            'j': 3, 
            'k': 4, 
            'l': 6}
        # Get the response (assuming event.waitKeys() was used)
        timer = core.Clock()
        keys = event.waitKeys(keyList=['s', 'd', 'f', 'j', 'k', 'l'])
        RT = timer.getTime()  
        key = key_map[keys[0]]  # Return the mapped key value  
        correctness = 1 if key == CorResp else 0
            
    else:
        # possible outputs, for speed / test mode
        RT = round(np.random.uniform(low=3, high=2000))
        RT = np.random.choice([RT, None], p=[0.9, 0.1])
        correctness = np.random.choice((0, 1), p=(0.3, 0.7))
        key = np.random.choice((0, 6, -9999))

    return RT, correctness, key

def accuracy_tracker(LastRTs=-99, Resp=0):
    global RTTracker, RespTracker, SkipMessage
    
    if config_info['Debug / speed mode'] == 'Yes' or use_keyboard:
        return None  # skip tracking in debug mode or when using keyboard for testing

    if LastRTs is None:
        RTTracker.append(3000)  # make RT max time, so I can do calculations
    else:
        RTTracker.append(LastRTs)

    RespTracker.append(Resp)
    used = None
    message_text = None
    show_inst = False
    HoeveelTrials = len(RespTracker)

    SkipMessage -= 1  # start at 0, will get below 0, but it does not matter

    if HoeveelTrials >= min_n_trials_for_average_tracking:
        if RespTracker.count(1) / HoeveelTrials < min_accuracy:
            if SkipMessage <= 0:  # if it is below 0 or 0 the message displays
                message_text = (
                    f'Dag {subject_name}, Probeer nauwkeuriger te reageren.\nDruk op een knop om de instructies opnieuw te bekijken')
                SkipMessage = 50  # skip if for the next X times it should go off, in orde to make it possible to recover score but the accuracy is computed for these trials to see progress
                used = f'Accuracy is {RespTracker.count(1) / HoeveelTrials}, min is = {min_accuracy * 100}%'
                show_inst = True
                RespTracker = []

    if HoeveelTrials > check_window_size:
        meanRT = np.mean(RTTracker[-check_window_size:])
        if meanRT >= 3000:  # 3000 = None
            message_text = (f'Dag {subject_name}, Probeer de trials binnen de tijd te voltooien.\n\n'
                            f'Druk op een knop om de verder te gaan')
            used = f'{check_window_size} time out of time'

        elif spam_rt >= meanRT:
            message_text = (
                f'Dag {subject_name}, Probeer alstublieft nauwkeuriger te reageren om ervoor te zorgen dat uw antwoorden correct worden geregistreerd.'
                f'\n\n Druk op een knop om verder te gaan')
            used = f'{check_window_size} to fast'

    if message_text:
        message(message_text=message_text, height=message_text_size)
        time.sleep(max_wait)  # value that is 3 or 0, is what I also need here
        wait_for_cedrus_resp()

        if show_inst:
            message(message_text=start_message, height=message_text_size - 5)
            wait_for_cedrus_resp()

    return used

def cedrus_test():
    text = visual.TextStim(win, text='Press a button')
    devices = pyxid2.get_xid_devices()
    if not devices:
        raise Exception("No port found for the response box, maybe try another USB port on the pc")
    if len(devices) != 1:
        raise Exception("Multiple Ports found for respone box, try and disconnect other serial ports")
    print('Detected Devices:')
    for dev in devices:
        print(dev)

    CedrusBox = devices[0]
    # Stop criterion
    stopExp = False
    text.text = 'Press a Key (Key 6 = Exit)'

    # Keep going until button 6 is pressed
    while not stopExp:
        # Present text

        text.draw()
        win.flip()

        # Reset base timer
        CedrusBox.reset_timer()

        # wait for a response
        while not CedrusBox.has_response():
            CedrusBox.poll_for_response()

        # Process the response
        thisResp = CedrusBox.get_next_response()
        print(thisResp)

        # You can filter out key releases by simply ignoring them
        if thisResp['pressed'] == True:
            # Save variables
            key = thisResp['key']
            RT = thisResp['time']
            Pressed = thisResp['pressed']

            text.text = f"Key: {key}\nRT: {RT}\nPressed: {Pressed} \n(Key 6 = Exit)"
            if key == 6:  # Last key above
                stopExp = True

def wait_for_cedrus_resp(allowed_keys=(0, 1, 2, 3, 4, 5, 6)):
    if config_info['Debug / speed mode'] == 'Yes':
        return 1
    elif use_keyboard:
        key_map = {
            's': 0, 
            'd': 2, 
            'f': 3, 
            'j': 4, 
            'k': 5, 
            'l': 6}
        # Get the response (assuming event.waitKeys() was used)
        keys = event.waitKeys(keyList=['s', 'd', 'f', 'j', 'k', 'l'])
        return key_map[keys[0]]  # Return the mapped key value  
    
    while True:
        # clear buffer before and after just in case
        CedrusBox.flush_serial_buffer()
        CedrusBox.clear_response_queue()

        # wait for a response
        while not CedrusBox.has_response():
            CedrusBox.poll_for_response()

        # Process the response
        thisResp = CedrusBox.get_next_response()
        if thisResp['pressed'] and thisResp['key'] in allowed_keys:
            CedrusBox.flush_serial_buffer()
            CedrusBox.clear_response_queue()
            return thisResp['key']

def generate_random_trial(dist_prop, background_context):
    one_trial = {}
    
    location_options = [1, 2, 3, 4, 5, 6]
    target = np.random.choice(location_options) 
    location_options.remove(target)
 
    one_trial['TargetLoc'] = target
    one_trial['DistLoc'] = np.random.choice(location_options + [0], p=[dist_prop/5]*5 + [1-dist_prop])  # 0 means no distractor
    one_trial['ColorSingleton'] = np.random.choice([0, 1])  
    one_trial['ShapeSingleton'] = np.random.choice([0, 1])  
    one_trial['LineOriTarget'] = np.random.choice([0, 90])  
    one_trial['FixationPeriod'] = np.round(np.random.uniform(1, 1.25), 2)
    one_trial['BackgroundContext'] = background_context
    
    return one_trial

# -----------------------------------------------------------------------------------------------------------
# Parameters
# -----------------------------------------------------------------------------------------------------------
percentage_dist_trials = 0.55
percentage_on_high_freq_loc = 0.45
n_blocks = 3
trials_per_block = (400, 400, 400)  
check_window_size = 3  # window where responses cant go above/below threshold
size_circle = (126, 126)  #size_circle = (108, 108)
size_diamond = (147.0782 / np.sqrt(2), 147.0782 / np.sqrt(2)) # based on De waard 23 (157 px) but then rescaled to visually similar size as circle
target_line_shape = (8, 57)
fixation_dot_radius = 7
shape_thickness = 6
min_accuracy = 0.75
training_trials = 20
max_allowed_abs_diff_between_locs = 6  # controls target distribution on spatial locations
text_size_feedback = 50
message_text_color = 'black'
message_text_size = 30
colors_singleton_stimuli = ['#00c800', '#FF0000']  # green, red,  (0/200/0), (255/0/0)
background_colors = ['#333333', '#cccccc', '#808080']  # dark, light  (51/51/51), (204/204/204)
background_colors_psychopy_version = [-1, 0, 1]  # for text color
text_color_for_background = ['white', 'black', 'black']
target_line_color = '#808080'  # 128, 128, 128
fixation_dot_color = '#999999'  # = 153, 153, 153
singleton_instruction_file = os.path.join(os.getcwd(), 'SingletonInstruction.png')
distractor_combinations = [(4, 1), (1, 4), (3, 6), (6, 3), (2, 5), (5, 2)]  # all hf combinations
screen_res = (1080, 1920)
allowed_resp_keys = (0, 3, 6)
min_n_trials_for_average_tracking = 100
spam_rt = 150  # 150 ms is considered spamming
max_wait = 3
post_wait = 0.150
feedback_duration = 0.350
training_feedback_duration = 1

use_keyboard = False  # use response box or keyboard for responses, for testing purposes

# full factorial design over all participants, made in other script: make_factorial.py
# Total length of each string: 168
factorial_dist       = "330501451240533421022415005320335242140245141513130133452124235241500405343420514014135502052231431544320112503150320425013510325434020235541241214422155534030520013314"
factorial_colororder = "011111111000001100011000101001111001010100111000000110011101010110101010110000110101011001101001111101010100110001110000111000001110001101000111101001010101000001111110"
factorial_resp       = "011101100011110011001000101100100111001000110110110010001110000010111101110110010000101110101010110110101100010110010010011001001101011010101100100000101101011010110101"

colname_dict = {
    'Participant': 0,
    'Block': 1,
    'TotalTrials': 2,
    'TrialsWithinBlock': 3,
    'BlockCounterB': 4,
    'RespCounterB': 5,
    'CurrentHFLoc': 6,
    'DistTrial': 7,
    'DistLoc': 8,
    'TargetLoc': 9,
    'Condition': 10,
    'BackgroundContext': 11,
    'ColorSingleton': 12,
    'ShapeSingleton': 13,
    'LineOriTarget': 14,
    'FixationPeriod': 15,
    'PreviousHF': 16
}

# -----------------------------------------------------------------------------------------------------------
# Initiate variables
# -----------------------------------------------------------------------------------------------------------
accuracy_tracker_training = 0
RTTracker = []
RespTracker = []
block_checker = 0
SkipMessage = 0
last_responses = []

# get resp box
if not use_keyboard:
    devices = pyxid2.get_xid_devices()
    assert devices, 'The response box can not be found, maybe try another usb port'
    CedrusBox = devices[0]
    print('RespBox:', CedrusBox)
else:
    print('Using keyboard for responses, for testing purposes')

# ---------------------------------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------------------------------
gui_check = True
while gui_check:
    # need to do this every iteration
    config_info = {
        "Participant nummer: IMPORTANT Every participant should have unique number (Controls Counterbalance)": '',
        'Debug / speed mode': ['No', 'Yes'],
        'Cedrus check routine (just a quick check, saying yes will only run the test and end the script)': ['No',
                                                                                                            'Yes'],
        'Training': ['Yes', 'No']}

    this_gui = gui.DlgFromDict(dictionary=config_info, title='Config Info, Can press OK, Next is participant GUI',
                               order=[
                                   "Participant nummer: IMPORTANT Every participant should have unique number (Controls Counterbalance)",
                                   "Debug / speed mode",
                                   "Cedrus check routine (just a quick check, saying yes will only run the test and end the script)",
                                   "Training"])  # this also runs the gui

    if not this_gui.OK:
        print('Pressed Cancel')
        core.quit()  # User pressed cancel
    # check on the info
    try:
        int(config_info[
                "Participant nummer: IMPORTANT Every participant should have unique number (Controls Counterbalance)"])
    except:
        continue
    gui_check = False

if config_info[
    'Cedrus check routine (just a quick check, saying yes will only run the test and end the script)'] == 'Yes':
    win = visual.Window(fullscr=True, units='pix', monitor = 'labMonitor')
    cedrus_test()
    win.close()
    core.quit()

# GUI for participant info
gui_check = True
while gui_check:
    # need to do this every iteration
    info = {"Voornaam": "", "Leeftijd": "", "Geslacht": ["M", "V", "X"],
            "Ik ben:": ['Rechtshandig', 'Linkshandig'], 'Heb je normaal kleurenzicht?': ['Ja', 'Nee'],
            'Heb je normaal of gecorrigeerd naar normaal zicht? (Bril/Lenzen)': ['Ja', 'Nee']}

    this_gui = gui.DlgFromDict(dictionary=info, title='Info',
                               order=["Voornaam", "Geslacht", "Leeftijd", "Ik ben:"])  # this also runs the gui

    if not this_gui.OK:
        print('Pressed Cancel')
        core.quit()  # User pressed cancel
    # check on the info
    if not info['Voornaam'].isalpha():
        continue
    try:
        int(info['Leeftijd'])
    except:
        continue
    gui_check = False

# ---------------------------------------------------------------------------------------------------
# Variables Based On User Input
# ---------------------------------------------------------------------------------------------------
if config_info['Debug / speed mode'] == 'Yes':
    max_wait, post_wait, feedback_duration, training_feedback_duration = 0, 0, 0, 0


participant_key = int(config_info["Participant nummer: IMPORTANT Every participant "
                                  "should have unique number (Controls Counterbalance)"])

data_file_path = os.path.join(os.getcwd(), 'DataSingletonExp', f'DataSubject_{str(participant_key).zfill(2)}')

if os.path.exists(data_file_path + '.csv'):
    print('This file already exists, making new one')
    data_file_path = os.path.join(os.getcwd(), 'DataSingletonExp', f'DataSubject_{np.random.randint(400, 600)}')


distractors = distractor_combinations[int(factorial_dist[int(participant_key - 1)])]
counterbalance_for_color_order = int(factorial_colororder[int(participant_key - 1)])
response_counterbalance = int(factorial_resp[int(participant_key - 1)])

color_order = (0, 1) if counterbalance_for_color_order == 0 else (1, 0)

distractors_if_background_one = distractors[color_order.index(1)]
distractors_if_background_zero = distractors[color_order.index(0)]

resp_keys = ('linker', 'rechter') if response_counterbalance == 0 else ('rechter', 'linker')

subject_name = info["Voornaam"].title()
info.pop("Voornaam")

# ---------------------------------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------------------------------

break_message = ('Neem nu even pauze en ga verder wanneer '
                 'je klaar bent. \n\n Druk op een knop als je klaar bent om verder te gaan')

context_message = f'Let op: de achtergrond zal voor de volgende fase van kleur veranderen. \n' \
                  f'\nDruk op een knop om verder te gaan wanneer je er klaar voor bent. '

intermixed_message = ('Goed bezig, je bent bijna klaar. \nDe kleur van de achtergrond zal nu afwisselen. '
                      '\n\n Druk op een knop om verder te gaan')

trials_done_message = 'Je hebt alle trials doorlopen, goed gedaan!\n\n Druk op een knop om verder te gaan'

end_message = (f"Beste {subject_name},\n\nDit is het einde van het experiment. Hartelijk bedankt "
               f"voor je waardevolle deelname!\n\n Druk op een knop om het experiment correct af te sluiten.")

visual_instruction_message = (f'Streepje rechtop = {resp_keys[0]} knop.\n'
                              f'Streepje plat = {resp_keys[1]} knop')

after_practice_message = ("Het echte experiment gaat nu van start! Tijdens het experiment zullen er momenten "
                          "worden aangegeven waarop je een pauze kunt nemen.\n\nWe geven vanaf nu ook enkel feedback als je fout of te traag bent\n\n"
                          "Druk op een knop om te starten.")

# ---------------------------------------------------------------------------------------------------
# Visuals
# ---------------------------------------------------------------------------------------------------
# start with neutral background for instructions etc
win = visual.Window(size = [1920, 1080], fullscr=True, units='pix', color= "#808080", monitor = 'labMonitor')
win.mouseVisible = False

fixation_dot = visual.Circle(win, radius=fixation_dot_radius, color='black')
line_shape = visual.rect.Rect(win, size=target_line_shape, fillColor='black', ori=40, pos=(-196, 175))

# one set
target_diamond = visual.rect.Rect(win, size=size_diamond, ori=45)
distractor_circle = visual.Circle(win, size=size_circle)
base_circle = visual.Circle(win, size=size_circle)

# other set
target_circle = visual.Circle(win, size=size_circle)
distractor_diamond = visual.rect.Rect(win, size=size_diamond, ori=45)
base_diamond = visual.rect.Rect(win, size=size_diamond, ori=45)

mask_size_circle = [i - shape_thickness * 2 for i in size_circle]
mask_size_diamond = [i - shape_thickness * 2 for i in size_diamond]

# laying mask over full colored shapes makes them look better, not noisy
mask_circle = visual.Circle(win, size=mask_size_circle)
mask_diamond = visual.rect.Rect(win, size=mask_size_diamond, ori=45)


# ---------------------------------------------------------------------------------------------------
# Design Matrix
# ---------------------------------------------------------------------------------------------------

design_matrix = np.full((sum(trials_per_block), len(colname_dict)), np.nan)  # empty nan matrix
for block in range(n_blocks):
    n_trials_this_block = trials_per_block[block]

    # make target locations
    reps_target = np.floor(n_trials_this_block / 6)
    targets_equal_prob = np.repeat((1, 2, 3, 4, 5, 6), reps_target)  # equal times over all trials
    target_extra = np.random.choice((1, 2, 3, 4, 5, 6),
                                    int(n_trials_this_block - len(targets_equal_prob)))  # due to floor
    all_targets_for_one_block = np.concatenate((targets_equal_prob, target_extra))  # extra to correct for rounding

    np.random.shuffle(all_targets_for_one_block)

    # if else for dist and background
    if block == 0 or block == 1:
        hf_current_block = distractors[block]  # distractor for this block

        all_locations = [1, 2, 3, 4, 5, 6]
        all_locations.remove(hf_current_block)  # remove the current distractor from list

        reps_for_high = np.floor(n_trials_this_block * percentage_dist_trials * percentage_on_high_freq_loc)
        reps_low = np.floor(n_trials_this_block * percentage_dist_trials * (1 - percentage_on_high_freq_loc) / 5)

        high_distractor = np.repeat(hf_current_block, reps_for_high)  # make distractor matrix
        low_distractor = np.repeat(all_locations, reps_low)  # all locations without distractor

        n_no_dist_trials = n_trials_this_block - (len(low_distractor) + len(high_distractor))  # get remaining trials for no distractor
        no_distractor = np.repeat(0, n_no_dist_trials)  # add no distractor presentations

        all_distractor_for_one_block = np.concatenate((low_distractor, high_distractor, no_distractor))

        np.random.shuffle(all_distractor_for_one_block)

        # color_order is either (1, 0) or (0, 1)
        background_images_binary = np.repeat(color_order[block], n_trials_this_block)


    if block == 2:
        # in last block determine background contex
        # randomize this last block in 2 parts for every background context, for equal prob for each, then combine
        half_n_trials = n_trials_this_block / 2  # set it to half for this block

        # Distractors
        n_no_dist_trials = np.floor(half_n_trials * (1 - percentage_dist_trials))

        no_distractor = np.repeat(0, n_no_dist_trials)  # add no distractor presentations
        distractors_trials = np.repeat(range(6), np.floor((half_n_trials - n_no_dist_trials) / 6)) + 1

        # fill in leftover trials with hf locations due to rounding
        number_extra = np.floor((half_n_trials - (len(distractors_trials) + len(no_distractor))) / 2)
        dist_extra = np.repeat(distractors, number_extra)  # but as much extra of the HF locs
        how_much_extra = int(half_n_trials - (len(distractors_trials) + len(no_distractor) + len(dist_extra)))
        dist_extra_extra = np.random.choice(distractors, size=how_much_extra)
        all_distractor_for_one_block = np.concatenate((distractors_trials, no_distractor, dist_extra, dist_extra_extra))

        # important 2 shuffles
        np.random.shuffle(all_distractor_for_one_block)
        first_half_distractors = all_distractor_for_one_block.copy()

        np.random.shuffle(all_distractor_for_one_block)  # shuflle again
        second_half_distractors = all_distractor_for_one_block.copy()

        # another sanity check
        halves_are_different = not np.all(second_half_distractors == first_half_distractors)  # inverse of equal
        assert halves_are_different, 'The half in last block are not mixed, error with shuflle in this last block'

        all_distractor_for_one_block = np.concatenate((first_half_distractors, second_half_distractors))

        # add exta col for background locations
        combined_matrix = np.vstack((all_distractor_for_one_block, np.repeat((0, 1), half_n_trials))).T

        # this shuffles the matrix rows, so background order is switched
        # but with same number of dist between backgrounds

        # can control for amount of background repeats here if needed
        np.random.shuffle(combined_matrix)

        all_distractor_for_one_block = combined_matrix[:, 0]
        background_images_binary = combined_matrix[:, 1]

    # assume it has for first time, saves a few checks
    have_overlap = True
    bad_target_distribution = True

    # get abs values on locs, and 'simulate' the difference, then calc proportions
    abs_per_loc = np.array([np.count_nonzero(all_targets_for_one_block == i) for i in range(1, 7)])
    abs_per_loc[0] -= np.floor(max_allowed_abs_diff_between_locs / 2)
    abs_per_loc[1] += np.ceil(max_allowed_abs_diff_between_locs / 2)
    abs_per_loc = np.array(abs_per_loc) / abs_per_loc.sum()
    lower_bound = np.min(abs_per_loc)
    upper_bound = np.max(abs_per_loc)

    while have_overlap or bad_target_distribution:
        # initialize for every loop bc you change it in this loop and want independent tries
        all_targets_for_one_block = np.concatenate((targets_equal_prob, target_extra))  # extra to correct for rounding

        # shuffle it again every iteration
        np.random.shuffle(all_targets_for_one_block)

        overlap_indices = np.where(all_targets_for_one_block == all_distractor_for_one_block)[0]
        for i in overlap_indices:
            all_options = [1, 2, 3, 4, 5, 6]
            all_options.remove(all_targets_for_one_block[i])  # remove the overlapping value
            all_targets_for_one_block[i] = np.random.choice(all_options)  # pick other option that is not the same

        # check target proportions per location, normally is about 0.1666
        target_proportions_per_loc = np.array(
            [np.count_nonzero(all_targets_for_one_block == i) / n_trials_this_block for i in range(1, 7)])

        bad_target_distribution = not np.all(
            (lower_bound <= target_proportions_per_loc) & (target_proportions_per_loc <= upper_bound))
        have_overlap = not np.all(all_targets_for_one_block != all_distractor_for_one_block)

    # sanity check
    all_different = np.all(all_targets_for_one_block != all_distractor_for_one_block)
    target_proportions_per_loc = np.array(
        [np.count_nonzero(all_targets_for_one_block == i) / n_trials_this_block for i in range(1, 7)])
    good_target_distribution = np.all(
        (lower_bound <= target_proportions_per_loc) & (target_proportions_per_loc <= upper_bound))

    assert all_different, "Targets and Distractors cant have the same location in same trial."
    assert good_target_distribution, 'Targets have bad distribution for spatial locations'

    # get current trials indices
    currentTrials = (np.arange(trials_per_block[0]), np.arange(trials_per_block[0], trials_per_block[0] * 2),
                     np.arange(trials_per_block[0] * 2, trials_per_block[0] * 2 + trials_per_block[2]),
                     np.arange(trials_per_block[0] * 2 + trials_per_block[2], sum(trials_per_block)))[block]

    design_matrix[currentTrials, colname_dict['Participant']] = participant_key
    design_matrix[currentTrials, colname_dict['Block']] = block
    design_matrix[currentTrials, colname_dict['BlockCounterB']] = counterbalance_for_color_order
    design_matrix[currentTrials, colname_dict['TotalTrials']] = currentTrials
    design_matrix[currentTrials, colname_dict['TrialsWithinBlock']] = np.arange(trials_per_block[block])
    design_matrix[currentTrials, colname_dict['RespCounterB']] = response_counterbalance  # flips response options
    design_matrix[currentTrials, colname_dict['BackgroundContext']] = background_images_binary
    design_matrix[currentTrials, colname_dict['ColorSingleton']] = np.random.choice((0, 1), size=n_trials_this_block)
    design_matrix[currentTrials, colname_dict['ShapeSingleton']] = np.random.choice((0, 1), size=n_trials_this_block)
    design_matrix[currentTrials, colname_dict['LineOriTarget']] = np.random.choice((0, 90), size=n_trials_this_block)
    design_matrix[currentTrials, colname_dict['FixationPeriod']] = np.round(
        np.random.uniform(1, 1.25, size=n_trials_this_block), 2)
    design_matrix[currentTrials, colname_dict['CurrentHFLoc']] = np.where(background_images_binary == 1,
                                                                          distractors_if_background_one,
                                                                          distractors_if_background_zero)
    design_matrix[currentTrials, colname_dict['DistTrial']] = np.where(all_distractor_for_one_block == 0, 0, 1)
    design_matrix[currentTrials, colname_dict['DistLoc']] = all_distractor_for_one_block
    design_matrix[currentTrials, colname_dict['TargetLoc']] = all_targets_for_one_block

    # flip logic of 'CurrentHFLoc'
    design_matrix[currentTrials, colname_dict['PreviousHF']] = np.where(background_images_binary == 0,
                                                                        distractors_if_background_one,
                                                                        distractors_if_background_zero)

    # Mapping dictionary, make it here so it is clear what numbers mean
    mapping = {
        10: "HF_ThisContext",
        11: "HF_OtherContext",
        12: "LF",
        13: "NoDist",
        14: "Match",
        15: "Mismatch"
    }

    current_hf = design_matrix[currentTrials, colname_dict['CurrentHFLoc']]
    other_context_hf = design_matrix[currentTrials, colname_dict['PreviousHF']]

    condition_arr = np.where(all_distractor_for_one_block == current_hf, 10, 12)
    condition_arr = np.where(all_distractor_for_one_block == other_context_hf, 11, condition_arr)
    condition_arr = np.where(all_distractor_for_one_block == 0, 13, condition_arr)

    if block == 2:
        condition_arr = np.where(background_images_binary == 0,
                                 np.where(all_distractor_for_one_block == distractors_if_background_zero, 14,
                                          condition_arr),
                                 np.where(all_distractor_for_one_block == distractors_if_background_one, 14,
                                          condition_arr))

        condition_arr = np.where(background_images_binary == 0,
                                 np.where(all_distractor_for_one_block == distractors_if_background_one, 15,
                                          condition_arr),
                                 np.where(all_distractor_for_one_block == distractors_if_background_zero, 15,
                                          condition_arr))

        condition_arr = np.where(all_distractor_for_one_block == 0, 13, condition_arr)

    design_matrix[currentTrials, colname_dict['Condition']] = condition_arr

# sorted_items is now a list of tuples ordered by column index, so order in colname_dict does not matter
columns_sorted_by_index = [k for k, v in sorted(colname_dict.items(), key=lambda item: item[1])]

# sanity check
assert not np.isnan(design_matrix).any(), "Design matrix contains NaN values!"
assert np.all(
    np.arange(len(colname_dict)) == [colname_dict[i] for i in columns_sorted_by_index]), 'Check Col_name order'

df_design_matrix = pd.DataFrame.from_records(design_matrix)
df_design_matrix.columns = columns_sorted_by_index
df_design_matrix['Condition'] = df_design_matrix['Condition'].replace(mapping)

print('\nDesign Matrix Created, starting experiment...\n')

# ---------------------------------------------------------------------------------------------------
# Experiment Handler
# ---------------------------------------------------------------------------------------------------

ThisExp = data.ExperimentHandler(dataFileName=data_file_path, extraInfo=info)  # file_name where to store csv
trial_list = pd.DataFrame.to_dict(df_design_matrix, orient='records')

trials = data.TrialHandler(trial_list, nReps=1, method='sequential')
ThisExp.addLoop(trials)

# Start Experiment
DurationTimer = core.Clock()

# Visual of instructions
visual_inst = visual.ImageStim(win, image = os.path.join(os.getcwd(), 'Instructions', 'Welcome.png'))
visual_inst.draw()
win.flip()
wait_for_cedrus_resp()

for instructionImage in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
    visual_inst.image = os.path.join(os.getcwd(), 'Instructions', f"Instructions{instructionImage}.png")
    visual_inst.draw()
    if instructionImage == 5:
        message(message_text=visual_instruction_message, height=message_text_size, pos=(-600, 0), bold=True)
    elif instructionImage in [9, 10]:
        message(message_text=visual_instruction_message, height=message_text_size, pos=(0, -200), bold=True)
    else:
        win.flip()
    wait_for_cedrus_resp()

# ---------------------------------------------------------------------------------------------------
# Practice Trials
# ---------------------------------------------------------------------------------------------------
if config_info['Training'] == 'Yes':
    while accuracy_tracker_training < training_trials * min_accuracy:
        print('\nStarting training trials\n')
        # place it here so every file has this col
        trials.addData("AccuracyMessagerIsUsed", 'PracticeStarted')

        for _ in range(training_trials):
            r_trial = generate_random_trial(percentage_dist_trials, 2) # generate a fully random trial
            RT, correctness, _ = singleton_display(trial=r_trial)

            accuracy_tracker_training += 0 if correctness is None else correctness

            if correctness == 0:
                message(message_text='Oeps!', duration=training_feedback_duration, height=text_size_feedback)
            elif correctness == 1:
                message(message_text='Juist!', duration=training_feedback_duration, height=text_size_feedback)
            else:
                message(message_text='Probeer sneller te antwoorden', duration=training_feedback_duration, height=text_size_feedback)

            time.sleep(post_wait)

        if trials_per_block[0] < training_trials + 5 or config_info['Debug / speed mode'] == 'Yes':
            break  # end the loop, so you do not need correct answers

# ---------------------------------------------------------------------------------------------------
# Start Experiment
# ---------------------------------------------------------------------------------------------------
print('\nStart Real Trials...\n')
message(message_text=after_practice_message, height=message_text_size, duration=2)
wait_for_cedrus_resp()

line_shape.fillColor = target_line_color
fixation_dot.color = fixation_dot_color

for trial in trials:

    if trial['Block'] != block_checker:  # Block breaks
        block_checker = trial['Block']
        message(message_text=break_message, height=message_text_size, duration=2)
        wait_for_cedrus_resp()

        if block_checker == 1:
            message(message_text=context_message, height=message_text_size, duration=2)
            wait_for_cedrus_resp()
            RespTracker = []

        elif block_checker == 2:
            message(message_text=intermixed_message, height=message_text_size, duration=2)
            wait_for_cedrus_resp()
            RespTracker = []

    if trial['Block'] != 2 and trial['TrialsWithinBlock'] == int(trials_per_block[0] / 2):
        message(message_text=break_message, height=message_text_size, duration=2)
        wait_for_cedrus_resp()

    win.color = background_colors[int(trial['BackgroundContext'])]
    fixation_dot.draw()  # draw it here so it does not flicker
    win.flip()

    time.sleep(post_wait)  # post trial wait but, before trial so fix period is already with current trial background

    RT, correctness, what_key = singleton_display(trial=trial)

    if what_key is None:
        message(message_text='Probeer sneller te antwoorden', duration=feedback_duration, height=text_size_feedback)
    elif correctness == 0:  # Feedback only if not correct
        message(message_text='Oeps!', duration=feedback_duration, height=text_size_feedback)

    used_tracker = accuracy_tracker(LastRTs=RT, Resp=correctness)
    if used_tracker:
        trials.addData("AccuracyMessagerIsUsed", used_tracker)

    trials.addData("CorrectnessResp", correctness)
    trials.addData("RT", RT)
    trials.addData("KeyPressed", what_key)
    ThisExp.nextEntry()

message(message_text=trials_done_message, height=message_text_size, duration=2)
wait_for_cedrus_resp()

# last questions of experiment
aware_binary, picks_for_one, picks_for_zero = conscience_detection()

# End the experiment
message(message_text=end_message, height=message_text_size)
event.waitKeys(maxWait=100)

# this will be on the last row only
ThisExp.extraInfo['reported_locations_for_zero'] = picks_for_zero
ThisExp.extraInfo['reported_locations_for_one'] = picks_for_one
ThisExp.extraInfo['reported_locations_binary'] = aware_binary
ThisExp.extraInfo['Accuracy'] = round(RespTracker.count(1) / sum(trials_per_block), 2)
ThisExp.nextEntry()
ThisExp.close()

print('\n\n---------------------------------------------------------------------------------------------------')
print('Done, no errors')
print(f"Data will be saved to: {data_file_path}.csv")
print(f"Total Experiment Time: {round(DurationTimer.getTime() / 60, 2)} minutes\n")
print('---------------------------------------------------------------------------------------------------\n\n')
