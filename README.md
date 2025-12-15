# MicroservicesLab-Languages
Services to Enable Learning Language


## Dependencies installation

```
pip install -r requirements.txt
```

## Running the Service

```
uvicorn main:app --reload
```

## Docker

### Build the image

```
docker image build -t <tag> .
```

**Parameters:**
- `docker image build`: Docker command to build an image from a Dockerfile
- `-t <tag>`: Tag the image with a name (replace `<tag>` with your desired image name, e.g., `microserviceslab-languages`)
- `.`: The build context (current directory containing the Dockerfile)

### Run the container

```
docker container run -i -t --rm -p 8000:8000 <tag>:latest
```

**Parameters:**
- `docker container run`: Docker command to run a container from an image
- `-i`: Interactive mode - keeps STDIN open even if not attached
- `-t`: Allocate a pseudo-TTY - provides an interactive terminal
- `--rm`: Automatically remove the container when it exits
- `-p 8000:8000`: Port mapping - maps port 8000 on the host to port 8000 in the container (format: `host_port:container_port`)
- `<tag>:latest`: The image name and tag to run (replace `<tag>` with the same tag used when building the image)