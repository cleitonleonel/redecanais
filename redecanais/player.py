# -*- coding: utf-8 -*-
#

html_player = """<!DOCTYPE html>
<html lang="en">
<style>
.center {
  margin: auto;
  background: #fff;
  padding: 10px;
}

.container {
    width: 100vw;
    height: 100vh;
    background: #6C7A89;
    display: flex;
    flex-direction: row;
    justify-content: center;
    align-items: center
}

.title {
    text-align: center;
}

.google-cast-launcher {
    float: right;
    margin: -55px 200px 14px 0px;
    width: 40px;
    height: 32px;
    opacity: 0.7;
    background-color: #000;
    border: none;
    outline: none;
}

.google-cast-launcher:hover {
    --disconnected-color: white;
    --connected-color: white;
}

body {
    margin: 0px;
}
</style>
<head>
    <meta charset="UTF-8">
    <title>RedeCanais Player</title>
    <script rel="stylesheet" src="https://www.gstatic.com/cv/js/sender/v1/cast_sender.js?loadCastFramework=1" type="text/javascript"></script>
    <script rel="stylesheet" src="https://cdn.jsdelivr.net/gh/fenny/castjs@3.0.1/cast.min.js"></script>    
    <!--<script rel="stylesheet" src="https://cdn.jsdelivr.net/afterglow/latest/afterglow.min.js" type="text/javascript"></script>-->
    <link href="https://unpkg.com/video.js/dist/video-js.css" rel="stylesheet">
    <script src="https://unpkg.com/video.js/dist/video.js"></script>
    <script src="https://unpkg.com/videojs-contrib-hls/dist/videojs-contrib-hls.js"></script>
</head>
<body>
    <div class="title">
        <h3>RedeCanais Player With Python Backend</h3>
    </div>

    <div class="container">
        <div style="width:980; height:823;">
            <div>
                <video id="my_video_1" class="video-js vjs-default-skin" controls preload="auto" width="640" height="268" data-setup='{}'>
                    <source src="%(url)s" type="video/mp4">
                </video>
                <!--<video class="afterglow center" id="myvideo" controls width="1080" height="500" autoplay="autoplay" src="%(url)s"></video>
                <button class="google-cast-launcher" is="google-cast-button"></button>-->
            </div>
        </div>
    </div>
</body>
<script>
    let cc = new Cast();
    cc.on('available', function() {
        cc.cast({
            poster:      '%(img)s',
            title:       '%(title)s',
            description: '%(description)s',
            content:     '%(url)s',            
        })
    })
</script>
</html>
"""