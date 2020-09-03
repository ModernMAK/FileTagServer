function addAndTagToSearchBox(searchboxId, escapedTagName) {
    let searchbox = document.getElementById(searchboxId);
    searchbox.value += "" + escapedTagName + " ";
}
function addOrTagToSearchBox(searchboxId, escapedTagName) {
    let searchbox = document.getElementById(searchboxId);
    searchbox.value += "~" + escapedTagName + " ";
}
function addNotTagToSearchBox(searchboxId, escapedTagName) {
    let searchbox = document.getElementById(searchboxId);
    searchbox.value += "-" + escapedTagName + " ";
}
