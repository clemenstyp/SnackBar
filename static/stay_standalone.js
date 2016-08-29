
// Mobile Safari in standalone mode
//if (('standalone' in window.navigator) && window.navigator.standalone) {
    window.addEventListener('load', function() {

        var links = document.links,
            link,
            i;

        for (i = 0; i < links.length; i++) {
            // Don't do this for javascript: links
            if (~(link = links[i]).href.toLowerCase().indexOf('javascript') || true) {
                link.addEventListener('click', function(event) {
                    top.location.href = this.href;
                    event.returnValue = false;
                }, false);
            }
        }

    }, false);

//}
