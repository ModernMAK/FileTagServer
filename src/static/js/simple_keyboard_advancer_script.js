$(document).keydown(
    function(e) {
        let url_obj = new URL(window.location.href)
        let local_url =  window.location.href.split('?')[0]
        let params = new URLSearchParams(url_obj.search)
        let id = parseInt(params.get("id"))

        switch (e.key)
        {
            case "Left": // IE/Edge specific value
            case "ArrowLeft":
                id = id - 1
                params.set("id",id.toString())
                let result_url_l = local_url.concat("?",params.toString())
                window.location.href = result_url_l
                break
            case "Right": // IE/Edge specific value
            case "ArrowRight":
                id = id + 1
                params.set("id",id.toString())
                let result_url_r = local_url.concat("?",params.toString())
                window.location.href = result_url_r
                break
        }
}
)