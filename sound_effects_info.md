# Sound Effects Setup

## How to Add Sound Effects

To use sound effects in your video editing system, you need to add sound effect files to your project directory.

### Current Sound Effect:
- **boom_effect.mp3** - Boom/explosion sound effect

### How to Add Your Own Sound Effects:

1. **Find or create sound effect files**:
   - Download from free sound libraries (freesound.org, zapsplat.com)
   - Create your own using audio editing software
   - Use AI-generated sound effects

2. **Supported formats**:
   - `.mp3` (recommended)
   - `.wav`
   - `.aac`
   - `.m4a`

3. **Add to project**:
   - Place sound effect files in the same directory as your Python scripts
   - Name them descriptively (e.g., `boom_effect.mp3`, `gunshot.mp3`, `swoosh.mp3`)

4. **Usage examples**:
   - "add boom effect when the explosion happens"
   - "add sound effect to the gunshot"
   - "boom effect at the climax"

### File Structure:
```
video-cursor/
├── specific.py
├── utils.py
├── boom_effect.mp3          # ← Add your sound effects here
├── gunshot_effect.mp3       # ← Example additional effect
├── swoosh_effect.mp3        # ← Example additional effect
└── ...
```

### Note:
The system currently looks for `boom_effect.mp3` by default. To use other sound effects, you'll need to modify the code to detect which sound effect to use based on the command.
