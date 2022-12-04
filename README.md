# stravadiscordbot

The world famous discord strava leaderboard bot! 

Everything deploys using docker-compose.

`docker-compose up`

Some secrets are needed, set this up in `.secrets.env` in the root directory of this repo. As long as you keep to the same naming convention, you won't check this file in as its listed in `.gitignore`

```
STRAVACLUB_PRETTYNAME="Utrarunning Discord Server"
STRAVACLUB="Utrarunning Discord Server"
STRAVATOKEN="<token>"
STRAVAREFRESHTOKEN="<token>"
STRAVACLIENTID=65536
STRAVASECRET="<secret>"
DISCORDTOKEN=<token>
MONGO_USER="root"
MONGO_PASSWD="password"
MONGO_DB_NAME="db"
MONGO_DB_HOST="mongo"
```

Note! `DISCORDTOKEN` does not like quotes if you see a 403 error.
