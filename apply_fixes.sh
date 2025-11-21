#!/bin/bash
# This script will create a fixed version of index.html

# Backup original
cp index.html index.html.backup

# Create the fixed version
sed -i '' '/<!-- Mobile Bottom Navigation -->/,/<\/div>/d' index.html

# Add the corrected mobile navigation section
sed -i '' '/<!-- Tab Content -->/a\
            <!-- Mobile Bottom Navigation -->\
            <div class="mobile-bottom-nav lg:hidden">\
                <button class="tab-button active flex flex-col items-center text-purple-400" data-tab="map">\
                    <i class="fas fa-map"></i>\
                    <span class="text-xs mt-1">Map</span>\
                </button>\
                <button class="tab-button flex flex-col items-center text-gray-400" data-tab="events">\
                    <i class="fas fa-calendar"></i>\
                    <span class="text-xs mt-1">Events</span>\
                </button>\
                <button class="tab-button flex flex-col items-center text-gray-400" data-tab="videos">\
                    <i class="fas fa-video"></i>\
                    <span class="text-xs mt-1">Videos</span>\
                </button>\
                <button class="tab-button flex flex-col items-center text-gray-400" data-tab="chat">\
                    <i class="fas fa-comments"></i>\
                    <span class="text-xs mt-1">Chat</span>\
                </button>\
            </div>\
' index.html

echo "Fixes applied successfully!"
echo "Original file backed up as index.html.backup"
