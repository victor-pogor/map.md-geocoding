all: docker-build-image docker-make-zip

docker-build-image:
	docker build -t map-md:1.0 . --file Dockerfile

docker-make-zip:
	docker run --rm -v ${PWD}:/usr/src/map-md:Z map-md:1.0 bash -c "pbt compile && pbt zip"
