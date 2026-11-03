// Passive 4-second observer. Does not restart anything. A restart claim requires
// a separately authorized external restart during RESTART_WINDOW_READY.
import QtQuick
import QtTest
import "../../plasma/plasmoids/org.kumios.controlcenter/contents/ui" as Kumi
TestCase {
 name: "LegacyServiceRestart"
 Kumi.NativeAudio { id: audio }
 property bool watching: false
 property bool lost: false
 Connections { target: audio; function onReadyChanged() { if (watching && !audio.ready) lost=true } }
 function test_remainsAvailableAcrossLegacyRestart() {
  tryCompare(audio,"ready",true,5000)
  verify(audio.output.available && audio.input.available)
  const output=audio.output.deviceName, input=audio.input.deviceName
  const volume=audio.output.volume, mute=audio.output.muted, micMute=audio.input.muted
  watching=true
  console.log("RESTART_WINDOW_READY")
  wait(4000)
  verify(!lost); verify(audio.output.available && audio.input.available)
  compare(audio.output.deviceName,output); compare(audio.input.deviceName,input)
  compare(audio.output.volume,volume); compare(audio.output.muted,mute); compare(audio.input.muted,micMute)
 }
}
