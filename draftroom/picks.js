var wsLoc = "wss://noslack.se/ws/"
var ws = new WebSocket(wsLoc);

class Player {
    constructor(player){
        this.name = player.name;
        this.team = player.team;
        this.pos = player.pos; // "GK" "DEF" "MID" "FWD"
        this.teamCode = player.team_code;
        this.id = "playerid_" + player.id;
    }

    // Returns the shirt tag of players
    getShirtUrl(){
        var start = "https://draft.premierleague.com/img/shirts/standard/shirt_";
        var middle = this.pos == "GK" ? this.teamCode + "_1" : this.teamCode;
        var end = "-36.png";
        return start + middle + end;
    }
}

class LeagueTeam {
    constructor(name, playersObj){
        this.name = name;
        this.players = [];
        this.addPicks(playersObj)
    }

    addPicks(picks){
        for(var player of picks){
            this.players.push(new Player(player));
        }
    }

}

class Model {
    constructor(){
        this.teams = [];
    }

    // Adds new teams or updates them if already exists
    updateTeams(picks){
        for(var team in picks){
            var teamExists = false
            for(var existingTeam of this.teams){
                if(team == existingTeam.name){
                    existingTeam.addPicks(picks[team]);
                    teamExists = true;
                }
            }
            if(!teamExists){
                var t = new LeagueTeam(team, picks[team]);
                this.teams.push(t);
            }
        }
    }

    printTeams() {
        for(var team of this.teams){
            console.log("TEAM:::::" + team.name);
            for(var player of team.players){
                console.log(player.name);
            }
        }
    }
    // "draws" the teams and picks to the html using ids
    draw(){
        for(var team of this.teams){
            var team_dom = document.getElementById(team.name);
            if(team_dom == null){
                var teamContainerLeft = document.getElementById("team-container-left");
                var teamContainerRight = document.getElementById("team-container-right");
                var template = document.getElementById("team-template"); 
                var clone = template.content.cloneNode(true).children[0];
                clone.id = team.name;
                var nametag = clone.getElementsByClassName("team-name")[0]
                nametag.innerHTML = team.name;

                var teamContainer = null;
                if(teamContainerLeft.children.length > teamContainerRight.children.length){
                    teamContainer = teamContainerRight;
                }else{
                    teamContainer = teamContainerLeft;
                }
                teamContainer.append(clone)
                team_dom = clone;
            }


            var gks =  team_dom.getElementsByClassName("picked-gks")[0]
            var defs = team_dom.getElementsByClassName("picked-defs")[0]
            var mids = team_dom.getElementsByClassName("picked-mids")[0]
            var fwds = team_dom.getElementsByClassName("picked-fwds")[0]

            for(var player of team.players){
                if(document.getElementById(player.id) != null){
                    continue;
                }
                var div = document.createElement("div");
                div.id = player.id;
                var shirtImg = document.createElement("img");
                shirtImg.src = player.getShirtUrl();
                var playerStr = player.name + " (" + player.team + ")";
                div.append(shirtImg);
                div.append(playerStr);

                if(player.pos == "GK"){
                    gks.append(div);
                }else if(player.pos == "DEF"){
                    defs.append(div);
                }else if(player.pos == "MID"){
                    mids.append(div)
                }else if(player.pos == "FWD"){
                    fwds.append(div)
                }else{
                    console.log("NO POS???");
                }
            }
        }
    }

}
var model = new Model();

ws.onmessage = function(event){
    msg= JSON.parse(event.data);
	var action = msg["action"];
    var picks = msg["picks"];
    if(action == "update"){
        model.updateTeams(picks);
        //model.printTeams();
        model.draw();
    }else if(action == "full"){
    }
};


