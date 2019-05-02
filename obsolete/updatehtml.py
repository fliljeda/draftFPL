from leagueinfo import *




def teamHtml(team):
    html = f"""
            <h5 class="card-title">
                {str(team.name)}
            </h5>
            <div class="card-body row px-0">
                <div class="col">
                    {"Total: " + str(team.pointsTotal)}
                </div>
                <div class="col">
                    {"GW:" + str(team.pointsGw) + "p"}
                </div>
            </div>
    """
    return html

def buildHtmlTeamDiv(team):
    html_text = f"""
    <div class="card mt-3 shadow-sm">
        <div class="card-body">
            {teamHtml(team)}
        </div>
    </div>
    """
    return html_text

def buildHtmlLeague(league):

    html_begin = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
        <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>

        <script>
            setTimeout(function(){{
               window.location.reload(1);
            }}, 5000);
        </script>
        <title>
            No Slack Draft GW{league.currentGw}
        </title>
    </head>
    <body class="bg-light"> 
        <main class="container">
    """

    html_final = html_begin
    for team in league.teams:
        html_final += buildHtmlTeamDiv(team)

    html_end = """
        </main>
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



