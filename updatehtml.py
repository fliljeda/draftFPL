from leagueinfo import *




def teamHtml(team):
    html = f"""
            <div class="col-md-4">
                <p><font size="8">
                    {str(team.name)}
                </font></p> 
            </div>
            <div class="col-md-4">
                <p><font size="8">
                    {"Total: " + str(team.pointsTotal)}
                </font></p> 
            </div>
            <div class="col-md-4">
                <p><font size="8">
                    {"GW:" + str(team.pointsGw) + "p"}
                </font></p> 
            </div>
    """
    return html

def buildHtmlTeamDiv(team):
    html_text = f"""
    <div class="panel panel-default">
        <div class="panel-heading"> 
            {teamHtml(team)}
        </div>
        <div class="panel-body">
        </div>
    </div>
    """
    return html_text


def buildHtmlLeague(league):

    html_begin = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.0/css/bootstrap.min.css">
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.0/js/bootstrap.min.js"></script>

        <script>
            setTimeout(function(){
               window.location.reload(1);
            }, 5000);
        </script>
        <title>
            No Slack Draft Current GW Standings
        </title>
    </head>
    <body> 

    """

    html_final = html_begin
    for team in league.teams:
        html_final += buildHtmlTeamDiv(team)

    html_end = """
    </body>
    """


    html_final += html_end

    return html_final


loop_n = 0
while True:
    updateScores(league)
    sortLeague(league, gameweek=False)
    html = buildHtmlLeague(league)

    with open('index.html', 'w+') as f:
        f.write(html)
    loop_n += 1
    time.sleep(5)



