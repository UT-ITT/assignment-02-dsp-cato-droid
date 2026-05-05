# cato-droid (13.5/15P)

## 1 - Karaoke Game (6.5/7P)
* frequency detection works correctly and robustly
    * semi, low-voice is registered better than high-voice; blue curve and continous visualization is not working 100% (2.5P)
* the game is playable, does not crash, and is (kind of) fun to play
    * yep (2P)
* the game tracks some kind of score for correctly sung notes
    * only after playing the game, but that's okay (1P)
* low latency between input and detection
    * yep (1P)

Please don't use pygame, since it doesn't work with newer python versions anymore, use pyglet instead


## 2 - Whistle Input (6/7P)
* upwards and downwards whistling is detected correctly and robustly
    * yep (3P)
*  detection is robust against background noise
    * background noise not robustly filtered (2P)
* low latency between input and detection
    * yep (1P)
* triggered key events work
    * yep (1P)

We had to fix your code in line 76 to even start the script (-1P)


## Code-Quality and .venv used (1/1P)