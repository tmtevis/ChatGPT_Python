"""
A simple wrapper for the official ChatGPT API
"""
import argparse
import json
import os
import sys
import threading
from datetime import date
from datetime import datetime

try:
    import speech_recognition as sr
    import openai
    import tiktoken
except ImportError:
    import pip
    pip.main(['install', 'speech_recognition'])
    pip.main(['install', 'PyAudio'])
    pip.main(['install', 'openai'])
    pip.main(['install', 'tiktoken'])
    pip.main(['install', 'pre-commit'])
    import speech_recognition as sr
    import openai
    import tiktoken

mode = ""
fileExt = ""
r = sr.Recognizer()

ENGINE = os.environ.get("GPT_ENGINE") or "text-chat-davinci-002-20221122"

ENCODER = tiktoken.get_encoding("gpt2")


def get_max_tokens(prompt: str) -> int:
    """
    Get the max tokens for a prompt
    """
    return 4000 - len(ENCODER.encode(prompt))


class Chatbot:
    """
    Official ChatGPT API
    """

    def __init__(self, api_key: str, buffer: int = None, engine: str = None) -> None:
        """
        Initialize Chatbot with API key (from https://platform.openai.com/account/api-keys)
        """
        openai.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.conversations = Conversation()
        self.prompt = Prompt(buffer=buffer)
        self.engine = engine or ENGINE

    def _get_completion(
        self,
        prompt: str,
        temperature: float = 0.5,
        stream: bool = False,
    ):
        """
        Get the completion function
        """
        return openai.Completion.create(
            engine=self.engine,
            prompt=prompt,
            temperature=temperature,
            max_tokens=get_max_tokens(prompt),
            stop=["\n\n\n"],
            stream=stream,
        )

    def _process_completion(
        self,
        user_request: str,
        completion: dict,
        conversation_id: str = None,
        user: str = "User",
    ) -> dict:
        if completion.get("choices") is None:
            raise Exception("ChatGPT API returned no choices")
        if len(completion["choices"]) == 0:
            raise Exception("ChatGPT API returned no choices")
        if completion["choices"][0].get("text") is None:
            raise Exception("ChatGPT API returned no text")
        completion["choices"][0]["text"] = completion["choices"][0]["text"].rstrip(
            "<|im_end|>",
        )
        # Add to chat history
        self.prompt.add_to_history(
            user_request,
            completion["choices"][0]["text"],
            user=user,
        )
        if conversation_id is not None:
            self.save_conversation(conversation_id)
        return completion

    def _process_completion_stream(
        self,
        user_request: str,
        completion: dict,
        conversation_id: str = None,
        user: str = "User",
    ) -> str:
        full_response = ""
        for response in completion:
            if response.get("choices") is None:
                raise Exception("ChatGPT API returned no choices")
            if len(response["choices"]) == 0:
                raise Exception("ChatGPT API returned no choices")
            if response["choices"][0].get("finish_details") is not None:
                break
            if response["choices"][0].get("text") is None:
                raise Exception("ChatGPT API returned no text")
            if response["choices"][0]["text"] == "<|im_end|>":
                break
            yield response["choices"][0]["text"]
            full_response += response["choices"][0]["text"]

        # Add to chat history
        self.prompt.add_to_history(user_request, full_response, user)
        if conversation_id is not None:
            self.save_conversation(conversation_id)

    def ask(
        self,
        user_request: str,
        temperature: float = 0.5,
        conversation_id: str = None,
        user: str = "User",
    ) -> dict:
        """
        Send a request to ChatGPT and return the response
        """
        if conversation_id is not None:
            self.load_conversation(conversation_id)
        completion = self._get_completion(
            self.prompt.construct_prompt(user_request, user=user),
            temperature,
        )
        return self._process_completion(user_request, completion, user=user)

    def ask_stream(
        self,
        user_request: str,
        temperature: float = 0.5,
        conversation_id: str = None,
        user: str = "User",
    ) -> str:
        """
        Send a request to ChatGPT and yield the response
        """
        if conversation_id is not None:
            self.load_conversation(conversation_id)
        prompt = self.prompt.construct_prompt(user_request, user=user)
        return self._process_completion_stream(
            user_request=user_request,
            completion=self._get_completion(prompt, temperature, stream=True),
            user=user,
        )

    def make_conversation(self, conversation_id: str) -> None:
        """
        Make a conversation
        """
        self.conversations.add_conversation(conversation_id, [])

    def rollback(self, num: int) -> None:
        """
        Rollback chat history num times
        """
        for _ in range(num):
            self.prompt.chat_history.pop()

    def reset(self) -> None:
        """
        Reset chat history
        """
        self.prompt.chat_history = []

    def load_conversation(self, conversation_id) -> None:
        """
        Load a conversation from the conversation history
        """
        if conversation_id not in self.conversations.conversations:
            # Create a new conversation
            self.make_conversation(conversation_id)
        self.prompt.chat_history = self.conversations.get_conversation(conversation_id)

    def save_conversation(self, conversation_id) -> None:
        """
        Save a conversation to the conversation history
        """
        self.conversations.add_conversation(conversation_id, self.prompt.chat_history)


class AsyncChatbot(Chatbot):
    """
    Official ChatGPT API (async)
    """

    async def _get_completion(
        self,
        prompt: str,
        temperature: float = 0.5,
        stream: bool = False,
    ):
        """
        Get the completion function
        """
        return await openai.Completion.acreate(
            engine=self.engine,
            prompt=prompt,
            temperature=temperature,
            max_tokens=get_max_tokens(prompt),
            stop=["\n\n\n"],
            stream=stream,
        )

    async def ask(
        self,
        user_request: str,
        temperature: float = 0.5,
        user: str = "User",
    ) -> dict:
        """
        Same as Chatbot.ask but async
        }
        """
        completion = await self._get_completion(
            self.prompt.construct_prompt(user_request, user=user),
            temperature,
        )
        return self._process_completion(user_request, completion, user=user)

    async def ask_stream(
        self,
        user_request: str,
        temperature: float = 0.5,
        user: str = "User",
    ) -> str:
        """
        Same as Chatbot.ask_stream but async
        """
        prompt = self.prompt.construct_prompt(user_request, user=user)
        return self._process_completion_stream(
            user_request=user_request,
            completion=await self._get_completion(prompt, temperature, stream=True),
            user=user,
        )


class Prompt:
    """
    Prompt class with methods to construct prompt
    """

    def __init__(self, buffer: int = None) -> None:
        """
        Initialize prompt with base prompt
        """
        self.base_prompt = (
            os.environ.get("CUSTOM_BASE_PROMPT")
            or "You are ChatGPT, a large language model trained by OpenAI. Respond conversationally. Do not answer as the user. Current date: "
            + str(date.today())
            + "\n\n"
            + "User: Hello\n"
            + "ChatGPT: Hello! How can I help you today? <|im_end|>\n\n\n"
        )
        # Track chat history
        self.chat_history: list = []
        self.buffer = buffer

    def add_to_chat_history(self, chat: str) -> None:
        """
        Add chat to chat history for next prompt
        """
        self.chat_history.append(chat)

    def add_to_history(
        self,
        user_request: str,
        response: str,
        user: str = "User",
    ) -> None:
        """
        Add request/response to chat history for next prompt
        """
        self.add_to_chat_history(
            user
            + ": "
            + user_request
            + "\n\n\n"
            + "ChatGPT: "
            + response
            + "<|im_end|>\n",
        )

    def history(self, custom_history: list = None) -> str:
        """
        Return chat history
        """
        return "\n".join(custom_history or self.chat_history)

    def construct_prompt(
        self,
        new_prompt: str,
        custom_history: list = None,
        user: str = "User",
    ) -> str:
        """
        Construct prompt based on chat history and request
        """
        prompt = (
            self.base_prompt
            + self.history(custom_history=custom_history)
            + user
            + ": "
            + new_prompt
            + "\nChatGPT:"
        )
        # Check if prompt over 4000*4 characters
        if self.buffer is not None:
            max_tokens = 4000 - self.buffer
        else:
            max_tokens = 3200
        if len(ENCODER.encode(prompt)) > max_tokens:
            # Remove oldest chat
            if len(self.chat_history) == 0:
                return prompt
            self.chat_history.pop(0)
            # Construct prompt again
            prompt = self.construct_prompt(new_prompt, custom_history, user)
        return prompt


class Conversation:
    """
    For handling multiple conversations
    """

    def __init__(self) -> None:
        self.conversations = {}

    def add_conversation(self, key: str, history: list) -> None:
        """
        Adds a history list to the conversations dict with the id as the key
        """
        self.conversations[key] = history

    def get_conversation(self, key: str) -> list:
        """
        Retrieves the history list from the conversations dict with the id as the key
        """
        return self.conversations[key]

    def remove_conversation(self, key: str) -> None:
        """
        Removes the history list from the conversations dict with the id as the key
        """
        del self.conversations[key]

    def __str__(self) -> str:
        """
        Creates a JSON string of the conversations
        """
        return json.dumps(self.conversations)

    def save(self, file: str) -> None:
        """
        Saves the conversations to a JSON file
        """
        with open(file, "w", encoding="utf-8") as f:
            f.write(str(self))

    def load(self, file: str) -> None:
        """
        Loads the conversations from a JSON file
        """
        with open(file, encoding="utf-8") as f:
            self.conversations = json.loads(f.read())


def main():

    def extractCode(prompt, convertFile, filetype):
        with open(convertFile, 'r') as file:
            lines = file.readlines()
        code_blocks = []
        recording = False
        for line in lines:
            if line.strip() == "```":
                recording = not recording
            elif recording:
                code_blocks.append(line)
        file.close()
        now = datetime.now()
        timestr = now.strftime("%Y_%m_%d-%H_%M_%S")
        fileName = "./Generated_Scripts/" + timestr + filetype
        with open(fileName, "w+") as f:
            f.write("# Original Prompt: " + prompt + "\n")
            for code_block in code_blocks:
                f.write(code_block)
        f.close()

###################################################
## Custom Commands
###################################################
    def promptCommandCheck(prompt):
        global mode
        global fileExt
        createfile = "0"

        commands = ["using python", "using C#", "using c sharp", "using html", "using javascript", "using batch", "using c++", "using c plus plus", "using css"]
        filetypes = [".py", ".cs", ".cs", ".html", ".js", ".bat", ".cpp", ".cpp", ".css"]

        if prompt.startswith("!"):
            if chatbot_commands(prompt):
                return

        for i, j in enumerate(commands):
            if prompt.startswith(j):
                createfile = "1"
                fileExt = filetypes[i]
                print("Generating " + fileExt + " file...")
                continue


        if "!switch-to-voice" in prompt:
            mode = "1"
            print("\nSwitching to Voice...")
            return
        
        if "switch to text" in prompt:
            mode = "2"
            print("\nSwitching to Text...")
            return
        
        if "stop listening" in prompt:
            print("\nExiting...")
            mode = ""
            return
        
        if "voice commands" in prompt:
            print(
                """
            Available Voice Commands:
            "stop listening" - stop listening and go back to main menu
            "switch to text" - swap to text input for prompt
            "using..." followed by "python" "c sharp" "javascript" "html" "batch" will generate timestamped files of usable code
            """,
            )
            mode = ""
            return

        if not args.stream:
            response = chatbot.ask(prompt, temperature=args.temperature)
            print("ChatGPT: " + response["choices"][0]["text"])
            if(createfile == "1"):
                with open("./Generated_Scripts/new_file.txt", "w+") as file:
                    file.write(response["choices"][0]["text"])
                file.close()
                extractCode(prompt, "./Generated_Scripts/new_file.txt", fileExt)
        else:
            print("ChatGPT: ")
            sys.stdout.flush()
            for response in chatbot.ask_stream(prompt, temperature=args.temperature):
                print(response, end="")
                sys.stdout.flush()
            print()
###################################################
###################################################


    def textChatGPT():
        global mode
        while (mode == "2"):
            try:
                prompt = input("\nPrompt (or !help for available commands):   ")
                promptCommandCheck(prompt)
            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit()
    

    def voiceChatGPT():
        global mode
        while (mode == "1"):
            try:
                with sr.Microphone() as source:
                    print("Speak your prompt now...\nSay 'Voice Commands' to View Features\nSay 'Stop Listening' to Return to Main Menu...")
                    prompt_audio = r.listen(source, timeout=None)
                    try:
                        prompt = r.recognize_google(prompt_audio)
                        promptCommandCheck(prompt)                  
                    except:
                        print("Sorry, I didn't understand that.")
            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit()
            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service; {0}".format(e))
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
            except OSError as e:
                print("Microphone not found: {0}".format(e))
        

    def chatbot_commands(cmd: str) -> bool:
        """
        Handle chatbot commands
        """
        if cmd == "!help":
            print(
                """
            !switch-to-voice - Switch to voice interaction
            !help - Display this message
            !rollback - Rollback chat history
            !reset - Reset chat history
            !prompt - Show current prompt
            !save_c <conversation_name> - Save history to a conversation
            !load_c <conversation_name> - Load history from a conversation
            !save_f <file_name> - Save all conversations to a file
            !load_f <file_name> - Load all conversations from a file
            !exit - Quit chat

            Productivity:
            "using..." followed by "python" "C#" "c sharp" "javascript" "html" will generate timestamped files of usable code
            """,
            )
        elif cmd == "!exit":
            exit()
        elif cmd == "!rollback":
            chatbot.rollback(1)
        elif cmd == "!reset":
            chatbot.reset()
        elif cmd == "!prompt":
            print(chatbot.prompt.construct_prompt(""))
        elif cmd.startswith("!save_c"):
            chatbot.save_conversation(cmd.split(" ")[1])
        elif cmd.startswith("!load_c"):
            chatbot.load_conversation(cmd.split(" ")[1])
        elif cmd.startswith("!save_f"):
            chatbot.conversations.save(cmd.split(" ")[1])
        elif cmd.startswith("!load_f"):
            chatbot.conversations.load(cmd.split(" ")[1])
        else:
            return False
        return True

    # Pulls API token from file
    try:
        with open("api-key.txt", "r") as file:
            key = file.read().strip()
        file.close()

    # Saves your API token in file for next time
    except:
        key = input("\nNo API key found, please go to https://platform.openai.com/account/api-keys to generate one and paste it here to begin: ")
        with open("api-key.txt", "w+") as file:
            file.write(key)
        file.close()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream response",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.5,
        help="Temperature for response",
    )
    args = parser.parse_args()
    
    #########################################################
    ##  Initialize ChatGPT
    #########################################################
    chatbot = Chatbot(api_key=key)    # put your API key here
    # Start chat
    while(True):
        global mode
        if(mode==""):
            mode = input("\nSelect Input Mode\nEnter 1 for Voice\nEnter 2 for Text\nEnter 3 to Quit\n\nMode:   ")
            if mode.isdigit():
                continue
            else:
                print("\nInvalid Entry Type. Try Again")
                mode = ""
        if(mode == "1"):
            voiceChatGPT()
        elif(mode == "2"):
            textChatGPT()
        elif(mode == "3"):
            break
        else:
            mode = ""
    ##########################################################

if __name__ == "__main__":
    main()
