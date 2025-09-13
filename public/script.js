// Professional DaVinci Resolve UI - Enhanced Interactions
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the interface with enhanced interactions
    initializeInterface();
    
    // Set up event listeners with smooth animations
    setupEventListeners();
    
    // Initialize audio meters with professional animation
    initializeAudioMeters();
    
    // Initialize timeline with enhanced interactions
    initializeTimeline();
    
    // Initialize timeline resize functionality
    initializeTimelineResize();
    
    // Initialize timeline scrolling
    initializeTimelineScrolling();
    
    // Initialize inspector with smooth transitions
    initializeInspector();
    
    // Initialize toolbox with professional feel
    initializeToolbox();
    
    // Initialize micro-interactions
    initializeMicroInteractions();
    
    // Initialize keyboard shortcuts
    initializeKeyboardShortcuts();
    
    // Initialize workspace organization features
    initializeWorkspaceOrganization();
});

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