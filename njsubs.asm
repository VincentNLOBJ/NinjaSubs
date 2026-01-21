;base offset:0x8c010000
;prog offset:0x8c305cd4

; NJ_SUBS() - Function to display subtitles via njPrint
; Parse CURRENT_TIMER to TIME_VALUES table to display SUBTITLES sequence.
; Features AUTO-X centering when X is 0xFF

NJ_SUBS:
    sts.l     PR,@-r15
    shll2     r2                        ; r2 = subs set (scene number)
    mov.l     @PTR_CURRENT_TIMER,r0     
    mov.l     @r0,r0                    ; r0 = load CURRENT_TIMER value
    mov.l     @PTR_PTR_TIME_VALUES,r7   ; r7 = pointer to TIME_VALUES table
    add       r2,r7                     ; add subs set ID *4 for TIME_VALUES table
    mov.l     @r7,r7
    mov.l     @PTR_PTR_SEQUENCE,r3      ; r3 = pointer to SEQUENCE array
    add       r2,r3                     ; add subs set ID *4 for SEQUENCE array 
    
    ; Loop to find matching timer value
    bra       find_current_time         ; Jump to loop check
    mov.l     @r3,r3                                
    
advance_sequence:
    add 0x2,r7                          ; r7 += 4 (next timer entry, uint32)
    add 0x4,r3                          ; r3 += 1 (next sequence index)
    
find_current_time:
    mov.w     @r7,r1                    ; r1 = load current timer value from table
    extu.w    r1,r1                     ; r7 = value as unsigned
    cmp/hi    r1,r0                     ; if current_timer > table_value
    bt        advance_sequence          ; If yes, continue the loop
    
    ; Found matching time
    mov.b     @r3,r1                    ; r1 = read sequence index uint8

    ; Save current color to stack
    mov.l     @PTR_CURRENT_COLOR,r7
    mov.l     @r7,r7
    mov.l     r7,@-r15                  ; Push current color value to stack

    ; Read color
    mov.b     @(0x1,r3),r0              ; r0 = color index
    shll2     r0                        ; color index * 4
    mov.l     @PTR_COLOR_ID_TABLE,r7    ; Read color table ptr
    mov.l     @(r0,r7),r7               ; color value in r7
    mov.l     @PTR_CURRENT_COLOR,r0
    mov.l     r7,@r0                    ; write color value
    
    ; Sub offset
    mov.b     @(0x2,r3),r0              
    extu.b    r0,r2                     ; r2 = y
    mov.b     @(0x3,r3),r0              ; r4 = x
    
    ; Check if x=0xFF (AUTO-X flag)
    cmp/eq    0xff,r0
    bf        loc_normal_VH
    mov       1,r7                      ; if x=FF, set AUTO-X flag to 1
    mov.l     r7,@-r15                  ; PUSH AUTO-X FLAG TO STACK
    bra       loc_after_vh_calc
    mov       0,r4                      ; x = 0 placeholder
    
loc_normal_VH:
    mov       0,r7                      ; AUTO-X flag = 0
    mov.l     r7,@-r15                  ; PUSH AUTO-X FLAG TO STACK
    extu.b    r0,r4
    
loc_after_vh_calc:
    shll16    r4
    or        r2,r4                     ; VH offset in r4
    mov.l     r4,@-r15                  ; SAVE r4 TO STACK
    
    ; Allocate 0x28 bytes on stack for text buffer
    add       -0x28,r15                 ; allocate 0x28 bytes
    mov       r15,r6                    ; r6 = pointer to buffer start
    mov       r6,r2                     ; backup pointer for char count in r2
    shll2     r1                        ; index * 4
    mov.l     @PTR_PTR_SUBS_TEXT,r0     ; r0 = pointer to SUBS_TEXT table
    add       r0,r1                     ; r3 = final text pointer
    mov       r1,r3
    mov.l     @r3,r3
    
    ; Initialize char counter
    mov       0,r8                      ; r8 = char count for current line

copy_loop:
    mov.b     @r3,r0                    ; load current character
    add       1,r3                      ; advance text pointer
    tst       r0,r0
    bt        final_print               ; if null, done

    cmp/eq    0x0A,r0
    bt        do_print_line             ; if newline, print line

    mov.b     r0,@r6                    ; copy char to buffer
    add       1,r6
    bra       copy_loop
    add       1,r8                      ; increment char counter

do_print_line:
    mov       0,r0
    mov.b     r0,@r6                    ; terminate string in buffer
    mov.l     r3,@-r15                  ; SAVE ORIGINAL TEXT POINTER
    mov       r15,r5                    ; r5 = buffer pointer (save it before jsr)
    add       0x4,r5                    ; r5 += 0x4 to skip TXT_PTR
  
    ; Check AUTO-X flag and calculate centered X if needed
    mov.l     @(0x30,r15),r0            ; load AUTO-X flag from stack 0x30
    cmp/eq    0,r0
    bt        loc_continue_print        ; if AUTO-X flag = 0, skip calculation
    
    ; Calculate centered X: ((36 - text_len) // 2) + 2
    mov       36,r0
    sub       r8,r0                     ; r0 = 36 - char_count
    shlr      r0                        ; r0 = r0 >> 1 (divide by 2)
    add       2,r0                      ; r0 += 2
    
    ; Update r4 with new centered X
    mov       r0,r1
    mov       0x2e,r0                   ; 0x2e (offset to X in VH on stack)
    mov.b     r1,@(r0,r15)              ; write X directly to stack
    mov.l     @(0x2c,r15),r4            ; 0x2c (load r4 VH from stack)

loc_continue_print:
    mov.l     @PTR_NJPRINT,r0
    jsr       @r0                       ; call _njPrint
    mov.l     r5,@-r15                  ; PUSH BUFFER POINTER IN DELAY SLOT
    
    ; Increase vertical offset AFTER printing
    mov.l     @(0x30,r15),r4            ; load r4 from stack (buffer 0x28 + TXT_PTR 0x4 + pushed buffer 0x4)
    add       0x1,r4                    ; increase vertical offset
    mov.l     r4,@(0x30,r15)            ; write updated r4 back to stack

    ; Restore original text pointer and skip 0x0A
    mov.l     @r15+,r3                  ; pop buffer pointer
    mov.l     @r15+,r3                  ; restore r3 (original text pointer)
    mov       r15,r6                    ; r6 = pointer to buffer on stack
    bra       copy_loop
    mov       0,r8                      ; reset char counter for next line

final_print:
    mov       0,r0
    mov.b     r0,@r6
    mov       r15,r3                    ; r3 = buffer pointer on stack
    
    ; Check AUTO-X flag for final line
    mov.l     @(0x2c,r15),r0            ; load AUTO-X flag from stack
    cmp/eq    0,r0
    bt        loc_final_print_normal    ; if AUTO-X flag = 0, skip calculation
    
    ; Calculate centered X: ((36 - text_len) // 2) + 2
    mov       36,r0
    sub       r8,r0                     ; r0 = 36 - char_count
    shlr      r0                        ; r0 = r0 >> 1 (divide by 2)
    add       2,r0                      ; r0 += 2
    
    ; Update r4 with new centered X
    mov.l     @(0x28,r15),r4            ; load r4 from stack 
    extu.w    r4,r7                     ; r7 = lower 16 bits (Y offset)
    shll16    r0                        ; shift new X to upper 16 bits
    or        r7,r0                     ; combine X and Y
    mov.l     r0,@(0x28,r15)            ; write updated r4 back to stack

loc_final_print_normal:
    mov.l     @(0x28,r15),r4            ; RESTORE r4 FROM STACK
    mov.l     @PTR_NJPRINT,r0           ; r0 = pointer to _njPrint function
    jsr       @r0                       ; _njPrint(r3=text, r4=position)
    mov.l     r3,@-r15                 
    add       0x4,r15 

    ; Restore color from stack
    mov.l     @r15+,r7                  
    mov.l     @PTR_CURRENT_COLOR,r0
    mov.l     r7,@r0

    ; Pop  ( AUTO-X flag 0x4 + buffer 0x28 + r4 0x4 )
    add       0x30,r15
    lds.l     @r15+,PR                  
    rts                                 
    nop

#align4

; Data section

PTR_NJPRINT:
    #data 0x8c17eb70

PTR_CURRENT_COLOR:
    #data 0x8cafe980

PTR_CURRENT_TIMER:
    #data 0x8c305c2c

PTR_PTR_SEQUENCE:
    #data PTR_SEQUENCE

PTR_PTR_TIME_VALUES:
    #data PTR_TIME_VALUES

PTR_PTR_SUBS_TEXT:
    #data PTR_SUBS_TEXT

PTR_COLOR_ID_TABLE:
    #data COLORS

PTR_SEQUENCE:
    #data SEQUENCE_0
    #data SEQUENCE_1
    #data SEQUENCE_2

PTR_TIME_VALUES:
    #data TIME_VALUES_0
    #data TIME_VALUES_1
    #data TIME_VALUES_2

PTR_SUBS_TEXT:
    #data SUBS_TEXT_0
    #data SUBS_TEXT_1
    #data SUBS_TEXT_2
    #data SUBS_TEXT_3

#align4

COLORS:
    #data 0xFFFFFFFF ; white
    #data 0xFF00FFFF ; color 1
    #data 0xFFFF00FF ; color 2


; sequence: subID(uint8), colorID(uint8),y(uint8),x(uint8)
SEQUENCE_0:
    #data 0x00 0x01 0x19 0xFF
    #data 0x01 0x01 0x19 0xFF
    #data 0x02 0x00 0x19 0xFF
    #data 0x03 0x00 0x19 0xFF

SEQUENCE_1:
    #data 0x00 0x01 0x19 0xFF
    #data 0x01 0x01 0x19 0xFF
    #data 0x02 0x00 0x19 0xFF
    #data 0x03 0x00 0x19 0xFF

SEQUENCE_2:
    #data 0x00 0x01 0x19 0xFF
    #data 0x01 0x01 0x19 0xFF
    #data 0x02 0x00 0x19 0xFF
    #data 0x03 0x00 0x19 0xFF

#align4

TIME_VALUES_0:
    #data 0x0000
    #data 0x0100
    #data 0x0200
    #data 0x0300
    #data 0xFFFF

#align4

TIME_VALUES_1:
    #data 0x0000
    #data 0x0100
    #data 0x0200
    #data 0x0300
    #data 0xFFFF
#align4

TIME_VALUES_2:
    #data 0x0000
    #data 0x0100
    #data 0x0200
    #data 0x0300
    #data 0xFFFF
#align4


;-----------
; SUBS TEXT
;-----------



; EMPTY, used for clearing text before next sub
SUBS_TEXT_0:
    #data 0x00000000     
#align4

; SUBS
SUBS_TEXT_1:
    #data "This is a test!" 0x00
#align4
SUBS_TEXT_2:
    #data "Second sub with spacing" 0x0a "new line!"
#align4
SUBS_TEXT_3:
    #data "Last one!" 0x00