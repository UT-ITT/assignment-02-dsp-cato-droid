import mido
from mido import MidiFile

for msg in MidiFile('Alle_Meine_Entchen.mid').play():
    #print(msg)
    if msg.type == "note_on":
        print(f"note: {msg.note}, frequency: {440 * 2 **((msg.note - 69) / 12)}")

#Note Frequency = 440Hz * 2^( (note - 69) / 12 )
#https://www.phys.unsw.edu.au/jw/notes.html
#https://www.reddit.com/r/embedded/comments/exxrub/popular_tunes_as_list_of_notes_frequencies/