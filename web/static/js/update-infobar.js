jQuery(
    function($) {
        $(".update-infobar")
        .click(
            function()
            {
                var data_set_name = $(this).attr('data-fts-source');
                var data_set_json = $(data_set_name).html();
//                data_set_json = data_set_json.substring(1,data_set_json.length-1);
                var data_set = JSON.parse(data_set_json);
                var data_index = $(this).attr('data-fts-index');
                var data = data_set[data_index];
                var template_path = $('#infobar-template').attr("src");
                $.get(template_path,
                    function(tempate)
                    {
//                        $.Mustache.render
//                        $.mustache.render
                        var text = Mustache.render(template, data);
                        $("#infobar-region").html(text);
                    },
                    "text"
                );
                return false;
            }
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