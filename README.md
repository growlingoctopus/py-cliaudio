# playtext.py

Requires numpy and sounddevice.  This uses a simple token format for playing 'music' on the CLI.
The first token tells the BPM and optionally the default waveform to use (in the format bpm/waveform).
Every token after that is a note, chord or rest.

## Note format
The base format for tokens is in the form "note:fractional note length".  For example, C:1/8 would play an eighth note.  With just a number like C:2, it automatically sets the denominator to 4 for quarter notes.

The format can look like these examples:

**C:1/8**: Just a C in the default octave (set to 3 at top of file).

**C4:1/8**: C, 4th octave

**C4maj:1/8**: C major chord

**C4maj:1/8:sawtooth**:  A third semicolon-split parameter lets you override the waveform for this note.

**C4maj:1/8:sawtooth+5**:  Adding +/- with a number will increase or decrease the gain on the note by that many dB.

Any of these things can be mixed together, for example Cmaj:3/4+5 is fine.

## Repeating Notes
You can put a repeat on any note by putting (Nx) anywhere in the note token where N is the repeat count. The token 'C4maj:1/8(4x)' would do a C major chord eighth note 4 times.

## Repeating blocks
You can also repeat a section of your notes together.  This works with repeating notes as well.

For example, `python3 playtext.py '120/sine repeat C4:1/8(4x) D4:1/8(4x) 2x` would repeat 4 C4 eighth notes and 4 D4 eighth notes twice.

## Rests
Rests can be added the same way as notes.  Just do rest:note length or r:note length (eg. r:3/8).

## Multiple Tracks
You can specify multiple 'tracks' in separated quoted note sequences.  BPM specified from any track other than the first will be ignored, and is not required to even use.  For example, `python3 playtext.py '120/sawtooth C4maj7:1/8(x8) F4pow:1/8(x4) G4maj7(x4)' 'organ C2:4 Eb:4 F2:4 G2maj:4'

# Changing gain mid track
Instead of setting the gain for a specific note, you can also just use a token like 'gain:+5' or 'gain:-10' and it will change it from then on (until you change it back with another command).

# Comments/bars
Any token in a track that starts with | is ignored, so it can be used to split up measures and make reading easier.  You can use it for comments (without spaces) if needed too, for example '|verse2'

# Skip command for testing
If you want to just ignore a part of the track during testing, you can put a token that's just 'skip' and it will skip everything after it until a 'noskip' command.
For example, `python3 playtext.py '160/triangle C4:1 D4:1 skip E4:1 F4:1 G4:1 noskip A4:1 B4:1' will only play C4:1 D4:1 A4:1 B4:1.

# tuning
A4_BASE is set to 440 in the top of the script.  It can be changed to tune to something else like A=432.

# staccato
Setting a higher staccato value increases the fade-out on notes to act more like staccato notes.  The default is 1 (whole numbers).  There's no capped limit, but it will stop working if the number is too high, so experimenting is wise.  Simply add a token like staccato:5 and it will affect all tokens afterwards, until you change it again.

## Examples
Highly professional masterpiece, Hot Cross Buns .. it even almost sounds like a recorder:

`python3 playtext.py '160/triangle B:2 A:2 G:2 rest:2 B4:2 A4:2 G4:2 rest:2 G4:1+5 G4:1+5 G4:1+5 G4:1+5 A4:1+10 A4:1+10 A4:1+10 A4:1+10 B4min:2 A4min:2 G4maj:2'`

Showing some chords:

`python3 playtext.py '110/sine C4:7/8 r:1/8 C4maj:7/8 r:1/8 C4maj7:7/8:organ-5 r:1/8 C4min:7/8 r:1/8 C4dom7:4:sawtooth+15'`

A longer example with more stuff:

`python3 playtext.py '120/organ+8 repeat C2:4 F#2:4 F2:4 E2:4 4x' 'sawtooth-15 repeat C#4:1/32(2x) C4:1/16 128x' 'noise-10 repeat C2:1/64 r:3/64 64x' 'pulse rest:32 repeat B1:1/8 r:1/8 4x repeat F#2:1/8 r:1/8 4x repeat F2:1/8 r:1/8 4x repeat E2:1/8 r:1/8 4x' 'sine-10 repeat C#6:1/32(2x)+2 C6:1/16 32x' 'pulse-10 rest:48 repeat B1:1/8 r:1/8 4x repeat F#2:1/8 r:1/8 4x repeat F2:1/8 r:1/8 4x repeat E2:1/8 r:1/8 4x'`


## Chords
The list of chords is in an array near the top of the script.  As of writing this, this is that list:
```
CHORD_INTERVALS = {
    'maj':     [ SEMITONE_MULTIPLIERS[i] for i in [0, 4, 7] ],          # root, maj 3, perf 5
    'maj7':    [ SEMITONE_MULTIPLIERS[i] for i in [0, 4, 7, 11] ],      # root, maj 3, perf 5, maj 7
    'min':     [ SEMITONE_MULTIPLIERS[i] for i in [0, 3, 7] ],          # root, min 3, perf 5
    'dim':     [ SEMITONE_MULTIPLIERS[i] for i in [0, 3, 6] ],          # root, min 3, dim 5
    'dom7':    [ SEMITONE_MULTIPLIERS[i] for i in [0, 4, 7, 10]],       # root, maj 3, perf 5, min 7
    'min7':    [ SEMITONE_MULTIPLIERS[i] for i in [0, 3, 7, 10]],       # root, min 3, perf 5, min 7
    'mmaj7':   [ SEMITONE_MULTIPLIERS[i] for i in [0, 3, 7, 11] ],      # root, min 3, perf 5, maj 7
    'sus4':    [ SEMITONE_MULTIPLIERS[i] for i in [0, 5, 7]],           # root, perf 4, perf 5
    'sus2':    [ SEMITONE_MULTIPLIERS[i] for i in [0, 2, 7] ],          # root, maj 2, perf 5
    'add9':    [ SEMITONE_MULTIPLIERS[i] for i in [0, 4, 7, 14] ],      # root, maj 3, perf 5, maj 9
    'maj6':    [ SEMITONE_MULTIPLIERS[i] for i in [0, 4, 7, 9] ],       # root, maj 3, perf 5, maj 6
    'min6':    [ SEMITONE_MULTIPLIERS[i] for i in [0, 3, 7, 9] ],       # root, min 3, perf 5, maj 6
    'aug':     [ SEMITONE_MULTIPLIERS[i] for i in [0, 4, 8] ],          # root, maj 3, augmented 5
    'pow':     [ SEMITONE_MULTIPLIERS[i] for i in [0, 7] ],             # root, perf 5 (power chord)
    'dim7':    [ SEMITONE_MULTIPLIERS[i] for i in [0, 3, 6, 9] ],       # root, min 3, dim 5, maj 6
    'hdim7':   [ SEMITONE_MULTIPLIERS[i] for i in [0, 3, 6, 10] ],      # root, min 3, dim 5, min 7 
    'aug7':    [ SEMITONE_MULTIPLIERS[i] for i in [0, 4, 8, 10] ],      # root, maj 3, sharp 5, min 7
    'dom9':    [ SEMITONE_MULTIPLIERS[i] for i in [0, 4, 7, 10, 14] ],  # root, maj 3, perf 5, min 7, maj 9
    'min9':    [ SEMITONE_MULTIPLIERS[i] for i in [0, 3, 7, 10, 14] ],  # root, min 3, perf 5, min 7, maj 9
    'maj9':    [ SEMITONE_MULTIPLIERS[i] for i in [0, 4, 7, 11, 14] ],  # root, maj 3, perf 5, maj 7, maj 9
    'shit':    [ SEMITONE_MULTIPLIERS[i] for i in [0, 1, 11, 13] ],     # what
}
```

They're just semitone maps so any other chords can be added easily.