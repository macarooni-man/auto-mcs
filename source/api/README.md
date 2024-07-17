# auto-mcs API

The goal of this API is to have a way of controlling one or multiple minecraft servers remotely from another auto-mcs client.

To reach this goal we first need to abstract functionality that it's currently coupled to the UI and have a collection of curated objects that will be in charge of executing the logic through HTTP requests (endpoints).

This API is being developed using [Fast-API](https://fastapi.tiangolo.com/) with a custom [function](./main.py#L61) that turns object methods into endpoints

## Endpoints Roadmap

### Main Actions

- [ ] Authentication
- [ ] List Current Servers
- [ ] Open Server
- [ ] Get Server Data By Name

### Server Specific Actions

- Main

  - [ ] Launch

- Backup

  - [ ] Save
  - [ ] Set Automatic Backups
  - [ ] Set Maximum Backups
  - [ ] Restore From Backup
    - [ ] List Current Backups

- Rules

  - [ ] Get Operators List
  - [ ] Get Banned Users List
  - [ ] Get Whitelisted Users List
  - [ ] Get User Data
  - [ ] Set User As Operator / Promote User
  - [ ] Ban User
  - [ ] Unban User
  - [ ] Set Rule As Global / Local
  - [ ] Ban a Range of IPs
  - [ ] Whitelist a Range of IPs

- amscript

  - [ ] Load Script
  - [ ] Save Script

- Settings

  - [ ] Set Memory Usage
  - [ ] Set Custom Launch Flags
  - [ ] Set MOTD
  - [ ] Set Server IP
  - [ ] Set Automatic Updates
  - [ ] Set Server Name
  - [ ] Update Server
  - [ ] Change Server.jar
  - [ ] Delete Server
