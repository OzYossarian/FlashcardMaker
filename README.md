## Current design

### MacOS

Purely python code. Can create flashcards either by getting items from server or from a text file. e.g. I run `flashcards_from_server.py` every thirty minutes on my old laptop via `crontab`. This looks for any new server entries and creates flascards from them. On the other hand, if I'm reading a book, I write down new words/phrases in a text file and then run `flashcards_from_file.py` manually on my current laptop.

On whichever computer you run this code on, you must:
- install Anki and have logged in at least once (if Anki isn't currently open, it'll open automatically).
- install AnkiConnect add-on: https://ankiweb.net/shared/info/2055492159. Further instructions on AnkiConnect homepage, e.g. disabling app nap on MacOS, etc.
- install (mini)conda and create an environment from the `environment.yml` file provided.

Cronjob used on old laptop is:
```
SHELL=/bin/bash
BASH_ENV=~/PycharmProjects/FlashcardMaker/.bashrc_conda
*/30 * * * * conda activate FlashcardMaker; cd ~/PycharmProjects/FlashcardMaker; python flashcards_from_server.py
```
(.bashrc_conda file should be edited so that it points to wherever user's version of (mini)conda is)

### iOS

Have written an iOS app and iOS extension (not in this repo - will have its own repo shortly). Extension just sends data to server, and this data sits there until someone (e.g. my old laptop) does anything with it. If internet is down, data is saved to companion app, which tries to resend it to server when app is next opened. iOS app should contain settings, but currently doesn't.

## Future design

Make a MacOS extension that can create flashcards. No point at the moment because such an extension can't run outside of debug mode in Xcode (unless I join Apple's developer scheme). If this extension existed though, would also make a Fluency Lube MacOS app. iOS extension would save data to iOS app, then iOS app would use iCloud to sync this data with MacOS app, which would finally create flashcards (only MacOS apps can execute python code, and all the code to actually make flashcards is in python). MacOS extension doesn't need to use the MacOS app - it can just make flashcards itself directly. But would save to MacOS app if internet were down or something. MacOS and iOS apps can then include settings - e.g. default deck, how many Linguee results to use, etc. These settings would stay synced across devices. 

### PythonKit

Some notes on using PythonKit within Xcode - wasn't finding Python initially!
First, to set an environment variable in Xcode, go to:
`Product > Scheme > Edit Scheme` and add the variable in the 
Arguments tab of the Run section. Set `PYTHON_LOADER_LOGGING` to `TRUE`
then try to run the app again to see where it's looking. 
Then set `PYTHON_LIBRARY` to the right path if it's looking in 
the wrong place. Tip: use 'which python3' in the terminal to find
your standard python path.
