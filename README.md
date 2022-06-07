User notes/instructions:

Must install AnkiConnect add-on: 
https://ankiweb.net/shared/info/2055492159
Further instructions on AnkiConnect homepage
- e.g. disabling app nap on MacOS, etc.


Temporary design: have set a python script to run periodically via cron. Crontab is:
```
SHELL=/bin/bash
BASH_ENV=~/PycharmProjects/FlashcardMaker/.bashrc_conda
*/5 * * * * conda activate FlashcardMaker; cd ~/PycharmProjects/FlashcardMaker; python main.py
```

Better design: get the MacOS app to execute all the python stuff?
iOS app certainly won't be able to but that's fine - get iOS app to 
sync data to Mac app, then get Mac app to create cards for the words
saved through the iOS extension. 


Using PythonKit within Xcode - wasn't finding Python initially!
First, to set an environment variable in Xcode, go to:
`Product > Scheme > Edit Scheme` and add the variable in the 
Arguments tab of the Run section. Set `PYTHON_LOADER_LOGGING` to `TRUE`
then try to run the app again to see where it's looking. 
Then set `PYTHON_LIBRARY` to the right path if it's looking in 
the wrong place. Tip: use 'which python3' in the terminal to find
your standard python path.
