// Stolen from
// https://stackoverflow.com/questions/4562012/make-a-link-open-on-double-click
jQuery(
    function($) {
        $(".dbl-click-link")
        .click(
            function() { return false; }
        ).dblclick(
            function() {
                window.location = this.href;
                return false;
            }
        ).keydown(
            function(event) {
                switch(event.which) {
                    case 13:
                    case 32:
                        window.location = this.href;
                }
                return false;
            }
        );
    }
);