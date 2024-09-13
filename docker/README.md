# Docker Stuff
This is a placeholder for now

- [ ] Allow user to set custom username and password for TTYD
- [x] Fix tar issues on Alpine (for example, installing Java doesn't work)
- [x] Add persistent directory for applicationFolder
- [x] Remove Kivy dependencies from Alpine build with a custom .spec and reqs
- [ ] Eventually turn Alpine Build into Docker image, and don't upload Alpine as an artifact
- [x] If Alpine is detected, set the is_docker flag to True in check_docker()
- [x] On Linux, if headless is run by default due to the DISPLAY not being set, it doesn't start Telepath by default, and possibly some other stuff. Check the logic order
- [ ] Offer documentation for building the Docker image similar to this: https://hub.docker.com/_/mariadb
- [x] Make account for Docker Hub
- [ ] For headless update command, disable the ability to update inside of the container with a command, and instead direct the user to the Docker hub documentation
      
<br>

- `dockerfile` is to build the image

- `docker-compose.yml` is to build the container with the image

- `auto-mcs-alpine.zip` is required for this process as well

- `docker-compose up -d`
