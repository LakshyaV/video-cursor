// Enhanced DaVinci Resolve UI with Backend Integration
document.addEventListener('DOMContentLoaded', function() {
    initializeInterface();
    setupEventListeners();
    initializeAudioMeters();
    initializeTimeline();
    initializeTimelineResize();
    initializeTimelineScrolling();
    initializeInspector();
    initializeToolbox();
    initializeMicroInteractions();
    initializeKeyboardShortcuts();
    initializeWorkspaceOrganization();
    initializeVideoEditor();
});

// Backend API configuration
const API_BASE = '/api';
let currentVideoId = null;
let uploadedFiles = new Map();

function initializeInterface() {
    // Set initial time display with smooth animation
    updateTimeDisplay();
    
    // Initialize media pool with enhanced interactions
    initializeMediaPool();
    
    // Initialize video controls with professional feedback
    initializeVideoControls();
    
    // Add loading animation
    addLoadingAnimation();
}

function setupEventListeners() {
    // Top bar tabs with smooth transitions
    const topTabs = document.querySelectorAll('.tab');
    topTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Smooth transition for tab switching
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 100);
            
            // Remove active class from sibling tabs
            const siblings = this.parentElement.querySelectorAll('.tab');
            siblings.forEach(s => s.classList.remove('active'));
            // Add active class to clicked tab
            this.classList.add('active');
        });
        
        // Add hover sound effect simulation
        tab.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-1px)';
        });
        
        tab.addEventListener('mouseleave', function() {
            if (!this.classList.contains('active')) {
                this.style.transform = 'translateY(0)';
            }
        });
    });
    
    // Inspector tabs with enhanced feedback
    const inspectorTabs = document.querySelectorAll('.inspector-tab');
    inspectorTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Smooth transition
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 100);
            
            // Remove active class from sibling tabs
            const siblings = this.parentElement.querySelectorAll('.inspector-tab');
            siblings.forEach(s => s.classList.remove('active'));
            // Add active class to clicked tab
            this.classList.add('active');
        });
    });
    
    // Navigation modules with professional animations
    const navModules = document.querySelectorAll('.nav-module');
    navModules.forEach(module => {
        module.addEventListener('click', function() {
            // Smooth scale animation
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
            
            // Remove active class from all modules
            navModules.forEach(m => m.classList.remove('active'));
            // Add active class to clicked module
            this.classList.add('active');
        });
    });
    
    // Media pool items with enhanced selection
    const mediaItems = document.querySelectorAll('.media-item');
    mediaItems.forEach(item => {
        item.addEventListener('click', function() {
            // Smooth selection animation
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 100);
            
            // Remove selection from all items
            mediaItems.forEach(i => i.classList.remove('selected'));
            // Add selection to clicked item
            this.classList.add('selected');
        });
    });
    
    // Folder tree items with smooth interactions
    const folderItems = document.querySelectorAll('.folder-item');
    folderItems.forEach(item => {
        item.addEventListener('click', function() {
            // Smooth selection animation
            this.style.transform = 'translateX(4px)';
            setTimeout(() => {
                this.style.transform = 'translateX(0)';
            }, 150);
            
            // Remove active class from all items
            folderItems.forEach(i => i.classList.remove('active'));
            // Add active class to clicked item
            this.classList.add('active');
        });
    });
}

function initializeMediaPool() {
    // Enhanced hover effects for media items
    const mediaItems = document.querySelectorAll('.media-item');
    
    mediaItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            if (!this.classList.contains('selected')) {
                this.style.transform = 'translateY(-2px) scale(1.02)';
                this.style.boxShadow = '0 4px 16px rgba(0, 168, 255, 0.2)';
            }
        });
        
        item.addEventListener('mouseleave', function() {
            if (!this.classList.contains('selected')) {
                this.style.transform = 'translateY(0) scale(1)';
                this.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.3)';
            }
        });
    });
}

function initializeVideoControls() {
    // Enhanced video control functionality
    let isPlaying = false;
    let currentTime = 0;
    let playbackInterval;
    
    function togglePlay() {
        isPlaying = !isPlaying;
        const playBtn = document.querySelector('.play-btn i');
        
        // Smooth button animation
        playBtn.parentElement.style.transform = 'scale(0.95)';
        setTimeout(() => {
            playBtn.parentElement.style.transform = 'scale(1)';
        }, 100);
        
        if (isPlaying) {
            playBtn.className = 'fas fa-pause';
            playBtn.parentElement.style.background = 'var(--accent-primary-hover)';
            startPlayback();
        } else {
            playBtn.className = 'fas fa-play';
            playBtn.parentElement.style.background = 'var(--accent-primary)';
            pausePlayback();
        }
    }
    
    function pausePlayback() {
        isPlaying = false;
        if (playbackInterval) {
            clearInterval(playbackInterval);
        }
    }
    
    function stopPlayback() {
        isPlaying = false;
        currentTime = 0;
        updateTimeDisplay();
        updatePlayhead(0);
        const playBtn = document.querySelector('.play-btn i');
        playBtn.className = 'fas fa-play';
        playBtn.parentElement.style.background = 'var(--accent-primary)';
        
        if (playbackInterval) {
            clearInterval(playbackInterval);
        }
    }
    
    function startPlayback() {
        // Simulate smooth playback
        playbackInterval = setInterval(() => {
            if (isPlaying) {
                currentTime += 0.1;
                updateTimeDisplay();
                updatePlayhead(currentTime);
            }
        }, 100);
    }
    
    // Video control buttons with enhanced feedback
    const playBtn = document.querySelector('.play-btn');
    const stopBtn = document.querySelector('.control-btn:nth-child(4)');
    
    if (playBtn) {
        playBtn.addEventListener('click', togglePlay);
    }
    
    if (stopBtn) {
        stopBtn.addEventListener('click', stopPlayback);
    }
    
    // Add hover effects to all control buttons
    const controlBtns = document.querySelectorAll('.control-btn');
    controlBtns.forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px) scale(1.05)';
        });
        
        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Make functions globally available
    window.togglePlay = togglePlay;
    window.stopPlayback = stopPlayback;
}

function initializeAudioMeters() {
    // Professional audio meter animation
    const meterBars = document.querySelectorAll('.meter-level');
    
    function animateMeters() {
        meterBars.forEach((bar, index) => {
            // Create more realistic audio meter behavior
            const baseHeight = 20 + Math.sin(Date.now() * 0.01 + index) * 30;
            const randomVariation = Math.random() * 20;
            const randomHeight = Math.max(5, Math.min(95, baseHeight + randomVariation));
            
            bar.style.height = randomHeight + '%';
            
            // Add color variation based on level
            if (randomHeight > 80) {
                bar.style.background = 'linear-gradient(to top, #10b981 0%, #f59e0b 50%, #ef4444 100%)';
            } else if (randomHeight > 60) {
                bar.style.background = 'linear-gradient(to top, #10b981 0%, #f59e0b 100%)';
            } else {
                bar.style.background = 'linear-gradient(to top, #10b981 0%, #10b981 100%)';
            }
        });
    }
    
    // Animate meters with varying intervals for more realistic effect
    setInterval(animateMeters, 80);
}

function initializeTimeline() {
    // Enhanced timeline interactions
    const timeline = document.querySelector('.timeline');
    const playhead = document.querySelector('.playhead');
    
    if (timeline && playhead) {
        timeline.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const percentage = (x / rect.width) * 100;
            
            // Smooth playhead movement
            playhead.style.transition = 'left 0.2s cubic-bezier(0.4, 0, 0.2, 1)';
            playhead.style.left = percentage + '%';
            
            // Update time display based on position
            const timeInSeconds = (percentage / 100) * 300;
            updateTimeFromSeconds(timeInSeconds);
            
            // Remove transition after animation
            setTimeout(() => {
                playhead.style.transition = 'none';
            }, 200);
        });
    }
    
    // Enhanced clip interactions
    const clips = document.querySelectorAll('.clip');
    const trackLabels = document.querySelectorAll('.track-label');
    trackLabels.forEach(tl => {
        tl.addEventListener('click', function(e) {
            // Do not interfere with context menu or controls
            if (e.target.closest('.track-controls')) return;
            trackLabels.forEach(x => x.classList.remove('active'));
            this.classList.add('active');
        });
    });
    clips.forEach(clip => {
        clip.addEventListener('click', function(e) {
            e.stopPropagation();
            
            // Smooth selection animation
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 100);
            
            // Remove selection from other clips
            clips.forEach(c => c.classList.remove('selected'));
            // Add selection to clicked clip
            this.classList.add('selected');
        });
        
        // Enhanced drag functionality
        let isDragging = false;
        let startX = 0;
        let startLeft = 0;
        
        clip.addEventListener('mousedown', function(e) {
            isDragging = true;
            startX = e.clientX;
            startLeft = parseFloat(this.style.left) || 0;
            this.style.zIndex = '1000';
            this.style.transform = 'scale(1.05)';
            this.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.4)';
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', function(e) {
            if (isDragging) {
                const deltaX = e.clientX - startX;
                const newLeft = startLeft + (deltaX / timeline.offsetWidth) * 100;
                clip.style.left = Math.max(0, Math.min(90, newLeft)) + '%';
            }
        });
        
        document.addEventListener('mouseup', function() {
            if (isDragging) {
                isDragging = false;
                clip.style.zIndex = '1';
                clip.style.transform = 'scale(1)';
                clip.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.3)';
            }
        });
    });
}

function initializeInspector() {
    // Enhanced property group interactions
    const propertyHeaders = document.querySelectorAll('.property-header');
    propertyHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const group = this.parentElement;
            const content = group.querySelector('.property-content');
            
            // Smooth expand/collapse animation
            if (content) {
                group.classList.toggle('expanded');
                
                if (group.classList.contains('expanded')) {
                    content.style.maxHeight = '0';
                    content.style.overflow = 'hidden';
                    content.style.display = 'block';
                    
                    // Animate height
                    const height = content.scrollHeight;
                    content.style.maxHeight = height + 'px';
                    
                    setTimeout(() => {
                        content.style.maxHeight = 'none';
                        content.style.overflow = 'visible';
                    }, 300);
                } else {
                    content.style.maxHeight = content.scrollHeight + 'px';
                    content.style.overflow = 'hidden';
                    
                    setTimeout(() => {
                        content.style.maxHeight = '0';
                    }, 10);
                    
                    setTimeout(() => {
                        content.style.display = 'none';
                    }, 300);
                }
            }
        });
    });
    
    // Enhanced toggle switches
    const toggleSwitches = document.querySelectorAll('.toggle-switch input');
    toggleSwitches.forEach(toggle => {
        toggle.addEventListener('change', function() {
            // Add visual feedback
            const label = this.nextElementSibling;
            label.style.transform = 'scale(0.95)';
            setTimeout(() => {
                label.style.transform = 'scale(1)';
            }, 100);
            
            console.log(`${this.id} is now ${this.checked ? 'on' : 'off'}`);
        });
    });
}

function initializeToolbox() {
    // Enhanced toolbox interactions
    const categoryHeaders = document.querySelectorAll('.category-header');
    categoryHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const category = this.parentElement;
            const items = category.querySelector('.category-items');
            
            // Smooth expand/collapse animation
            if (items) {
                category.classList.toggle('expanded');
                
                if (category.classList.contains('expanded')) {
                    items.style.maxHeight = '0';
                    items.style.overflow = 'hidden';
                    items.style.display = 'block';
                    
                    const height = items.scrollHeight;
                    items.style.maxHeight = height + 'px';
                    
                    setTimeout(() => {
                        items.style.maxHeight = 'none';
                        items.style.overflow = 'visible';
                    }, 300);
                } else {
                    items.style.maxHeight = items.scrollHeight + 'px';
                    items.style.overflow = 'hidden';
                    
                    setTimeout(() => {
                        items.style.maxHeight = '0';
                    }, 10);
                    
                    setTimeout(() => {
                        items.style.display = 'none';
                    }, 300);
                }
            }
        });
    });
    
    // Enhanced toolbox items
    const toolboxItems = document.querySelectorAll('.toolbox-item');
    toolboxItems.forEach(item => {
        item.addEventListener('click', function() {
            // Smooth selection animation
            this.style.transform = 'translateX(4px)';
            setTimeout(() => {
                this.style.transform = 'translateX(0)';
            }, 150);
            
            // Remove selection from sibling items
            const siblings = this.parentElement.querySelectorAll('.toolbox-item');
            siblings.forEach(s => s.classList.remove('selected'));
            // Add selection to clicked item
            this.classList.add('selected');
        });
    });
}

function initializeMicroInteractions() {
    // Add subtle hover effects to all interactive elements
    const interactiveElements = document.querySelectorAll('button, .tab, .media-item, .clip, .folder-item, .toolbox-item');
    
    interactiveElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            if (!this.classList.contains('active') && !this.classList.contains('selected')) {
                this.style.transition = 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)';
            }
        });
    });
    
    // Add ripple effect to buttons
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
}

function initializeKeyboardShortcuts() {
    // Enhanced keyboard shortcuts with visual feedback
    document.addEventListener('keydown', function(e) {
        switch(e.code) {
            case 'Space':
                e.preventDefault();
                togglePlay();
                showKeyboardFeedback('Play/Pause');
                break;
            case 'KeyK':
                e.preventDefault();
                togglePlay();
                showKeyboardFeedback('Pause');
                break;
            case 'KeyJ':
                e.preventDefault();
                stopPlayback();
                showKeyboardFeedback('Stop');
                break;
            case 'Escape':
                e.preventDefault();
                // Deselect all items with animation
                document.querySelectorAll('.selected').forEach(item => {
                    item.style.transform = 'scale(0.98)';
                    setTimeout(() => {
                        item.style.transform = 'scale(1)';
                        item.classList.remove('selected');
                    }, 100);
                });
                showKeyboardFeedback('Deselect All');
                break;
        }
    });
}

function showKeyboardFeedback(action) {
    // Create visual feedback for keyboard shortcuts
    const feedback = document.createElement('div');
    feedback.textContent = action;
    feedback.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--accent-primary);
        color: white;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
        z-index: 10000;
        animation: fadeInOut 2s ease-in-out;
        pointer-events: none;
    `;
    
    document.body.appendChild(feedback);
    
    setTimeout(() => {
        feedback.remove();
    }, 2000);
}

function addLoadingAnimation() {
    // Add subtle loading animation to the interface
    const appContainer = document.querySelector('.app-container');
    appContainer.style.opacity = '0';
    appContainer.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        appContainer.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
        appContainer.style.opacity = '1';
        appContainer.style.transform = 'translateY(0)';
    }, 100);
}

function updateTimeDisplay() {
    const timeDisplays = document.querySelectorAll('.timecode-display');
    timeDisplays.forEach(display => {
        const now = new Date();
        const timeString = now.toTimeString().split(' ')[0];
        display.textContent = timeString;
    });
}

function updateTimeFromSeconds(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const frames = Math.floor((seconds % 1) * 30);
    
    const timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}:${frames.toString().padStart(2, '0')}`;
    
    const timeDisplays = document.querySelectorAll('.timecode-display');
    timeDisplays.forEach(display => {
        display.textContent = timeString;
    });
}

function updatePlayhead(position) {
    const playhead = document.querySelector('.playhead');
    if (playhead) {
        const percentage = (position / 300) * 100;
        playhead.style.left = Math.min(100, Math.max(0, percentage)) + '%';
    }
}

// Workspace Organization Features
function initializeWorkspaceOrganization() {
    // Initialize inspector toggle
    initializeInspectorToggle();
    
    // Initialize context menu for tracks
    initializeTrackContextMenu();
    
    // Initialize track height controls
    initializeTrackHeightControls();
    
    // Initialize track renaming
    initializeTrackRenaming();
    
    // Initialize media bins
    initializeMediaBins();
    
    // Initialize workspace presets
    initializeWorkspacePresets();
    
    // Initialize clip color coding
    initializeClipColorCoding();
    
    // Initialize volume sliders
    initializeVolumeSliders();
}

function initializeInspectorToggle() {
    const rightPanel = document.getElementById('rightPanel');
    const inspectorTab = document.querySelector('.tab-group .tab:last-child'); // Inspector tab (last tab)
    
    console.log('Initializing inspector toggle...');
    console.log('Right panel found:', !!rightPanel);
    console.log('Inspector tab found:', !!inspectorTab);
    
    if (inspectorTab && rightPanel) {
        console.log('Both elements found, setting up event listener...');
        
        // Initialize the tab state on page load
        updateInspectorTabState();
        
        inspectorTab.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Inspector tab clicked!');
            
            // Toggle the right panel visibility
            rightPanel.classList.toggle('collapsed');
            console.log('Panel collapsed:', rightPanel.classList.contains('collapsed'));
            
            // Update the tab appearance
            updateInspectorTabState();
            
            // Show feedback
            showKeyboardFeedback(rightPanel.classList.contains('collapsed') ? 'Inspector Hidden' : 'Inspector Shown');
        });
        
        function updateInspectorTabState() {
            const isCollapsed = rightPanel.classList.contains('collapsed');
            console.log('Updating inspector tab state. Collapsed:', isCollapsed);
            
            if (isCollapsed) {
                // Panel is closed - make tab look inactive
                inspectorTab.classList.remove('active');
                inspectorTab.style.background = 'var(--bg-tertiary)';
                inspectorTab.style.color = 'var(--text-tertiary)';
                inspectorTab.style.borderBottom = 'none';
                console.log('Set tab to inactive state');
            } else {
                // Panel is open - make tab look active
                inspectorTab.classList.add('active');
                inspectorTab.style.background = 'var(--accent-primary)';
                inspectorTab.style.color = 'white';
                inspectorTab.style.borderBottom = '2px solid var(--accent-primary)';
                console.log('Set tab to active state');
            }
        }
    } else {
        console.error('Inspector toggle setup failed:');
        console.error('Right panel found:', !!rightPanel);
        console.error('Inspector tab found:', !!inspectorTab);
    }
}

function initializeTrackContextMenu() {
    const contextMenu = document.getElementById('contextMenu');
    const trackLabels = document.querySelectorAll('.track-label');
    let currentTrack = null;
    
    // Show context menu on right-click
    trackLabels.forEach(trackLabel => {
        trackLabel.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            currentTrack = this;
            
            // Position context menu
            contextMenu.style.left = e.clientX + 'px';
            contextMenu.style.top = e.clientY + 'px';
            contextMenu.classList.add('visible');
            
            // Hide context menu when clicking elsewhere
            setTimeout(() => {
                document.addEventListener('click', hideContextMenu);
            }, 10);
        });
    });
    
    // Handle context menu actions
    const contextMenuItems = document.querySelectorAll('.context-menu-item');
    contextMenuItems.forEach(item => {
        item.addEventListener('click', function() {
            const action = this.dataset.action;
            handleTrackAction(action, currentTrack);
            hideContextMenu();
        });
    });
    
    function hideContextMenu() {
        contextMenu.classList.remove('visible');
        document.removeEventListener('click', hideContextMenu);
    }
}

function handleTrackAction(action, track) {
    if (!track) return;
    
    const trackElement = document.querySelector(`[data-track="${track.dataset.track}"]`);
    
    switch(action) {
        case 'minimize':
            trackElement.classList.toggle('minimized');
            showKeyboardFeedback('Track Minimized');
            break;
        case 'collapse':
            trackElement.classList.toggle('collapsed');
            showKeyboardFeedback('Track Collapsed');
            break;
        case 'rename':
            startTrackRenaming(track);
            break;
        case 'color-dialogue':
            changeClipColor(trackElement, 'dialogue-clip');
            break;
        case 'color-music':
            changeClipColor(trackElement, 'soundtrack-clip');
            break;
        case 'color-foley':
            changeClipColor(trackElement, 'foley-clip');
            break;
        case 'mute':
            toggleTrackMute(track);
            break;
    }
}

function initializeTrackHeightControls() {
    const minimizeButtons = document.querySelectorAll('.track-controls .fa-arrows-alt-v');
    
    minimizeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const trackLabel = this.closest('.track-label');
            const trackElement = document.querySelector(`[data-track="${trackLabel.dataset.track}"]`);
            
            if (trackElement.classList.contains('minimized')) {
                trackElement.classList.remove('minimized');
                trackElement.classList.add('collapsed');
            } else if (trackElement.classList.contains('collapsed')) {
                trackElement.classList.remove('collapsed');
            } else {
                trackElement.classList.add('minimized');
            }
            
            showKeyboardFeedback('Track Height Changed');
        });
    });
}

function initializeTrackRenaming() {
    // Track renaming is handled in handleTrackAction
}

function startTrackRenaming(trackLabel) {
    const span = trackLabel.querySelector('span');
    const originalText = span.textContent;
    
    // Create input field
    const input = document.createElement('input');
    input.value = originalText;
    input.style.cssText = `
        background: transparent;
        border: 1px solid var(--accent-primary);
        color: var(--text-primary);
        font-size: var(--font-sm);
        font-weight: 600;
        width: 100%;
        outline: none;
        padding: 2px 4px;
        border-radius: 2px;
    `;
    
    // Replace span with input
    span.style.display = 'none';
    trackLabel.appendChild(input);
    input.focus();
    input.select();
    
    // Handle input completion
    function finishRenaming() {
        const newName = input.value.trim() || originalText;
        span.textContent = newName;
        span.style.display = 'block';
        input.remove();
        showKeyboardFeedback('Track Renamed');
    }
    
    input.addEventListener('blur', finishRenaming);
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            finishRenaming();
        } else if (e.key === 'Escape') {
            span.style.display = 'block';
            input.remove();
        }
    });
}

function initializeMediaBins() {
    const binHeaders = document.querySelectorAll('.bin-header');
    
    binHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const bin = this.parentElement;
            const content = bin.querySelector('.bin-content');
            const icon = this.querySelector('.fa-chevron-right, .fa-chevron-down');
            
            // Toggle expanded state
            bin.classList.toggle('expanded');
            content.classList.toggle('expanded');
            
            // Update icon
            if (bin.classList.contains('expanded')) {
                icon.className = 'fas fa-chevron-down';
            } else {
                icon.className = 'fas fa-chevron-right';
            }
            
            // Show feedback
            const binName = this.querySelector('span').textContent.trim();
            showKeyboardFeedback(`${binName} ${bin.classList.contains('expanded') ? 'Expanded' : 'Collapsed'}`);
        });
    });
}

function initializeWorkspacePresets() {
    const presetItems = document.querySelectorAll('.preset-item');
    const workspacePresets = document.getElementById('workspacePresets');
    
    // Show presets on Ctrl+Shift+P
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.shiftKey && e.key === 'P') {
            e.preventDefault();
            workspacePresets.classList.toggle('visible');
        }
    });
    
    // Hide presets when clicking outside
    document.addEventListener('click', function(e) {
        if (!workspacePresets.contains(e.target)) {
            workspacePresets.classList.remove('visible');
        }
    });
    
    presetItems.forEach(item => {
        item.addEventListener('click', function() {
            const preset = this.dataset.preset;
            applyWorkspacePreset(preset);
            workspacePresets.classList.remove('visible');
        });
    });
}

function applyWorkspacePreset(preset) {
    const rightPanel = document.getElementById('rightPanel');
    const leftPanel = document.querySelector('.left-panel');
    const timeline = document.querySelector('.timeline-container');
    
    // Reset all panels
    rightPanel.classList.remove('collapsed');
    leftPanel.style.width = '300px';
    timeline.style.height = '200px';
    
    // Apply preset-specific settings
    switch(preset) {
        case 'editing':
            // Standard editing layout - inspector visible
            showKeyboardFeedback('Editing Layout Applied');
            break;
        case 'color':
            // Focus on color grading - inspector visible
            rightPanel.classList.remove('collapsed');
            showKeyboardFeedback('Color Grading Layout Applied');
            break;
        case 'audio':
            // Focus on audio - minimize video tracks
            const videoTracks = document.querySelectorAll('.track.video-track');
            videoTracks.forEach(track => track.classList.add('minimized'));
            showKeyboardFeedback('Audio Mixing Layout Applied');
            break;
        case 'minimal':
            // Minimal layout - collapse inspector and minimize tracks
            rightPanel.classList.add('collapsed');
            const allTracks = document.querySelectorAll('.track');
            allTracks.forEach(track => track.classList.add('minimized'));
            showKeyboardFeedback('Minimal Layout Applied');
            break;
    }
}

function initializeClipColorCoding() {
    // This is handled by the context menu system
}

function initializeVolumeSliders() {
    const sliders = document.querySelectorAll('.slider');
    
    sliders.forEach(slider => {
        const volumeValue = slider.parentElement.querySelector('.volume-value');
        
        // Update display on input
        slider.addEventListener('input', function() {
            volumeValue.textContent = this.value + '%';
            showKeyboardFeedback(`Volume: ${this.value}%`);
        });
        
        // Add visual feedback on interaction
        slider.addEventListener('mousedown', function() {
            this.style.transform = 'scale(1.05)';
        });
        
        slider.addEventListener('mouseup', function() {
            this.style.transform = 'scale(1)';
        });
        
        slider.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
}

function changeClipColor(trackElement, colorClass) {
    const clips = trackElement.querySelectorAll('.clip');
    clips.forEach(clip => {
        // Remove existing color classes
        clip.classList.remove('dialogue-clip', 'soundtrack-clip', 'foley-clip', 'music-clip', 'graphics-clip', 'broll-clip', 'voiceover-clip', 'effects-clip');
        // Add new color class
        clip.classList.add(colorClass);
    });
    
    showKeyboardFeedback('Clip Color Changed');
}

// Lock functionality removed - no longer available in UI

function toggleTrackMute(trackLabel) {
    const muteIcon = trackLabel.querySelector('.fa-volume-mute');
    const trackElement = document.querySelector(`[data-track="${trackLabel.dataset.track}"]`);
    
    if (trackElement.classList.contains('muted')) {
        trackElement.classList.remove('muted');
        muteIcon.style.color = 'var(--text-quaternary)';
        showKeyboardFeedback('Track Unmuted');
    } else {
        trackElement.classList.add('muted');
        muteIcon.style.color = 'var(--accent-error)';
        showKeyboardFeedback('Track Muted');
    }
}

// Timeline Resize Functionality
function initializeTimelineResize() {
    const resizeSlider = document.getElementById('timelineResizeSlider');
    const trackLabels = document.querySelector('.track-labels');
    const timelineHeader = document.querySelector('.timeline-header');
    
    if (!resizeSlider || !trackLabels || !timelineHeader) return;
    
    let isResizing = false;
    let startX = 0;
    let startWidth = 0;
    
    resizeSlider.addEventListener('mousedown', function(e) {
        isResizing = true;
        startX = e.clientX;
        startWidth = trackLabels.offsetWidth;
        
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', function(e) {
        if (!isResizing) return;
        
        const deltaX = e.clientX - startX;
        const newWidth = Math.max(80, Math.min(300, startWidth + deltaX));
        
        trackLabels.style.width = newWidth + 'px';
        
        // Update timeline header padding to match
        timelineHeader.style.paddingLeft = newWidth + 'px';
    });
    
    document.addEventListener('mouseup', function() {
        if (isResizing) {
            isResizing = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            
            // Save the width to localStorage for persistence
            localStorage.setItem('timelineLabelsWidth', trackLabels.offsetWidth);
        }
    });
    
    // Load saved width on page load
    const savedWidth = localStorage.getItem('timelineLabelsWidth');
    if (savedWidth) {
        const width = parseInt(savedWidth);
        if (width >= 80 && width <= 300) {
            trackLabels.style.width = width + 'px';
            timelineHeader.style.paddingLeft = width + 'px';
        }
    }
}

// Add CSS for enhanced animations
const style = document.createElement('style');
style.textContent = `
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: scale(0);
        animation: ripple-animation 0.6s linear;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    @keyframes fadeInOut {
        0% { opacity: 0; transform: translateY(-10px); }
        20% { opacity: 1; transform: translateY(0); }
        80% { opacity: 1; transform: translateY(0); }
        100% { opacity: 0; transform: translateY(-10px); }
    }
    
    .property-group.expanded .property-content {
        display: block !important;
    }
    
    .toolbox-category.expanded .category-items {
        display: block !important;
    }
    
    .media-item.selected {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 1px var(--accent-primary), var(--shadow-medium) !important;
    }
    
    .clip.selected {
        border-color: var(--accent-error) !important;
        box-shadow: 0 0 0 1px var(--accent-error), var(--shadow-medium) !important;
    }
    
    .toolbox-item.selected {
        background: var(--accent-primary) !important;
        color: var(--text-inverse) !important;
    }
    
    .folder-item.active {
        background: var(--accent-primary) !important;
        color: var(--text-inverse) !important;
    }
    
    .tab.active {
        background: var(--bg-elevated) !important;
        color: var(--accent-primary) !important;
    }
    
    .inspector-tab.active {
        color: var(--accent-primary) !important;
        border-bottom-color: var(--accent-primary) !important;
    }
    
    .nav-module.active {
        color: var(--accent-primary) !important;
        background: var(--bg-elevated) !important;
    }
    
    /* Smooth transitions for all interactive elements */
    button, .tab, .media-item, .clip, .folder-item, .toolbox-item, .property-header, .category-header {
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Enhanced focus states */
    button:focus-visible, .tab:focus-visible, .media-item:focus-visible, .clip:focus-visible {
        outline: 2px solid var(--accent-primary);
        outline-offset: 2px;
    }
`;
document.head.appendChild(style);

// Initialize timeline scrolling with natural trackpad behavior
function initializeTimelineScrolling() {
    const timelineScrollContainer = document.querySelector('.timeline-scroll-container');
    const trackLabels = document.querySelector('.track-labels');
    const timelineTracks = document.querySelector('.timeline-tracks');
    
    if (!timelineScrollContainer || !trackLabels || !timelineTracks) {
        console.error('Timeline scroll elements not found');
        return;
    }
    
    console.log('Initializing timeline scrolling...');
    
    // Variables for smooth scrolling
    let isScrolling = false;
    let scrollVelocity = 0;
    let lastScrollTime = 0;
    let animationFrame = null;
    
    // Smooth scroll function with momentum
    function smoothScrollTo(targetScrollTop) {
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
        }
        
        const startScrollTop = timelineScrollContainer.scrollTop;
        const distance = targetScrollTop - startScrollTop;
        const duration = 150; // ms
        const startTime = performance.now();
        
        function animate(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function for smooth deceleration
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const currentScrollTop = startScrollTop + (distance * easeOut);
            
            timelineScrollContainer.scrollTop = currentScrollTop;
            
            if (progress < 1) {
                animationFrame = requestAnimationFrame(animate);
            } else {
                animationFrame = null;
            }
        }
        
        animationFrame = requestAnimationFrame(animate);
    }
    
    // Enhanced wheel event handler for trackpad
    function handleWheel(e) {
        // Prevent default scrolling behavior
        e.preventDefault();
        e.stopPropagation();
        
        const currentTime = performance.now();
        const timeDelta = currentTime - lastScrollTime;
        
        // Calculate scroll amount based on delta mode
        let scrollAmount;
        if (e.deltaMode === 0) {
            // DOM_DELTA_PIXEL - trackpad (most common)
            scrollAmount = e.deltaY * 1.2; // Increased sensitivity
        } else if (e.deltaMode === 1) {
            // DOM_DELTA_LINE - mouse wheel
            scrollAmount = e.deltaY * 20;
        } else {
            // DOM_DELTA_PAGE - page scroll
            scrollAmount = e.deltaY * 100;
        }
        
        // Apply momentum for natural feel
        if (timeDelta < 16) { // 60fps
            scrollVelocity = scrollVelocity * 0.7 + scrollAmount * 0.3;
        } else {
            scrollVelocity = scrollAmount;
        }
        
        // Calculate new scroll position
        const currentScrollTop = timelineScrollContainer.scrollTop;
        const newScrollTop = currentScrollTop + scrollVelocity;
        const maxScroll = timelineScrollContainer.scrollHeight - timelineScrollContainer.clientHeight;
        
        // Clamp scroll position
        const clampedScrollTop = Math.max(0, Math.min(newScrollTop, maxScroll));
        
        // Apply scroll with momentum
        if (Math.abs(scrollVelocity) > 0.5) {
            timelineScrollContainer.scrollTop = clampedScrollTop;
        }
        
        lastScrollTime = currentTime;
        
        // Reset scroll velocity over time
        if (!isScrolling) {
            isScrolling = true;
            setTimeout(() => {
                scrollVelocity = 0;
                isScrolling = false;
            }, 100);
        }
    }
    
    // Add single, optimized event listener
    timelineScrollContainer.addEventListener('wheel', handleWheel, { passive: false });
    
    // Also listen on timeline tracks for better coverage
    timelineTracks.addEventListener('wheel', handleWheel, { passive: false });
    
    // Force enable scrolling
    timelineScrollContainer.style.overflowY = 'auto';
    timelineScrollContainer.style.height = '200px';
    timelineScrollContainer.style.scrollBehavior = 'auto'; // Disable CSS smooth scroll
    
    // Remove visual indicator
    timelineScrollContainer.style.border = 'none';
    
    console.log('Timeline scrolling initialized successfully');
}

// Video Editor Initialization
function initializeVideoEditor() {
    setupFileUpload();
    setupVideoControls();
    setupEffectsPanel();
    setupAudioPanel();
    setupExportPanel();
    loadExistingFiles();
}

// File Upload Setup
function setupFileUpload() {
    const dropZone = document.createElement('div');
    dropZone.className = 'drop-zone';
    dropZone.innerHTML = `
        <div class="drop-zone-content">
            <i class="fas fa-cloud-upload-alt"></i>
            <h3>Drop video files here or click to browse</h3>
            <p>Supports MP4, MOV, AVI, MKV</p>
            <input type="file" id="file-input" accept="video/*,audio/*,.srt" multiple style="display: none;">
            <button class="upload-btn">Browse Files</button>
        </div>
    `;
    
    const mediaPool = document.querySelector('.folder-tree');
    if (mediaPool) {
        mediaPool.appendChild(dropZone);
    }
    
    const fileInput = document.getElementById('file-input');
    const uploadBtn = dropZone.querySelector('.upload-btn');
    
    uploadBtn.addEventListener('click', () => fileInput.click());
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        handleFiles(e.dataTransfer.files);
    });
    
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
}

// Handle File Upload
async function handleFiles(files) {
    for (const file of files) {
        await uploadFile(file);
    }
    updateMediaPool();
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    showProgress(`Uploading ${file.name}...`);
    
    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Upload failed');
        
        const result = await response.json();
        uploadedFiles.set(result.file_id, {
            ...result,
            type: file.type.startsWith('video/') ? 'video' : 
                  file.type.startsWith('audio/') ? 'audio' : 'subtitle'
        });
        
        showSuccess(`${file.name} uploaded successfully`);
        return result.file_id;
    } catch (error) {
        showError(`Failed to upload ${file.name}: ${error.message}`);
    }
}

// Load Existing Files
async function loadExistingFiles() {
    try {
        const response = await fetch(`${API_BASE}/files`);
        const data = await response.json();
        
        for (const file of data.files) {
            uploadedFiles.set(file.file_id, file);
        }
        updateMediaPool();
    } catch (error) {
        console.error('Failed to load files:', error);
    }
}

// Update Media Pool Display
function updateMediaPool() {
    const mediaPool = document.querySelector('.folder-tree');
    const existingFiles = mediaPool.querySelectorAll('.media-file');
    existingFiles.forEach(file => file.remove());
    
    uploadedFiles.forEach((file, fileId) => {
        const fileElement = document.createElement('div');
        fileElement.className = 'media-file';
        fileElement.innerHTML = `
            <div class="file-item" data-file-id="${fileId}">
                <i class="fas ${getFileIcon(file.type)}"></i>
                <span class="file-name">${file.filename}</span>
                <div class="file-actions">
                    <button class="btn-preview" title="Preview">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="btn-delete" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
        
        mediaPool.appendChild(fileElement);
        
        fileElement.querySelector('.btn-preview').addEventListener('click', () => previewFile(fileId));
        fileElement.querySelector('.btn-delete').addEventListener('click', () => deleteFile(fileId));
        fileElement.addEventListener('click', () => selectFile(fileId));
    });
}

function getFileIcon(type) {
    switch(type) {
        case 'video': return 'fa-video';
        case 'audio': return 'fa-music';
        case 'subtitle': return 'fa-closed-captioning';
        default: return 'fa-file';
    }
}

// File Operations
async function selectFile(fileId) {
    currentVideoId = fileId;
    document.querySelectorAll('.file-item').forEach(item => item.classList.remove('selected'));
    document.querySelector(`[data-file-id="${fileId}"]`).classList.add('selected');
    
    const file = uploadedFiles.get(fileId);
    if (file.type === 'video') {
        await loadVideoInfo(fileId);
        updateVideoPlayer(fileId);
    }
}

async function loadVideoInfo(fileId) {
    try {
        const response = await fetch(`${API_BASE}/info/${fileId}`);
        const data = await response.json();
        
        updateInspectorPanel(data.info);
    } catch (error) {
        console.error('Failed to load video info:', error);
    }
}

function updateVideoPlayer(fileId) {
    const videoFrame = document.querySelector('.video-frame');
    if (videoFrame) {
        videoFrame.innerHTML = `
            <video controls class="video-player" src="${API_BASE}/preview/${fileId}">
                Your browser does not support the video tag.
            </video>
        `;
    }
}

async function previewFile(fileId) {
    window.open(`${API_BASE}/preview/${fileId}`, '_blank');
}

async function deleteFile(fileId) {
    if (!confirm('Are you sure you want to delete this file?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/files/${fileId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            uploadedFiles.delete(fileId);
            updateMediaPool();
            showSuccess('File deleted successfully');
        } else {
            throw new Error('Delete failed');
        }
    } catch (error) {
        showError(`Failed to delete file: ${error.message}`);
    }
}

// Video Controls Setup
function setupVideoControls() {
    const trimSection = document.createElement('div');
    trimSection.className = 'control-section';
    trimSection.innerHTML = `
        <h4>Trim Video</h4>
        <div class="control-group">
            <label>Start Time:</label>
            <input type="text" id="trim-start" placeholder="00:00:00" pattern="[0-9]{2}:[0-9]{2}:[0-9]{2}">
        </div>
        <div class="control-group">
            <label>End Time:</label>
            <input type="text" id="trim-end" placeholder="00:10:00" pattern="[0-9]{2}:[0-9]{2}:[0-9]{2}">
        </div>
        <button class="action-btn" onclick="trimVideo()">
            <i class="fas fa-cut"></i> Trim Video
        </button>
    `;
    
    addToInspector(trimSection);
    
    const spliceSection = document.createElement('div');
    spliceSection.className = 'control-section';
    spliceSection.innerHTML = `
        <h4>Remove Section</h4>
        <div class="control-group">
            <label>Remove Start:</label>
            <input type="text" id="splice-start" placeholder="00:01:00" pattern="[0-9]{2}:[0-9]{2}:[0-9]{2}">
        </div>
        <div class="control-group">
            <label>Remove End:</label>
            <input type="text" id="splice-end" placeholder="00:02:00" pattern="[0-9]{2}:[0-9]{2}:[0-9]{2}">
        </div>
        <button class="action-btn" onclick="spliceVideo()">
            <i class="fas fa-scissors"></i> Remove Section
        </button>
    `;
    
    addToInspector(spliceSection);
}

// Effects Panel Setup
function setupEffectsPanel() {
    const effectsSection = document.createElement('div');
    effectsSection.className = 'control-section';
    effectsSection.innerHTML = `
        <h4>Video Effects</h4>
        <div class="effects-grid">
            <div class="effect-control">
                <label>Blur:</label>
                <input type="range" id="blur" min="0" max="10" step="0.1" value="0">
                <span id="blur-value">0</span>
            </div>
            <div class="effect-control">
                <label>Brightness:</label>
                <input type="range" id="brightness" min="-1" max="1" step="0.1" value="0">
                <span id="brightness-value">0</span>
            </div>
            <div class="effect-control">
                <label>Contrast:</label>
                <input type="range" id="contrast" min="0" max="2" step="0.1" value="1">
                <span id="contrast-value">1</span>
            </div>
            <div class="effect-control">
                <label>Saturation:</label>
                <input type="range" id="saturation" min="0" max="2" step="0.1" value="1">
                <span id="saturation-value">1</span>
            </div>
            <div class="effect-control">
                <label>Rotation:</label>
                <input type="range" id="rotation" min="-180" max="180" step="1" value="0">
                <span id="rotation-value">0°</span>
            </div>
        </div>
        <div class="effect-checkboxes">
            <label><input type="checkbox" id="zoom"> Zoom Effect</label>
            <label><input type="checkbox" id="h-flip"> Horizontal Flip</label>
            <label><input type="checkbox" id="v-flip"> Vertical Flip</label>
        </div>
        <div class="effect-filters">
            <label>Artistic Filter:</label>
            <select id="artistic-filter">
                <option value="none">None</option>
                <option value="black & white">Black & White</option>
                <option value="sepia">Sepia</option>
                <option value="vintage">Vintage</option>
                <option value="negative">Negative</option>
                <option value="emboss">Emboss</option>
                <option value="edge detection">Edge Detection</option>
            </select>
        </div>
        <button class="action-btn" onclick="applyEffects()">
            <i class="fas fa-magic"></i> Apply Effects
        </button>
    `;
    
    addToInspector(effectsSection);
    
    const sliders = effectsSection.querySelectorAll('input[type="range"]');
    sliders.forEach(slider => {
        slider.addEventListener('input', function() {
            const valueSpan = document.getElementById(`${this.id}-value`);
            if (valueSpan) {
                valueSpan.textContent = this.id === 'rotation' ? `${this.value}°` : this.value;
            }
        });
    });
}

// Audio Panel Setup
function setupAudioPanel() {
    const audioSection = document.createElement('div');
    audioSection.className = 'control-section';
    audioSection.innerHTML = `
        <h4>Audio Controls</h4>
        <div class="audio-controls">
            <button class="action-btn" onclick="extractAudio()">
                <i class="fas fa-volume-up"></i> Extract Audio
            </button>
            <div class="control-group">
                <label>Background Music:</label>
                <select id="bg-music-file">
                    <option value="">Select audio file...</option>
                </select>
                <div class="audio-options">
                    <label>Volume: <input type="range" id="bg-volume" min="0" max="2" step="0.1" value="0.5"></label>
                    <label><input type="checkbox" id="mix-audio" checked> Mix with original</label>
                </div>
                <button class="action-btn" onclick="addBackgroundMusic()">
                    <i class="fas fa-music"></i> Add Background Music
                </button>
            </div>
            <div class="control-group">
                <label>Sound Effect:</label>
                <select id="sound-effect-file">
                    <option value="">Select audio file...</option>
                </select>
                <div class="audio-options">
                    <label>Start Time (s): <input type="number" id="effect-start" value="0" step="0.1"></label>
                    <label>Duration (s): <input type="number" id="effect-duration" step="0.1"></label>
                    <label>Volume: <input type="range" id="effect-volume" min="0" max="2" step="0.1" value="1"></label>
                </div>
                <button class="action-btn" onclick="addSoundEffect()">
                    <i class="fas fa-bell"></i> Add Sound Effect
                </button>
            </div>
            <div class="control-group">
                <label>Subtitles:</label>
                <select id="subtitle-file">
                    <option value="">Select subtitle file...</option>
                </select>
                <div class="subtitle-options">
                    <label><input type="checkbox" id="burn-subtitles"> Burn into video</label>
                    <label><input type="checkbox" id="auto-transcribe"> Auto-transcribe</label>
                </div>
                <button class="action-btn" onclick="addSubtitles()">
                    <i class="fas fa-closed-captioning"></i> Add Subtitles
                </button>
            </div>
        </div>
    `;
    
    addToInspector(audioSection);
    updateAudioFileSelects();
}

// Export Panel Setup
function setupExportPanel() {
    const exportSection = document.createElement('div');
    exportSection.className = 'control-section';
    exportSection.innerHTML = `
        <h4>Export Options</h4>
        <div class="export-controls">
            <div class="control-group">
                <label>Video Codec:</label>
                <select id="video-codec">
                    <option value="libx264">H.264</option>
                    <option value="libx265">H.265</option>
                    <option value="libvpx-vp9">VP9</option>
                </select>
            </div>
            <div class="control-group">
                <label>Audio Codec:</label>
                <select id="audio-codec">
                    <option value="aac">AAC</option>
                    <option value="mp3">MP3</option>
                    <option value="opus">Opus</option>
                </select>
            </div>
            <div class="control-group">
                <label>Quality (CRF):</label>
                <input type="range" id="quality" min="0" max="51" value="23">
                <span id="quality-value">23</span>
            </div>
            <button class="action-btn" onclick="convertVideo()">
                <i class="fas fa-download"></i> Convert & Download
            </button>
            <div class="gif-controls">
                <h5>Create GIF</h5>
                <div class="gif-options">
                    <label>Start: <input type="text" id="gif-start" placeholder="00:00:00"></label>
                    <label>Duration: <input type="text" id="gif-duration" placeholder="00:00:10"></label>
                    <label>Width: <input type="number" id="gif-width" value="320"></label>
                    <label>Height: <input type="number" id="gif-height" value="240"></label>
                </div>
                <button class="action-btn" onclick="createGif()">
                    <i class="fas fa-image"></i> Create GIF
                </button>
            </div>
        </div>
    `;
    
    addToInspector(exportSection);
    
    document.getElementById('quality').addEventListener('input', function() {
        document.getElementById('quality-value').textContent = this.value;
    });
}

function addToInspector(section) {
    const inspector = document.querySelector('.inspector-content');
    if (inspector) {
        inspector.appendChild(section);
    }
}

function updateAudioFileSelects() {
    const selects = ['bg-music-file', 'sound-effect-file', 'subtitle-file'];
    
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }
        
        uploadedFiles.forEach((file, fileId) => {
            if ((selectId.includes('music') || selectId.includes('effect')) && file.type === 'audio') {
                const option = document.createElement('option');
                option.value = fileId;
                option.textContent = file.filename;
                select.appendChild(option);
            } else if (selectId.includes('subtitle') && file.type === 'subtitle') {
                const option = document.createElement('option');
                option.value = fileId;
                option.textContent = file.filename;
                select.appendChild(option);
            }
        });
    });
}

// Video Processing Functions
async function trimVideo() {
    if (!currentVideoId) {
        showError('Please select a video file first');
        return;
    }
    
    const startTime = document.getElementById('trim-start').value || '00:00:00';
    const endTime = document.getElementById('trim-end').value;
    
    if (!endTime) {
        showError('Please specify end time');
        return;
    }
    
    showProgress('Trimming video...');
    
    try {
        const response = await fetch(`${API_BASE}/trim`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                video_id: currentVideoId,
                start_time: startTime,
                end_time: endTime
            })
        });
        
        if (!response.ok) throw new Error('Trim failed');
        
        const result = await response.json();
        showSuccess('Video trimmed successfully');
        offerDownload(result.output_id, 'trimmed');
    } catch (error) {
        showError(`Trim failed: ${error.message}`);
    }
}

async function spliceVideo() {
    if (!currentVideoId) {
        showError('Please select a video file first');
        return;
    }
    
    const removeStart = document.getElementById('splice-start').value;
    const removeEnd = document.getElementById('splice-end').value;
    
    if (!removeStart || !removeEnd) {
        showError('Please specify start and end times for removal');
        return;
    }
    
    showProgress('Removing section from video...');
    
    try {
        const formData = new FormData();
        formData.append('video_id', currentVideoId);
        formData.append('remove_start_time', removeStart);
        formData.append('remove_end_time', removeEnd);
        
        const response = await fetch(`${API_BASE}/splice`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Splice failed');
        
        const result = await response.json();
        showSuccess('Section removed successfully');
        offerDownload(result.output_id, 'spliced');
    } catch (error) {
        showError(`Splice failed: ${error.message}`);
    }
}

async function applyEffects() {
    if (!currentVideoId) {
        showError('Please select a video file first');
        return;
    }
    
    const effects = {
        video_id: currentVideoId,
        blur: parseFloat(document.getElementById('blur').value),
        brightness: parseFloat(document.getElementById('brightness').value),
        contrast: parseFloat(document.getElementById('contrast').value),
        saturation: parseFloat(document.getElementById('saturation').value),
        rotation: parseFloat(document.getElementById('rotation').value),
        zoom: document.getElementById('zoom').checked,
        horizontal_flip: document.getElementById('h-flip').checked,
        vertical_flip: document.getElementById('v-flip').checked,
        artistic_filter: document.getElementById('artistic-filter').value
    };
    
    showProgress('Applying effects...');
    
    try {
        const response = await fetch(`${API_BASE}/effects`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(effects)
        });
        
        if (!response.ok) throw new Error('Effects failed');
        
        const result = await response.json();
        showSuccess('Effects applied successfully');
        offerDownload(result.output_id, 'effects');
    } catch (error) {
        showError(`Effects failed: ${error.message}`);
    }
}

async function extractAudio() {
    if (!currentVideoId) {
        showError('Please select a video file first');
        return;
    }
    
    showProgress('Extracting audio...');
    
    try {
        const formData = new FormData();
        formData.append('video_id', currentVideoId);
        formData.append('audio_codec', 'mp3');
        formData.append('bitrate', '192k');
        
        const response = await fetch(`${API_BASE}/audio/extract`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Audio extraction failed');
        
        const result = await response.json();
        showSuccess('Audio extracted successfully');
        offerDownload(result.output_id, 'audio');
    } catch (error) {
        showError(`Audio extraction failed: ${error.message}`);
    }
}

async function addBackgroundMusic() {
    if (!currentVideoId) {
        showError('Please select a video file first');
        return;
    }
    
    const audioFileId = document.getElementById('bg-music-file').value;
    if (!audioFileId) {
        showError('Please select an audio file');
        return;
    }
    
    const volume = parseFloat(document.getElementById('bg-volume').value);
    const mix = document.getElementById('mix-audio').checked;
    
    showProgress('Adding background music...');
    
    try {
        const response = await fetch(`${API_BASE}/audio/background`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                video_id: currentVideoId,
                audio_file_id: audioFileId,
                volume: volume,
                mix: mix
            })
        });
        
        if (!response.ok) throw new Error('Background music failed');
        
        const result = await response.json();
        showSuccess('Background music added successfully');
        offerDownload(result.output_id, 'music');
    } catch (error) {
        showError(`Background music failed: ${error.message}`);
    }
}

async function addSoundEffect() {
    if (!currentVideoId) {
        showError('Please select a video file first');
        return;
    }
    
    const audioFileId = document.getElementById('sound-effect-file').value;
    if (!audioFileId) {
        showError('Please select an audio file');
        return;
    }
    
    const startTime = parseFloat(document.getElementById('effect-start').value);
    const duration = document.getElementById('effect-duration').value ? 
                    parseFloat(document.getElementById('effect-duration').value) : null;
    const volume = parseFloat(document.getElementById('effect-volume').value);
    
    showProgress('Adding sound effect...');
    
    try {
        const response = await fetch(`${API_BASE}/audio/effect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                video_id: currentVideoId,
                audio_file_id: audioFileId,
                start_time: startTime,
                duration: duration,
                volume: volume,
                mix: true
            })
        });
        
        if (!response.ok) throw new Error('Sound effect failed');
        
        const result = await response.json();
        showSuccess('Sound effect added successfully');
        offerDownload(result.output_id, 'effect');
    } catch (error) {
        showError(`Sound effect failed: ${error.message}`);
    }
}

async function addSubtitles() {
    if (!currentVideoId) {
        showError('Please select a video file first');
        return;
    }
    
    const autoTranscribe = document.getElementById('auto-transcribe').checked;
    const burn = document.getElementById('burn-subtitles').checked;
    
    let subtitleFileId = null;
    if (!autoTranscribe) {
        subtitleFileId = document.getElementById('subtitle-file').value;
        if (!subtitleFileId) {
            showError('Please select a subtitle file or enable auto-transcribe');
            return;
        }
    }
    
    showProgress(autoTranscribe ? 'Transcribing audio...' : 'Adding subtitles...');
    
    try {
        const response = await fetch(`${API_BASE}/subtitles`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                video_id: currentVideoId,
                subtitle_file_id: subtitleFileId,
                burn: burn,
                auto_transcribe: autoTranscribe,
                language: 'en-US'
            })
        });
        
        if (!response.ok) throw new Error('Subtitles failed');
        
        const result = await response.json();
        showSuccess('Subtitles added successfully');
        offerDownload(result.output_id, 'subtitles');
    } catch (error) {
        showError(`Subtitles failed: ${error.message}`);
    }
}

async function convertVideo() {
    if (!currentVideoId) {
        showError('Please select a video file first');
        return;
    }
    
    const videoCodec = document.getElementById('video-codec').value;
    const audioCodec = document.getElementById('audio-codec').value;
    const quality = document.getElementById('quality').value;
    
    showProgress('Converting video...');
    
    try {
        const formData = new FormData();
        formData.append('video_id', currentVideoId);
        formData.append('video_codec', videoCodec);
        formData.append('audio_codec', audioCodec);
        formData.append('quality', quality);
        
        const response = await fetch(`${API_BASE}/convert`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Conversion failed');
        
        const result = await response.json();
        showSuccess('Video converted successfully');
        offerDownload(result.output_id, 'converted');
    } catch (error) {
        showError(`Conversion failed: ${error.message}`);
    }
}

async function createGif() {
    if (!currentVideoId) {
        showError('Please select a video file first');
        return;
    }
    
    const startTime = document.getElementById('gif-start').value || '00:00:00';
    const duration = document.getElementById('gif-duration').value || '00:00:10';
    const width = parseInt(document.getElementById('gif-width').value);
    const height = parseInt(document.getElementById('gif-height').value);
    
    showProgress('Creating GIF...');
    
    try {
        const formData = new FormData();
        formData.append('video_id', currentVideoId);
        formData.append('start_time', startTime);
        formData.append('duration', duration);
        formData.append('width', width);
        formData.append('height', height);
        
        const response = await fetch(`${API_BASE}/gif`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('GIF creation failed');
        
        const result = await response.json();
        showSuccess('GIF created successfully');
        offerDownload(result.output_id, 'gif');
    } catch (error) {
        showError(`GIF creation failed: ${error.message}`);
    }
}

// Utility Functions
function offerDownload(outputId, type) {
    const downloadBtn = document.createElement('button');
    downloadBtn.className = 'download-btn';
    downloadBtn.innerHTML = `<i class="fas fa-download"></i> Download ${type}`;
    downloadBtn.onclick = () => window.open(`${API_BASE}/download/${outputId}`, '_blank');
    
    const existingBtn = document.querySelector('.download-btn');
    if (existingBtn) existingBtn.remove();
    
    document.querySelector('.inspector-content').appendChild(downloadBtn);
}

function showProgress(message) {
    const notification = createNotification(message, 'progress');
    showNotification(notification);
}

function showSuccess(message) {
    const notification = createNotification(message, 'success');
    showNotification(notification);
}

function showError(message) {
    const notification = createNotification(message, 'error');
    showNotification(notification);
}

function createNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check' : type === 'error' ? 'fa-times' : 'fa-spinner fa-spin'}"></i>
        <span>${message}</span>
    `;
    return notification;
}

function showNotification(notification) {
    let container = document.querySelector('.notifications');
    if (!container) {
        container = document.createElement('div');
        container.className = 'notifications';
        document.body.appendChild(container);
    }
    
    container.appendChild(notification);
    
    if (!notification.classList.contains('progress')) {
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

function updateInspectorPanel(mediaInfo) {
    const inspector = document.querySelector('.inspector-content');
    let infoSection = inspector.querySelector('.media-info-section');
    
    if (!infoSection) {
        infoSection = document.createElement('div');
        infoSection.className = 'media-info-section control-section';
        inspector.insertBefore(infoSection, inspector.firstChild);
    }
    
    if (mediaInfo) {
        const format = mediaInfo.format;
        const videoStream = mediaInfo.streams.find(s => s.codec_type === 'video');
        const audioStream = mediaInfo.streams.find(s => s.codec_type === 'audio');
        
        infoSection.innerHTML = `
            <h4>Media Information</h4>
            <div class="info-grid">
                <div class="info-item">
                    <label>Duration:</label>
                    <span>${formatDuration(parseFloat(format.duration))}</span>
                </div>
                ${videoStream ? `
                    <div class="info-item">
                        <label>Resolution:</label>
                        <span>${videoStream.width}x${videoStream.height}</span>
                    </div>
                    <div class="info-item">
                        <label>Frame Rate:</label>
                        <span>${eval(videoStream.r_frame_rate).toFixed(2)} fps</span>
                    </div>
                    <div class="info-item">
                        <label>Video Codec:</label>
                        <span>${videoStream.codec_name}</span>
                    </div>
                ` : ''}
                ${audioStream ? `
                    <div class="info-item">
                        <label>Audio Codec:</label>
                        <span>${audioStream.codec_name}</span>
                    </div>
                    <div class="info-item">
                        <label>Sample Rate:</label>
                        <span>${audioStream.sample_rate} Hz</span>
                    </div>
                ` : ''}
                <div class="info-item">
                    <label>File Size:</label>
                    <span>${formatBytes(parseInt(format.size))}</span>
                </div>
            </div>
        `;
    }
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}