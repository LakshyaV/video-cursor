# DaVinci Resolve UI Replica

A modern, pixel-perfect UI replica of DaVinci Resolve Studio 20's video editing interface built with Node.js, HTML5, CSS3, and JavaScript.

## Features

### 🎬 Professional Video Editor Interface
- **Media Pool**: Grid-based thumbnail view with video/audio file previews
- **Video Viewer**: Central video display with custom animated scene
- **Timeline**: Multi-track editing interface with video and audio tracks
- **Audio Meters**: Real-time animated audio level indicators
- **Navigation**: Module-based navigation (Media, Cut, Edit, Fusion, Color, Fairlight, Deliver)

### 🎨 Modern Design
- **Dark Theme**: Professional dark interface matching DaVinci Resolve
- **Responsive Layout**: Adapts to different screen sizes
- **Smooth Animations**: Hover effects, transitions, and interactive feedback
- **Pixel-Perfect Details**: Attention to every visual detail from the original

### ⚡ Interactive Features
- **Playback Controls**: Play, pause, stop functionality
- **Timeline Interaction**: Click to scrub, drag clips
- **Media Selection**: Click to select media items and clips
- **Keyboard Shortcuts**: Space (play/pause), K (pause), J (stop)
- **Module Navigation**: Switch between different editing modules

## Installation

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd davinci-resolve-ui
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm start
   ```

4. **Open your browser**
   Navigate to `http://localhost:3000`

## Project Structure

```
davinci-resolve-ui/
├── public/
│   ├── index.html          # Main HTML structure
│   ├── styles.css          # Complete CSS styling
│   └── script.js           # Interactive JavaScript
├── package.json            # Node.js dependencies
├── server.js              # Express server
└── README.md              # This file
```

## Technical Details

### Frontend Technologies
- **HTML5**: Semantic structure with accessibility features
- **CSS3**: Modern styling with Flexbox, Grid, and animations
- **JavaScript (ES6+)**: Interactive functionality and event handling
- **Font Awesome**: Professional icons

### Backend
- **Node.js**: Runtime environment
- **Express.js**: Web server framework
- **Static File Serving**: Efficient asset delivery

### Key Features Implemented

#### Media Pool
- Grid layout with video thumbnails
- Hover effects and selection states
- File information display (name, duration)
- Play/music icons for different media types

#### Video Viewer
- Custom animated scene (red car on landscape)
- Professional video frame styling
- Audio level meters with real-time animation
- Playhead indicator

#### Timeline
- Multiple video tracks (V1, V2, V3, V4, V8)
- Audio tracks with waveform visualization
- Color-coded clips (blue, green, purple, pink)
- Title clip with special styling
- Interactive playhead and clip dragging

#### Navigation
- Module-based navigation bar
- Active state management
- Professional branding

## Customization

### Colors
The interface uses a carefully crafted color palette:
- **Primary**: #4a9eff (Blue)
- **Background**: #1a1a1a (Dark)
- **Secondary**: #2a2a2a (Medium Dark)
- **Accent**: #ff6b35 (Orange for audio)

### Layout
- Fully responsive design
- Flexible grid system
- Professional spacing and typography

## Browser Support

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Future Enhancements

This UI is designed to be a foundation for actual video editing functionality:
- Real video file loading and playback
- Timeline scrubbing and editing
- Audio waveform generation
- Project management
- Export functionality

## License

MIT License - Feel free to use this project for learning and development purposes.

## Credits

Inspired by DaVinci Resolve Studio 20's professional interface design.
