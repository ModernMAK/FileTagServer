function addTagToSearchBox(searchboxId, escapedTagName) {
    let searchbox = document.getElementById(searchboxId);
    searchbox.value += escapedTagName + " ";
}

function removeTagToSearchBox(searchboxId, escapedTagName) {
    let searchbox = document.getElementById(searchboxId);
    searchbox.value += "Not " + escapedTagName + " ";


}