#audiorecognition

import os
import time
from slackclient import SlackClient
import pyttsx
from os import system
import speech_recognition as sr
r = sr.Recognizer()
m = sr.Microphone()

# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants

AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "line "
num=1
haiku=""
speech=""
# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

from PyDictionary import PyDictionary
dictionary = PyDictionary()

specials = ["the", "an","a", "and", "or", "both","is", "am", "are", "was","in"]
pronouns = ["he","his", "she", "her", "me", "I", "we", "us","they","them"]

def handle_command(command,channel):
    global num
    global haiku
    global speech
    num_syllables=5
    if command=="haiku":
        haiku="Your haiku: \n"
        num=1
        slack_client.api_call("chat.postMessage", channel=channel,text="Sure I would love to help you with your haiku. Enter line 1 of your haiku.", as_user=True)
    elif num>3:
        slack_client.api_call("chat.postMessage", channel=channel, text="That's too many lines for your haiku! Please start again using the keyword haiku.", as_user=True)
    elif command=="audio":
    	command="line 1: " + audiorecognizer()
    	handle_command(command,channel)
    elif command.startswith(EXAMPLE_COMMAND):
        if num==2:
            num_syllables=7
        elif num==1 or num==3:
            num_syllables=5
        actual_no_of_syllables = 0
        new_command = scrub_n_split(command[7:])
        for i in new_command:
            actual_no_of_syllables += syllables(i)
        if actual_no_of_syllables==num_syllables:
            num+=1
            speech = speech + " " + command[7:]
            haiku=haiku+ " " + command[7:] + "\n"
            if num<=3:
                slack_client.api_call("chat.postMessage", channel=channel, text="Nice job on Line " + str(num-1) + " of the haiku! Now enter line " + str(num) + "!", as_user=True)
            else:
                slack_client.api_call("chat.postMessage", channel=channel, text="Congratulations on your haiku!", as_user=True)
                system('say '+speech)
                slack_client.api_call("chat.postMessage", channel=channel, text=haiku, as_user=True)
        else:
            suggest_edits(command[7:],num_syllables)

    elif command.startswith("define"):
        slack_client.api_call("chat.postMessage", channel=channel, text=define(command[7:]), as_user=True)

    elif command.startswith("translate"):
        print('command: ', command[9:])
        slack_client.api_call("chat.postMessage", channel=channel, text=translate_to_spanish(command[9:]), as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


def syllables(word):
    count = 0
    vowels = 'aeiouy'
    word = word.lower().strip(".:;?!")
    if word[0] in vowels:
        count += 1
    for index in range(1,len(word)):
        if word[index] in vowels and word[index-1] not in vowels:
            count += 1
    if word == "business":
        return 2
    if word.endswith('e'):
        count -= 1
    if word.endswith('le'):
        count+=1
    if word.endswith('ed'):
        count -= 1
    if word.endswith("ted"):
        count += 1
    if word.endswith("ing"):
        index = word.find("ing")
        if word[(index - 1)] in vowels:
            count += 1
    if word.endswith("lle"):
        count -= 1
    if count == 0:
        count +=1
    return count


def translate_to_spanish(word):
    return dictionary.translate(word,"es")

def define(word):
    return dictionary.meaning(word)   

def scrub_n_split(line):
    scrubbed_line = ""
    for char in line:
        if char.isalpha() or char==" ":
            scrubbed_line += char.lower()
    return scrubbed_line.split()

def combs_lister(words):
    syls_table= [[(w, syllables(w))] for w in words]
    for word_set in syls_table:
        w = word_set[0][0]
        w_syns = dictionary.synonym(w)
        if w in specials or w in pronouns or not w_syns:
            continue
        for syn in w_syns:
            word_set.append((syn, syllables(syn)))
    return syls_table

def combs_maker(syls_table, needed):
    valid_combs = []
    def combs_maker_helper(current_comb, table_index, remaining):
        if table_index==len(syls_table):
            if remaining==0:
                valid_combs.append(current_comb)
        else:
            for next_word in syls_table[table_index]:
                combs_maker_helper(current_comb+[next_word], table_index+1, remaining-next_word[1])
    combs_maker_helper([], 0, needed)
    return valid_combs

############### API ###################

def print_comb(valid_comb):
    sentence = ""
    for valid_word in valid_comb:
        sentence+=(valid_word[0] + ' ')
    slack_client.api_call("chat.postMessage", channel=channel,text="-" + sentence, as_user=True)


def print_all_valids(valid_combs):
    if valid_combs:
        slack_client.api_call("chat.postMessage", channel=channel,text="Here are some suggested edits for this line: ", as_user=True)
        for valid_comb in valid_combs:
            print_comb(valid_comb)
    else:
        slack_client.api_call("chat.postMessage", channel=channel,text="Here are some suggested edits for this line: ", as_user=True)

def print_smart_valids(valid_combs):
    if valid_combs:
        cache = []
        slack_client.api_call("chat.postMessage", channel=channel,text="Here are some suggested edits for this line: ", as_user=True)
        for valid_comb in valid_combs:
            do_print = False
            for word in valid_comb:
                if word not in cache:
                    cache.append(word)
                    do_print = True
            if do_print:
                print_comb(valid_comb)
    else:
        slack_client.api_call("chat.postMessage", channel=channel,text="No valid suggestions. ", as_user=True)

def suggest_edits(line, l_num):
    print_smart_valids((combs_maker(combs_lister(scrub_n_split(line)), l_num)))
    # print_all_valids((combs_maker(combs_lister(scrub_n_split(line)), l_num)))
def audiorecognizer():
	global s
	global r
	try:
	    print("A moment of silence, please...")
	    with m as source: r.adjust_for_ambient_noise(source)
	    print("Set minimum energy threshold to {}".format(r.energy_threshold))
	    for i in range(1):
	        print("Say something!")
	        with m as source: audio = r.listen(source)
	        print("Got it! Now to recognize it...")
	        try:
	            # recognize speech using Google Speech Recognition
	            value = r.recognize_google(audio)
	            print(value)
	            return value

	            # we need some special handling here to correctly print unicode characters to standard output
	            if str is bytes: # this version of Python uses bytes for strings (Python 2)
	                
	                print(u"You said {}".format(value).encode("utf-8"))
	            else: # this version of Python uses unicode for strings (Python 3+)
	                print("You said {}".format(value))
	        except sr.UnknownValueError:
	            print("Oops! Didn't catch that")
	        except sr.RequestError as e:
	            print("Uh oh! Couldn't request results from Google Speech Recognition service; {0}".format(e))
	except KeyboardInterrupt:
	    pass



if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")





