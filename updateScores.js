var wsLoc = "wss://noslack.se/ws/"
var ws = new WebSocket(wsLoc);
ws.onmessage = function(event){
    msg= JSON.parse(event.data)

    var teamContainer = document.getElementById("team-container")
    teamContainer.innerHTML = ""
    var template = document.getElementById("team-template")

    for(x in msg){
        teamVals = msg[x]
        var clone = template.content.cloneNode(true).children[0]
        var teamName = clone.getElementsByClassName("team-name")[0]
        var pointsTot = clone.getElementsByClassName("team-points-total")[0]
        var pointsGw = clone.getElementsByClassName("team-points-gw")[0]

        teamName.innerHTML = teamVals["name"]
        pointsTot.innerHTML = "Total: " + teamVals["points-total"]
        pointsGw.innerHTML = "GW: " + teamVals["points-gw"]

        teamContainer.append(clone)
    }

};
