# Gunshot Dataset Builder

## Top Firearm Channels on YouTube

1. hickok45
2. sootch00
3. Military Arms Channel
4. Iraqveteran8888
5. nutnfancy
6. T.REX ARMS
7. Garand Thumb
8. TWANGnBANG
9. Colion Noir
10. DemolitionRanch

## Use youtube-dl to download audio of youtube video

```shell script
youtube-dl -x --audio-format wav --audio-quality 0 [url]
```


## Acoustical Characteristics of Gunshots 

To tackle the sensitivity problem of our SVM model, we analyzed the acoustical characteristics of real gunshots. We compared audios of actual gunshots from popular YouTube firearm channels with the recording of gunshots played by speakers. We found that real gunshots are much louder than gunshot audios played by speakers. We also comfirmed it with other sources online. In another word, normally speakers cannot produce acoustical signals similar to real gunshots. In fact, almost noting in our daily life can produce sounds with similar amplitute as gunshots.

To reduce sensitivity and false possitive rate of our system, we set a threadhold for our microphone. If there is no high amplitude signal within current epoch, we skip the inference and move forward. 