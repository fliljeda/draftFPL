var wsLoc = "wss://noslack.se/ws/"
var ws = new WebSocket(wsLoc);

class Player {
    constructor(name, team, pos){
        this.name = name;
        this.team = team;
        this.pos = pos;
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
            this.players.push(new Player(player.name, player.team, player.pos));
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
                var teamContainer = document.getElementById("team-container");
                var template = document.getElementById("team-template"); 
                var clone = template.content.cloneNode(true).children[0];
                clone.id = team.name;
                teamContainer.append(clone)
                team_dom = clone;
            }

            var nametag = team_dom.getElementsByClassName("team-name")[0]
            nametag.innerHTML = team.name;

            var gks =  team_dom.getElementsByClassName("picked-gks")[0]
            var defs = team_dom.getElementsByClassName("picked-defs")[0]
            var mids = team_dom.getElementsByClassName("picked-mids")[0]
            var fwds = team_dom.getElementsByClassName("picked-fwds")[0]
            gks.innerHTML = "";
            defs.innerHTML = "";
            mids.innerHTML = "";
            fwds.innerHTML = "";

            for(var player of team.players){
                var str = "<p>" + player.name + " (" + player.team + ")" + "</p>";
                if(player.pos == "GK"){
                    gks.innerHTML += str;
                }else if(player.pos == "DEF"){
                    defs.innerHTML += str;
                }else if(player.pos == "MID"){
                    mids.innerHTML += str;
                }else if(player.pos == "FWD"){
                    fwds.innerHTML += str;
                }else{
                    console.log("NO POS???");
                }
            }
        }
    }

}
var model = new Model();

ws.onmessage = function(event){
    msg= JSON.parse(event.data)
	var action = msg["action"];
    var picks = msg["picks"];
    if(action == "update"){
        model.updateTeams(picks);
        //model.printTeams();
        model.draw();
    }else if(action == "full"){
    }
};


