import sys
import time
import numpy as np
import sounddevice as sd

# Configuration
SAMPLE_RATE = 44100
WAVE_TYPE = 'sine'  # Options: 'sine', 'square', 'triangle', 'sawtooth'
ACCEPTED_WAVE_TYPES = ['sine', 'square', 'triangle', 'sawtooth', 'pulse','organ', 'noise']
SEMITONE_MULTIPLIERS = [2 ** (x / 12.0) for x in range(24)]
DEFAULT_OCTAVE = "3"
PULSE_WIDTH = .25

# Standard frequency definitions for Octave 4
NOTE_FREQS4 = {
    'C':  261.63, 'C#': 277.18, 'Db': 277.18, 'D':  293.66, 
    'D#': 311.13, 'Eb': 311.13, 'E':  329.63, 'F':  349.23, 
    'F#': 369.99, 'Gb': 369.99, 'G':  392.00, 'G#': 415.30,
    'Ab': 415.30, 'A':  440.00, 'A#': 466.16, 'Bb': 466.16,
    'B':  493.88
}
NOTE_FREQS = {}
# yes i know you shouldnt do this to constants, fuck you if you complain
for flvl in [0, 1, 2, 3]:
    for fbase in NOTE_FREQS4.keys():
        newlvl = fbase + str(flvl)
        NOTE_FREQS[newlvl] = NOTE_FREQS4[fbase] / (2 ** (4 - flvl))
        print(f"flvl: {flvl}, fbase {fbase}, newlvl {newlvl}, freq {NOTE_FREQS.get(newlvl)}")
for fbase in NOTE_FREQS4.keys():
    NOTE_FREQS[fbase+'4'] = NOTE_FREQS4[fbase]
for flvl in [5, 6, 7, 8]:
    for fbase in NOTE_FREQS4.keys():
        newlvl = fbase + str(flvl)
        NOTE_FREQS[newlvl] = NOTE_FREQS4[fbase] * (2 ** (flvl - 4))
for fbase in NOTE_FREQS4.keys(): # defaults
    NOTE_FREQS[fbase] = NOTE_FREQS[fbase + DEFAULT_OCTAVE]

# Chord intervals for different chords
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

def get_wave(phase, wave_type):
    if wave_type == 'sine':
        return np.sin(phase * 2 * np.pi)
    elif wave_type == 'square':
        return np.where(phase % 1.0 < 0.5, 1.0, -1.0)
    elif wave_type == 'triangle':
        return 2.0 * np.abs(2.0 * (phase % 1.0 - np.floor(phase % 1.0 + 0.5))) - 1.0
    elif wave_type == 'sawtooth':
        return 2.0 * (phase % 1.0 - np.floor(phase % 1.0 + 0.5))
    elif wave_type == 'pulse':
        # pulse_width=0.25 creates a classic 25% thin pulse wave
        return np.where(phase % 1.0 < PULSE_WIDTH, 1.0, -1.0)
    elif wave_type == 'organ':
        # Additive Synthesis: Fundamental + Second Harmonic at half volume
        fundamental = np.sin(phase * 2 * np.pi)
        second_harmonic = 0.5 * np.sin((phase * 2) * 2 * np.pi)
        return (fundamental + second_harmonic) / 1.5    
    elif wave_type == 'noise':
        # Generates a random array matching the shape of your phase vector
        return np.random.uniform(-1.0, 1.0, size=phase.shape)
    
    return np.zeros_like(phase)

def generate_step(frequencies, duration_beats, bpm, wave_type,staccato=4):
    samples_per_beat = (60.0 / bpm) * SAMPLE_RATE
    total_samples = int(duration_beats * samples_per_beat)
    
    if total_samples == 0:
        return np.array([])

    t = np.arange(total_samples)
    mixed_wave = np.zeros(total_samples)

    if wave_type in ['rest', 'r']:
        return mixed_wave
    if len(frequencies) > 0:
        for freq in frequencies:
            phase = (t * freq) / SAMPLE_RATE
            mixed_wave += get_wave(phase, wave_type)
        mixed_wave /= len(frequencies)

    # 10ms anti-pop envelope
    fade_samples = int(0.010 * SAMPLE_RATE)
    if fade_samples * (2 + staccato) < total_samples:
        fade_in = np.linspace(0.0, 1.0, fade_samples)
        fade_out = np.linspace(1.0, 0.0, fade_samples * staccato)
        envelope = np.ones(total_samples)
        envelope[:fade_samples] = fade_in
        envelope[-fade_samples * staccato:] = fade_out
        mixed_wave *= envelope

    return mixed_wave

def parse_and_render(sequence_string, wave_type, bypass_bpm=0):
    tokens = sequence_string.split()
    if not tokens:
        return np.array([])
    dB_base = 0

    # get dB override from first token
    if '+' in tokens[0]:
        (tokens[0], dB) = tokens[0].split('+')
        if dB.isdigit():
            dB_base = float(dB)
    elif '-' in tokens[0]:
        (tokens[0], dB) = tokens[0].split('-')
        if dB.isdigit():
            dB_base = -float(dB)
    # Extract BPM from the first token
    try:
        bpm_array = tokens[0].split('/')
        if bypass_bpm:
            bpm = bypass_bpm
        else:
            if bpm_array[0].isdigit():
                bpm = float(bpm_array[0])
            else:
                print("Error: No BPM provided")
                return np.array([])
        if len(bpm_array) > 1 or not bpm_array[0].isdigit():
            if bpm_array[-1] in ACCEPTED_WAVE_TYPES:
                wave_type = bpm_array[-1]
            else:
                print("WARNING: Wave type %s not found." % bpm_array[1]) 
        note_tokens = tokens[1:]
    except ValueError:
        print("Error: The sequence must start with a BPM number (e.g., '120 C4maj:1/8')")
        sys.exit(1)
        
    full_song_buffer = []

    block_repeat = False
    block_repeat_buffer = []
    restok = False
    restok_buffer = []
    staccato = 1
    for token in note_tokens:
        wave_override = wave_type
        dB_adjust = 0
        repeat_count = 1
        
        if token.startswith('|'):
            continue # visual bar splitter for making the command easier to read if you want

        if token == 'repeat':
            block_repeat = True
            continue
        elif token.endswith('x') and token[:-1].isdigit():
            if len(block_repeat_buffer) > 0:
                for i in range(int(token[:-1])):
                    for j in range(len(block_repeat_buffer)):
                        full_song_buffer.append(block_repeat_buffer[j])
            block_repeat = False
            block_repeat_buffer = []

        # ANYTHING WITHOUT A : GOES ABOVE THIS
        if ':' not in token:
            continue

        if '+' in token:
            (token, dB_adjust) = token.split('+')
            dB_adjust = float(dB_adjust)
        elif '-' in token:
            (token, dB_adjust) = token.split('-')
            dB_adjust = -float(dB_adjust)
        wave_multiplier = .5 * ( 10**((dB_adjust+dB_base)/20) )

        if token.find('(') >= 0 and token.find('x)') > token.find('('):
            (tok_head, tok_tail) = token.split('(')
            (repeat_count, tok_tail) = tok_tail.split('x)')
            token = tok_head + tok_tail
            if repeat_count.isdigit():
                repeat_count = int(repeat_count)

        if token.endswith('..'):
            token = token[:-2]
            restok = True

        tksplit = token.split(':')

        # ANY STUFF THAT USES : SPLITS BELOW THIS
        if tksplit[0] == 'staccato':
            if tksplit[1].isdigit():
                staccato = max(1, int(tksplit[1]))
            continue

        if len(tksplit) == 3 and tksplit[2] in ACCEPTED_WAVE_TYPES:
            wave_override = tksplit[2]
        note_part = tksplit[0]
        duration_part = tksplit[1]
        
        # Parse fraction duration
        duration_split = duration_part.split('/')
        if len(duration_split) == 2:
            num, denom = map(float, duration_part.split('/'))
        elif len(duration_split) == 1:
            num = float(duration_split[0])
            denom = 4.0 # so that a single number is a quarter note
        duration_beats = (num / denom) * 4.0 # 1/4 note = 1.0 beat
        
        # Match chord modifiers by checking the longest extension names first
        chord_type = None
        root_note = note_part
        if note_part.startswith('r'):
            chunk = generate_step(0, duration_beats, bpm, 'rest')
            if block_repeat:
                block_repeat_buffer.append(chunk)
            else:
                full_song_buffer.append(chunk)
            continue

        # START BASIC NOTE PARSING
        sharpflat = ""
        if note_part[1] in ['b', '#']:
            sharpflat = note_part[1]
            note_part = note_part[0] + note_part[2:]
            print(f"stripped sharpflat {sharpflat} from {note_part}")
        if len(note_part) == 1:
            root_note = note_part
            chord_type = ""
        elif note_part[1].isdigit():
            root_note = note_part[:2]
            chord_type = note_part[2:]
            if (chord_type not in CHORD_INTERVALS and chord_type != "") or root_note not in NOTE_FREQS:
                print(f"missing root note({root_note}) or chord type ({chord_type}) for {note_part}")
        elif note_part[0] in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            root_note = note_part[0]
            chord_type = note_part[1:]
        else:
            print(f"Warning: Unknown note/chord part '{note_part}'")

        if sharpflat:
            root_note = root_note[0] + sharpflat + root_note[1:]

        print(f"Parsing root note {root_note} => {chord_type} (from token {token})")
        if root_note in NOTE_FREQS:
            print(f"note {root_note} in note freqs")
            base_freq = NOTE_FREQS[root_note]
            if chord_type:
                target_freqs = [base_freq * interval for interval in CHORD_INTERVALS[chord_type]]
            else:
                print(f"note {root_note} frequency is {base_freq}")
                target_freqs = [base_freq]
        else:
            print(f"Warning: Unknown note/chord '{note_part}'")
            target_freqs = []

        chunk = generate_step(target_freqs, duration_beats, bpm, wave_override, staccato)
        chunk *= wave_multiplier

        if block_repeat:
            for i in range(repeat_count):
                block_repeat_buffer.append(chunk)
        else:
            for i in range(repeat_count):
                full_song_buffer.append(chunk)
                print(f"full buffer is now {len(full_song_buffer)} in size ()")
    if block_repeat and len(block_repeat_buffer) > 0:
        full_song_buffer.append(block_repeat_buffer)
    return np.concatenate(full_song_buffer) if full_song_buffer else np.array([])


def get_sequence_string_bpm(sequence_string):
    tok = sequence_string.split(' ')[0]
    return float(tok.split('/')[0])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 script.py 'BPM NOTE:DURATION NOTE:DURATION ...'")
        print("Example: python3 script.py '120 C4maj:1/8 F4maj7:3/8'")
        sys.exit(1)

    max_sequence_length = 0    
    input_sequence = sys.argv[1]
    audio_tracks = []
    bpm = get_sequence_string_bpm(sys.argv[1]) # only use bpm from the first track, use the same one on the others

    for i in sys.argv[1:]:
        audio_tracks.append(parse_and_render(i, WAVE_TYPE, bpm))
        if len(audio_tracks[-1]) > max_sequence_length:
            max_sequence_length = len(audio_tracks[-1])

    audio_data = np.zeros(max_sequence_length)
    for i in range(len(audio_tracks)):
        if len(audio_tracks[i]) < max_sequence_length:
            audio_tracks[i] = np.pad(audio_tracks[i], (0, max_sequence_length - len(audio_tracks[i])), mode='constant', constant_values=0)
        #print(f"adding {audio_tracks[i][69000:69015]} to {audio_data[69000:69015]}")
        audio_data += audio_tracks[i]
            #print(audio_tracks[i])

    audio_data /= float(len(audio_tracks))
    
#    if len(audio_data) > 0:
#        sd.play(audio_data, SAMPLE_RATE)
#        sd.wait() 
    if len(audio_data) > 0:
        print("Playing audio... Press Ctrl+C to stop.")
        try:
            # Starts playback in a background thread and returns immediately
            sd.play(audio_data, SAMPLE_RATE)
            
            # Keep Python active in short sleep bursts instead of using sd.wait()
            # sd.get_stream().active checks if the audio card is still processing data
            while sd.get_stream().active:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            # Caught instantly during time.sleep()
            print("\nPlayback interrupted!")
            sd.stop()
            sys.exit(0)