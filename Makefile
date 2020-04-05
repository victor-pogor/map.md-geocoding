all: docker-build-image docker-make-zip

docker-build-image:
	docker build -t map-md:1.0 . --file Dockerfile

docker-make-zip:
	docker run --rm -w /usr/src/map-md map-md:1.0 bash -c "pbt compile && pbt zip"
