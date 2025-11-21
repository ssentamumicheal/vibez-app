#!/bin/bash
# This script will fix the mobile navigation issue

# First, let's check if we're in the right directory
if [ ! -f "index.html" ]; then
    echo "Error: index.html not found in current directory"
    echo "Current directory: $(pwd)"
    echo "Files in current directory:"
    ls -la
    exit 1
fi

# Create a backup
cp index.html index.html.backup

# Use sed to add the data-tab attributes to mobile navigation buttons
sed -i 's/<button class="tab-button active flex flex-col items-center text-purple-400">/<button class="tab-button active flex flex-col items-center text-purple-400" data-tab="map">/' index.html
sed -i 's/<button class="tab-button flex flex-col items-center text-gray-400">/<button class="tab-button flex flex-col items-center text-gray-400" data-tab="events">/' index.html
sed -i 's/<button class="tab-button flex flex-col items-center text-gray-400">/<button class="tab-button flex flex-col items-center text-gray-400" data-tab="videos">/' index.html
sed -i 's/<button class="tab-button flex flex-col items-center text-gray-400">/<button class="tab-button flex flex-col items-center text-gray-400" data-tab="chat">/' index.html

echo "Mobile navigation fixed successfully!"
echo "Backup created as index.html.backup"
