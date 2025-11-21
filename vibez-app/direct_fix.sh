#!/bin/bash
echo "Applying direct fixes to index.html..."

# Backup the original file
cp index.html index.html.backup2

# Use sed to fix JavaScript issues
sed -i 's/document.addEventListener(.DOMContentLoaded., () => {/document.addEventListener("DOMContentLoaded", function() {/' index.html

# Fix the button event listeners
sed -i '/DOM.getStartedButton.addEventListener(.click., ViewManager.showAuthForm);/c\
    DOM.getStartedButton.addEventListener("click", function(e) {\
        e.preventDefault();\
        document.getElementById("landing-page").classList.add("hidden");\
        document.getElementById("auth-container").classList.remove("hidden");\
    });' index.html

sed -i '/DOM.joinNowButton.addEventListener(.click., ViewManager.showAuthForm);/c\
    DOM.joinNowButton.addEventListener("click", function(e) {\
        e.preventDefault();\
        document.getElementById("landing-page").classList.add("hidden");\
        document.getElementById("auth-container").classList.remove("hidden");\
    });' index.html

# Add simple initialization
sed -i '/console.log(.Vibez app initialized successfully!.);/a\
\
    // Force initialization\
    setTimeout(function() {\
        if (typeof ViewManager !== "undefined") {\
            console.log("ViewManager loaded");\
        } else {\
            console.log("ViewManager not found - using fallback");\
            // Fallback initialization\
            var getStartedBtn = document.getElementById("get-started-button");\
            if (getStartedBtn) {\
                getStartedBtn.onclick = function() {\
                    document.getElementById("landing-page").classList.add("hidden");\
                    document.getElementById("auth-container").classList.remove("hidden");\
                };\
            }\
        }\
    }, 1000);' index.html

echo "Direct fixes applied!"
