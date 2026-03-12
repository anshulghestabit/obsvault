````md
# linux-in-container.md

## Build Image
```bash
docker build -t day-1 .
````

## Run Container

```bash
docker run -d -p 3000:3000 --name day-1container day-1
```

## Verify Running Container

```bash
docker ps
```

### Output Observed

* Container ID: `02d922f0f824`
* Image: `day-1`
* Container Name: `day-1container`
* Port Mapping: `0.0.0.0:3000->3000/tcp`

---

## Enter Container

```bash
docker exec -it day-1container /bin/sh
```

This opened an interactive shell inside the running container.

---

## File System Exploration

Command used:

```bash
ls
```

Output observed:

```bash
server.js
```

Observation:

* The application file `server.js` is present inside `/app`

---

## Process Exploration

Command used:

```bash
ps aux
```

Output observed:

```bash
PID   USER     TIME  COMMAND
1     root     0:00  node server.js
14    root     0:00  /bin/sh
21    root     0:00  ps aux
```

Observation:

* The main container process is `node server.js`
* It runs as `PID 1`
* The shell session is also visible as a running process

---

## Logs Exploration

Command used:

```bash
docker logs day-1container
```

Output observed:

```bash
Server running on port 3000
```

Observation:

* Application logs are accessible through Docker logs
* The Node server started successfully on port 3000

---

## Container Linux Notes

* The container runs a lightweight Linux environment based on `node:18-alpine`
* The working directory is `/app`
* The Node application is running successfully inside the container
* Basic Linux inspection commands worked correctly inside the container

---

## Conclusion

This task demonstrated how a Docker container can behave like a minimal Linux server environment. The Node app was built into an image, started as a container, accessed using `/bin/sh`, and inspected using Linux commands and Docker logs.

```
```
