# Define the image name
$imageName = "zkill-discord-bot"

# Generate the current date and time as the version
$newVersion = Get-Date -Format "yyyyMMddHHmmss"

# Build and run the container
docker build -t "$($imageName):$newVersion" .
docker run -d --restart=always --name $imageName "$($imageName):$newVersion"
