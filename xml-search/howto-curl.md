# Howto use the API for search

use `python3 zetcom_session.py -u USER -s URL` for the session id.

`curl -X "POST" "URL/ria-ws/application/module/Registrar/search" -u "user[USER]:session[SESSIONID]" -H "Content-Type: application/xml" --data @registrar.xml`
