# 🎴 Flashcards Study App

A comprehensive flashcards application built with Streamlit for effective learning with spaced repetition. Designed for both local use and cloud deployment (Streamlit Cloud compatible).

## ✨ Key Features

### 📚 Study Mode
- Study active or archived flashcards
- Track correct/wrong answers per card
- View consecutive correct streak
- Cards automatically archive after 5 consecutive correct answers
- **Enhanced Navigation**:
  - Next/Previous buttons for easy card navigation
  - Jump to any question via dropdown selector
  - Progress indicator showing current position

### ➕ Create Flashcards
- Add new flashcards with questions
- Include text answers
- Upload images as answers (supports PNG, JPG, JPEG, GIF)
- Combine text and image answers

### ✏️ Edit Flashcards
- Modify existing flashcard questions
- Update answer text
- Replace or remove answer images
- Preserve statistics when editing

### 🗑️ Delete Flashcards
- Remove unwanted flashcards
- Preview before deletion
- Automatically cleans up associated image files

### 📦 Manage Archived Cards
- View all archived flashcards
- Reset individual archived cards
- Reset all archived cards at once
- Cards reset with streak counter cleared

### 📊 Statistics Dashboard
- View total cards (active/archived)
- Track overall accuracy percentage
- See detailed per-card statistics
- Monitor learning progress

### 💾 Backup & Restore
- **Download backups**: Export your progress as JSON files
- **Upload backups**: Restore your data from any device
- **Cloud-friendly**: Perfect for Streamlit Cloud deployment
- **Portable**: Sync across multiple devices
- **Complete data**: Images embedded as base64 in backups

## Installation

1. Install required packages:
```bash
pip install -r flashcards_requirements.txt
```

Or install individually:
```bash
pip install streamlit pandas
```

## Usage

1. Run the app:
```bash
streamlit run flashcards_app.py
```

2. The app will automatically import your `ppl_flashcards.csv` on first run

3. Navigate using the sidebar menu:
   - **Study**: Review flashcards
   - **Create**: Add new cards
   - **Edit**: Modify existing cards
   - **Delete**: Remove cards
   - **Archived**: Manage archived cards
   - **Statistics**: View your progress

## Data Storage

- **flashcards_data.json**: Stores all flashcard data, statistics, and images (as base64)
- **Images**: Embedded directly in JSON using base64 encoding
- **Cloud Compatible**: No external file dependencies - everything in one JSON file
- **Portable**: Download and upload your complete progress anywhere

### For Cloud Deployment (Streamlit Cloud)

Since Streamlit Cloud has ephemeral storage, use the built-in backup system:

1. **Before closing**: Download your backup from the sidebar
2. **When reopening**: Upload your backup file to restore progress
3. **Recommended**: Keep backups in cloud storage (Google Drive, OneDrive, etc.)

### For Local Use

Data automatically persists between sessions in `flashcards_data.json`.

## How It Works

### Study Process
1. Question is displayed
2. Click "Show Answer" to reveal the answer
3. Mark your response as "Correct" or "Wrong"
4. Statistics are updated automatically
5. After 5 consecutive correct answers, card is archived

### Archival System
- Cards with 5+ consecutive correct answers are automatically archived
- Archived cards can be studied separately
- Reset archived cards to return them to active study pool
- Resetting clears the consecutive streak but preserves total statistics

## Tips for Effective Learning

- Study active cards regularly
- Be honest with yourself when marking answers
- Review archived cards periodically
- Reset archived cards when you want to refresh your knowledge
- Use images for visual concepts or diagrams
- **For cloud deployment**: Download backups regularly to preserve progress

## Cloud Deployment

### Deploying to Streamlit Cloud

1. Push your code to GitHub
2. Connect your repository to Streamlit Cloud
3. Deploy the app
4. Use the backup/restore feature to manage your data across sessions

### Important Notes for Cloud Use

- Storage is ephemeral (resets on app restart)
- Always download backups before closing
- Upload your backup when you return
- Images are stored as base64 in JSON (no separate files needed)

## Workflow Example

### First Time Setup
1. Create your flashcards locally or in the cloud app
2. Study and build your progress
3. Download backup before closing

### Daily Use (Cloud)
1. Open the app
2. Upload your latest backup file
3. Study your flashcards
4. Download updated backup before closing
5. Store backup in your preferred cloud storage

### Daily Use (Local)
1. Run `streamlit run flashcards_app.py`
2. Study - progress saves automatically
3. Optional: Download backups for redundancy

## Initial Data

The app starts with flashcards from `ppl_flashcards.csv` (aviation/pilot training content).
You can add, edit, or delete these flashcards as needed.

## Keyboard Navigation

- Use the Previous/Next buttons to navigate
- Click "Show Answer" before marking your response
- Use the sidebar for quick statistics overview

---

**Enjoy your learning journey! 🚀**
