function addAndTagToSearchBox(searchboxId, escapedTagName) {
    let searchbox = document.getElementById(searchboxId);
    if (searchbox.value.length !== 0 && searchbox.value.slice(-1) !== " ") {
        searchbox.value += " "
    }
    searchbox.value += "" + escapedTagName;
}

function addOrTagToSearchBox(searchboxId, escapedTagName) {
    let searchbox = document.getElementById(searchboxId);
    if (searchbox.value.length !== 0 && searchbox.value.slice(-1) !== " ") {
        searchbox.value += " "
    }
    searchbox.value += "~" + escapedTagName;
}

function addNotTagToSearchBox(searchboxId, escapedTagName) {
    let searchbox = document.getElementById(searchboxId);
    if (searchbox.value.length !== 0 && searchbox.value.slice(-1) === " ") {
        searchbox.value += " "
    }
    searchbox.value += "-" + escapedTagName;
}
