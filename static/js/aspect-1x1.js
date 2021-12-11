var __shared_aspect_func =
    function(event) {
        $(".aspect-1x1").each(
            function() {
                var w = $(this).width();
                $(this).css("height",w);
            }
        )
    };



jQuery(
    function($) {
        $(window).ready(
            function(event) {
                __shared_aspect_func(event);
            }
        )
    }
);
jQuery(
    function($) {
        $(window).resize(
            function(event) {
                __shared_aspect_func(event);
//                __shared_remainder_func(event);
            }
        )
    }
);