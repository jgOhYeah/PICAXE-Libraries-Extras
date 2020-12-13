/** PICAXE Tune converter
A small Musescore 3 plugin to convert simple tunes into code that can be used by the PICAXE tune command.
This is VERY buggy and may or may not work, but I found it useful.
(Be warned, I didn't really know what I was doing or much about qml when I wrote this - No comment about what I know or don't know about it now :) )

To use:
1. Copy this file into the Musecore plugins folder (In Windows, this is User's Folder\Documents\Musescore3\plugins)
2. In Musecore, go to Plugins > Plugin manager and tick the box next to this file to display it in the Plugins menu.
3. Open the file you want to convert. Ideally, it should only have a single stave and one note at a time. Things that PICAXE microchips do not support such as dotted notes and ties should be edited out.
4. Make sure that nothing is selected as there seems to be a bit of a bug in how it is handled in the code somewhere.
5. Go to Plugins > the name of this file to run it. There should be a box popup with the tune. Click copy to clipboard.
6. Paste the code in the Picaxe editor document. Replace "pin" with the pin to use (see the manual for pins available on each chip) and "speed" with the code for the closest speed (see the manual or the table on the popup window).

Tips:
- If there are short notes or more complex timings required, it may be helpful to write the song in Musescore with each note taking up double the number of beats it would normally, then setting a faster time to play in the PICAXE chip.
- If there are random notes or rests added, double check there is not more than one note played at a time.
- Depending on versions of Musescore and bugginess of this script, the plugin may not run correctly when started from the plugins dropown menu. Instead, you might have to open this file in the plugin creator and click run in the bottom left of it.
- It may be helpful if you are struggling to get timings that the PICAXE supports to put everything in one massive bar so that you do not have to worry about things like 2 minims (1/2 notes) tied together over a bar line and can instead use a semibreve (whole note).
- Repeats and jumps are ignored. If you need them, copy everything out in a linear fashion.

Writted by Jotham Gates. Some stuff is copied from various example plugins.
*/

import QtQuick 2.2
import MuseScore 3.0
//import QtQuick.Dialogs 1.1
import QtQuick.Controls 1.4
MuseScore { 
      
      menuPath: "Plugins.To Picaxe Tune"
      description: "Exports single notes into a format for picaxe microcontrollers"
      version: "1.0"
      pluginType: "dialog"
      width:  800
      height: 400
      property var noteString: "tune pin, speed, (";
      
      onRun: {
            console.log("Picaxe Tune Exporter Started");
            if (typeof curScore === 'undefined') {
                  console.log("No score. Stopping");
                  Qt.quit();
            }
            console.log("hello world");
            applyToNotesInSelection(exportNote);
            noteString = noteString.slice(0, -1) + ') \'Converted from ' + curScore.scoreName;
            console.log(noteString);
            //messageDialog.text = noteString;
            //messageDialog.open();
            //Qt.quit();
            outputText.text = noteString;
            outputText.selectAll();
            //outputText.copy();
            }
            
      function applyToNotesInSelection(func) {
            var cursor = curScore.newCursor();
            cursor.rewind(1);
            var startStaff;
            var endStaff;
            var endTick;
            var fullScore = false;
            if (!cursor.segment) { // no selection
                  fullScore = true;
                  startStaff = 0; // start with 1st staff
                  endStaff = curScore.nstaves - 1; // and end with last
            } else {
                  startStaff = cursor.staffIdx;
                  cursor.rewind(2);
                  if (cursor.tick === 0) {
                        // this happens when the selection includes
                        // the last measure of the score.
                        // rewind(2) goes behind the last segment (where
                        // there's none) and sets tick=0
                        endTick = curScore.lastSegment.tick + 1;
                  } else {
                        endTick = cursor.tick;
                  }
                  endStaff = cursor.staffIdx;
            }
            console.log(startStaff + " - " + endStaff + " - " + endTick)
            for (var staff = startStaff; staff <= endStaff; staff++) {
                  for (var voice = 0; voice < 4; voice++) {
                        cursor.rewind(1); // sets voice to 0
                        cursor.voice = voice; //voice has to be set after goTo
                        cursor.staffIdx = staff;

                        if (fullScore)
                              cursor.rewind(0) // if no selection, beginning of score

                        while (cursor.segment && (fullScore || cursor.tick < endTick)) {
                              if (cursor.element && cursor.element.type === Element.CHORD) {
                                    var notes = cursor.element.notes;
                                    for (var k = 0; k < notes.length; k++) {
                                          var note = notes[k];
                                          func(note.pitch,cursor.element.duration);
                                    }
                              } else if (cursor.element.type === Element.REST) {
                                    //console.log(Object.keys(cursor.element));
                                    func(128,cursor.element.duration);
                              }
                              cursor.next();
                        }
                  }
            }
      }
      
      function exportNote(notePitchInput,noteLength) {
            //console.log("Note: " + notePitchInput + ", Length numerator: " + noteLength.numerator + ", Length denominator: " + noteLength.denominator);
            if (notePitchInput < 128) {
                  var notePitch = notePitchInput % 12;
            } else {
                  var notePitch = 15; //Rest
            }
            var noteDuration = 0;
            switch(noteLength.denominator) { //Get the length of the note and convert it into bits for the picaxe
                  case 1:
                        //console.log("Semibreve");
                        noteDuration = 128;
                        break;
                  case 2:
                        //console.log("Minim");
                        noteDuration = 192;
                        break;
                  case 4:
                        //console.log("Crotchet");
                        noteDuration = 0;
                        break;
                  case 8:
                        //console.log("Quaver");
                        noteDuration = 64; //1
                        break;
                  default:
                        //console.log("Note length not supported!");
                        break;
            }
            var noteOctave = 0;
            if (notePitchInput < 72) {
                  noteOctave = 32;
            } else if (notePitchInput > 83) {
                  noteOctave = 16;
            }
            var noteCode = notePitch | noteDuration | noteOctave;
            //console.log("Note pitch (C is 0): " + notePitch + ", Duration: " + noteDuration + ", Octave: " + noteOctave + ", Complete: " + noteCode);
            noteString += noteCode + ",";
      }
     
      Rectangle {
            color: "white"
            anchors.fill: parent
            }
      TableView {
            id: speedTable
            //anchors.left: outputText.right
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 102
            TableViewColumn {
                  role: "snum"
                  title: "Speed"
                  width: 50
                  horizontalAlignment: Text.AlignHCenter
                  }
            TableViewColumn {
                  role: "bpm"
                  title: "BPM"
                  width: 50
                  horizontalAlignment: Text.AlignHCenter
                  }
            model: speedModel
            }
      ListModel {
            id: speedModel
            ListElement {
                  snum: "1"
                  bpm: "812"
                  }
            ListElement {
                  snum: "2"
                  bpm: "406"
                  }
            ListElement {
                  snum: "3"
                  bpm: "270"
                  }
            ListElement {
                  snum: "4"
                  bpm: "203"
                  }
            ListElement {
                  snum: "5"
                  bpm: "162"
                  }
            ListElement {
                  snum: "6"
                  bpm: "135"
                  }
            ListElement {
                  snum: "7"
                  bpm: "116"
                  }
            ListElement {
                  snum: "8"
                  bpm: "101"
                  }
            ListElement {
                  snum: "9"
                  bpm: "90"
                  }
            ListElement {
                  snum: "10"
                  bpm: "81"
                  }
            ListElement {
                  snum: "11"
                  bpm: "73"
                  }
            ListElement {
                  snum: "12"
                  bpm: "67"
                  }
            ListElement {
                  snum: "13"
                  bpm: "62"
                  }
            ListElement {
                  snum: "14"
                  bpm: "58"
                  }
            ListElement {
                  snum: "15"
                  bpm: "54"
                  }
            }
      TextEdit {
            //color: "red"
            id: outputText
            wrapMode: TextEdit.Wrap
            //anchors.centerIn: parent
            anchors.left: parent.left
            anchors.right: speedTable.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.margins: 10
            x: 10
            text: qsTr("Something went wrong... Maybe run from the plugin creator window.")
            
            }
            MouseArea {
            anchors.fill: parent
            onClicked: {
                  console.log("hello");
                  if(outputText.selectionStart = outputText.selectionEnd) {
                        outputText.selectAll();
                        console.log("selecting all");
                  } else {
                        outputText.deselect();
                  }
                  }
            }
       Rectangle {
            width: 100
            height: 20
            color: "grey"
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.margins: 10
            
            Text {
                  text: "Copy to clipboard"
                  color: "white"
                  anchors.fill: parent
                  horizontalAlignment: Text.AlignHCenter
                  verticalAlignment: Text.AlignVCenter
                  }
            
            }
            MouseArea {
            anchors.fill: parent
            onClicked: {
                  outputText.selectAll();
                  outputText.copy();
                  }
            }
            
      
    }
