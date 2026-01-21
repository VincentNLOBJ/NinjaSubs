NinjaSubs is a modern subtitle system for SEGA Dreamcast games using njPrint library function.

It's aimed to translators / modders, that want to add subtitles to games with a simple interface.

- Generate SH4 code including subtitles when "Patch Game Binary" is pressed
- Auto-center subs
- Multi-lines
- SRT import
- Auto scan for njPrint, njPrintColor offsets
- Customize colors, timer and scene names
- Convert times to game 60/30 fps
- Fix debug font paragraph (V1 and V2)
- Up to 254 subs per scene!

Please note that while it generates the code, subs, timings, colors by directly patching executable, you still need to manually define / create functions for:

1. A timer (if not already existing)
2. Scene / Timer initialization functions (if not already existing)
3. Function where to execute NinjaSubs
