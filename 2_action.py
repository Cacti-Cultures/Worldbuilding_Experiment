import os
import openai
import time
from random import seed, choice
from uuid import uuid4
import threading
import sys
import signal
from dotenv import load_dotenv

# Create a Spinner class
class Spinner:
    def __init__(self):
        self._running = True

    def terminate(self):
        self._running = False

    def spinner(self):
        while self._running:
            for state in ['\\', '|', '/', '-']:
                sys.stdout.write('\rLoading ' + state)
                sys.stdout.flush()
                time.sleep(0.1)  # use time.sleep instead of sleep

spinner_obj = None

def signal_handler(sig, frame):
    global spinner_obj
    if spinner_obj is not None:
        spinner_obj.terminate()  # Stop the spinner.
    sys.stdout.write('\r')
    sys.stdout.flush()
    print('Exiting...')
    sys.exit(0)

# Load the environment variables from the .env file
load_dotenv(verbose=True)

# Retrieve the environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
temperature = float(os.getenv("TEMPERATURE", "0.7"))
model = os.getenv("MODEL")

# Use the environment variables
openai.api_key = openai_api_key

seed()

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        return infile.read()

def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

def chatgpt_completion(messages):
    global spinner_obj
    spinner_obj = Spinner()
    spinner_thread = threading.Thread(target=spinner_obj.spinner)  # Create a new spinner thread.
    spinner_thread.start()  # Start the spinner thread.
    max_retry = 7
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature) # use the global model and temperature variables here
            text = response['choices'][0]['message']['content']
            spinner_obj.terminate()  # Stop the spinner.
            spinner_thread.join()  # Wait for the spinner thread to finish.
            # Clear the spinner before returning.
            sys.stdout.write('\r')
            sys.stdout.flush()
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                print(f"\rExiting due to an error in ChatGPT: {oops}")
                sys.exit(1)  # Used sys.exit() here for better compatibility and readability.
            print(f'\rError communicating with OpenAI: "{oops}" - Retrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    scenario_folder = 'scenarios'
    action_folder = 'actions'
    
    system_message = open_file('system_action.txt')

    for scenario_file in os.listdir(scenario_folder):
        scenario_filepath = os.path.join(scenario_folder, scenario_file)
        action_filepath = os.path.join(action_folder, scenario_file)


        if os.path.exists(action_filepath):
            continue

        scenario = open_file(scenario_filepath)
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": scenario},
        ]
        action = chatgpt_completion(messages)
        print('\n\n===============\n\n\nScenario:\n', scenario, '\n\nAction:\n', action)
        save_file(action_filepath, action)
    exit()
