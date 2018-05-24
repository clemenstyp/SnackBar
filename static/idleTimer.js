function IdleTimerOpenURL() {
    this.timeout = -1;
    this.url = "";
    var self = this;
    var timer;
    var seconds = 0;
    window.onload = resetTimer;
    window.onmousemove = resetTimer;
    window.onmousedown = resetTimer; // catches touchscreen presses
    window.ontouchstart = resetTimer;
    window.onclick = resetTimer;     // catches touchpad clicks
    window.onscroll = resetTimer;    // catches scrolling with arrow keys
    window.onkeypress = resetTimer;

    this.setupTimer = function(timeout, url){
         this.timeout = timeout;
         this.url = url;
         resetTimer();
    }
    this.changeTimeout = function(timeout){
        this.timeout = timeout;
        resetTimer();
    }
    function callTimeout() {
        if (seconds == 0){
             window.location.href= self.url
        }
    }
    function resetTimer() {
        seconds = self.timeout;
        updateTimer();
        clearTimeout(timer);
        timer = setTimeout(timeoutTick, 1000)
        // 1000 milisec = 1 sec
    }
    function updateTimer(){
        if (document.getElementById('timeout_in')){
            document.getElementById('timeout_in').innerHTML = "-" + seconds + " s";
        }
        if (document.getElementById('timeout_in_top')){
            document.getElementById('timeout_in_top').innerHTML = "-" + seconds + " s";
        }
        console.log('callling timeout in ' + seconds + ' seconds.')
    }
    function timeoutTick(){
        seconds = seconds - 1;
        updateTimer();
        if (seconds <= 0){
            callTimeout();
        }else{
            clearTimeout(timer);
            timer = setTimeout(timeoutTick, 1000)
            // 1000 milisec = 1 sec
        }
    }
};