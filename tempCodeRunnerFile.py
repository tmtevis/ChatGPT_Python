    prompt = ""
    mode = input("\nSelect Input Mode\nEnter 1 for Voice\nEnter 2 for Text\n\nMode:   ")
    # Start chat
    while True:
        try:
            while(mode == 1):
                with sr.Microphone() as source:
                    print("Speak your prompt, or say 'Stop Listening' to QUIT...")
                    prompt_audio = r.listen(source, timeout=None)
                    try:
                        prompt = r.recognize_google(prompt_audio)
                        if(prompt == "stop listening"):     # add other command phrases here such as opening webpages
                            print("\nExiting...")
                            break
                        if(prompt == "text input"):     # switch to text input for using built-in commands such as saving
                            prompt = input("\nPrompt:   ")
                    except:
                        print("Sorry, I didn't understand that.")
                        
            if(mode == 2):
                prompt = input("\nPrompt:   ")