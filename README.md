# GenMacro

A GUI application that automatically writes, compresses, reads, and replays macros. Intended to simplify the macro creation and management process. 

## Features

- Create: Record and save macros
- Run: Replay saved macros
- Settings: Modify keybinds and precision timings
- File loading interface: Options to select, create, and delete files
- Overly redundant safety measures
- Tkinter GUI: Resizes when recording and replaying

## Dependencies

- [keyboard](https://github.com/boppreh/keyboard)
- [mouse](https://github.com/boppreh/mouse)

## Known issues

- Quitting a running macro doesn't restore currently pressed keys to their original state
- The letter 'b' is rarely pressed when replaying a file that involved recording an overwhelming ammount of keyboard commands simultaneously
- Replaying a file recorded on a different screen size does not currently work

## More to come

- Transference to desktop application (.exe)
- More UI feedback and optimizations
- Support for scheduling macros in succession or on command
- Support for screen size
- Automated visual checking process 
