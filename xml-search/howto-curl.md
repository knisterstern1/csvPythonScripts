# Howto use the API for search

use `python3 zetcom_session.py -u TCH -s https://mptest.kumu.swiss` for the session id.

`curl -X "POST" "https://mptest.kumu.swiss/ria-ws/application/module/Registrar/search" -u "user[USER]:session[SESSIONID]" -H "Content-Type: application/xml" --data @registrar.xml`
