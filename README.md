## NinjaSubs

**NinjaSubs** is a modern subtitle system for **SEGA Dreamcast** games built around the `njPrint` library. It is designed for translators and modders who want to add subtitles to games through a simple and flexible workflow.

### Features

- Generates SH4 code with embedded subtitles when **Patch Game Binary** is pressed  
- Automatic subtitle centering  
- Multi-line subtitle support  
- `.SRT` file import  
- Automatic scanning for `njPrint` and `njPrintColor` offsets  
- Customizable colors, timers, and scene names  
- Time conversion for 60 FPS and 30 FPS games  
- Debug font paragraph fixes (V1 and V2)  
- Supports up to **254 subtitles per scene**
<img width="902" height="712" alt="image" src="https://github.com/user-attachments/assets/7f1d9212-82ae-45ad-8e9b-f16a82440f7e" />

### Important Notes

NinjaSubs directly patches the game executable to inject subtitle code, timings, and colors.  
However, you must still manually implement the following if they do not already exist in the game:

- A timer function  
- Scene and timer initialization functions  
- The function or hook where NinjaSubs is executed

### Games Using NinjaSubs:
- Rent-A-Hero No.1 (English Translation)
- SEGAGAGA (English Translation)

![ezgif com-animated-gif-maker](https://github.com/user-attachments/assets/5da1c42a-c45f-402f-810a-8097becf22ec)
