build:
	podman build -t pyblog-webapp .

run:
	podman run -p 1337:80 --rm -it --name pyblog-test -v`pwd`/app:/var/www/html sccommunity-webapp