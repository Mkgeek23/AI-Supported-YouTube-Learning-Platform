# Rebuild the image
docker build -t youtube-learning-platform .

# Run the container
docker run -p 5000:5000 --env-file .env youtube-learning-platform
