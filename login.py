##################################################
##
##
##
##
##
##     NOT NECESSARY FOR MOST API ENDPOINTS
##     Plus the session would not give authenticated
##     responses after login. Needs work
##
##      
##
##
##
##
###################################################
base_url = 'https://draft.premierleague.com/'
login_url = 'https://users.premierleague.com/accounts/login/'
login = input('Login email: ')
password = input('Password: ')
print('Ok!')

params = {
 'password': login,
 'login': password,
 'redirect_uri': 'https://draft.premierleague.com/a/login',
 'app': 'plfpl-web'
}

def draftFetch(uri):
    url = base_url + uri
    resp = session.get(url)
    return resp


#session.post(login_url, data=params)
