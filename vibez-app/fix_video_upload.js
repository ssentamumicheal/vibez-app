// Replace the handleVideoUpload function in your index.html

const handleVideoUpload = async (e) => {
    e.preventDefault();
    const authToken = localStorage.getItem('authToken');
    const videoFile = document.getElementById('video-file').files[0];
    const caption = document.getElementById('video-caption').value;
    
    console.log('Upload attempt:', { 
        hasToken: !!authToken, 
        hasFile: !!videoFile, 
        file: videoFile?.name,
        caption: caption 
    });
    
    if (!videoFile) {
        showNotification('Please select a video file', 'error');
        return;
    }
    
    if (!authToken) {
        showNotification('Please log in to upload videos', 'error');
        showAuthForm();
        return;
    }
    
    // Check file size (max 50MB)
    if (videoFile.size > 50 * 1024 * 1024) {
        showNotification('Video file too large (max 50MB)', 'error');
        return;
    }
    
    // Check file type
    const allowedTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/wmv'];
    if (!allowedTypes.includes(videoFile.type)) {
        showNotification('Please select a video file (MP4, AVI, MOV, WMV)', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const formData = new FormData();
        formData.append('video_file', videoFile);
        formData.append('caption', caption || 'No caption');
        
        console.log('Sending upload request...');
        
        const response = await fetch(`${API_BASE_URL}/videos/`, {
            method: 'POST',
            headers: {
                'Authorization': `Token ${authToken}`,
                // Don't set Content-Type - let browser set it with boundary
            },
            body: formData
        });
        
        const responseData = await response.json();
        console.log('Upload response:', { status: response.status, data: responseData });
        
        if (response.ok) {
            showNotification('Video uploaded successfully!', 'success');
            document.getElementById('upload-form').reset();
            fetchVideos(); // Refresh the video list
        } else {
            // More detailed error handling
            let errorMsg = 'Upload failed';
            if (responseData.detail) {
                errorMsg = responseData.detail;
            } else if (responseData.video_file) {
                errorMsg = `Video file: ${responseData.video_file.join(', ')}`;
            } else if (responseData.caption) {
                errorMsg = `Caption: ${responseData.caption.join(', ')}`;
            } else if (typeof responseData === 'object') {
                errorMsg = JSON.stringify(responseData);
            }
            showNotification(`Upload failed: ${errorMsg}`, 'error');
        }
    } catch (error) {
        console.error('Error uploading video:', error);
        showNotification('Network error during upload', 'error');
    } finally {
        showLoading(false);
    }
};

// Update the upload form event listener
if (uploadForm) {
    uploadForm.removeEventListener('submit', handleVideoUpload); // Remove old listener
    uploadForm.addEventListener('submit', handleVideoUpload);
}

// Also update the fetchVideos function to handle authentication
const fetchVideos = async () => {
    const authToken = localStorage.getItem('authToken');
    const userId = localStorage.getItem('userId');
    
    try {
        const headers = {};
        if (authToken) {
            headers['Authorization'] = `Token ${authToken}`;
        }
        
        const response = await fetch(`${API_BASE_URL}/videos/`, { headers });
        if (response.ok) {
            const videos = await response.json();
            allVideos = videos;
            if (userId) {
                myVideos = videos.filter(video => video.user === parseInt(userId));
            }
            renderVideos();
        } else {
            console.error('Failed to fetch videos:', response.status);
        }
    } catch (error) {
        console.error('Failed to fetch videos:', error);
    }
};
