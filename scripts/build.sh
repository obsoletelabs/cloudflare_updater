docker compose -f docker/docker-compose.yml down
docker container remove dev
docker image prune -a
docker compose --project-directory . -f docker/docker-compose.yml up