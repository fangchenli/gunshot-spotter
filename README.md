# GunshotSpotter

## Setup

### Hardware, Driver, and Libraries

1. Setup Raspberry Pi following the official tutorial.
2. Assemble the ReSpeaker 6-Mic Array and install it on the Pi. 
3. Install Device Driver and other libraries.
4. Setup Python virtual environment and packages such as PyAudio and Numpy.
5. Install AWS Core SDK on the core, and device SDK on the device.


### AWS IoT Greengrass

1. Set up the core and two devices following the official tutorial.


## Rule Query

### SNS Message

```sql
SELECT VALUE state.reported.alert FROM '$aws/things/<Device Name>/shadow/update/accepted' WHERE state.reported.gunshot = 'yes'
```


## Recourse
1. Official Raspberry Pi Setup Instruction https://projects.raspberrypi.org/en/projects/raspberry-pi-setting-up
2. Official ReSpeaker Wiki for the 6-Mic circular array http://wiki.seeedstudio.com/ReSpeaker_6-Mic_Circular_Array_kit_for_Raspberry_Pi/
3. AWS IoT Greengrass tutorial https://docs.aws.amazon.com/greengrass/latest/developerguide/gg-gs.html


## Reference
1. https://github.com/hazooree/Real-Time-Implementation-of-Gunshot-Detection-System
2. https://github.com/voice-engine/voice-engine