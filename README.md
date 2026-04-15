# 🎴 Flashcards Study App

A comprehensive flashcards application built with Streamlit for effective learning with spaced repetition.

## Features

### 📚 Study Mode
- Study active or archived flashcards
- Track correct/wrong answers per card
- View consecutive correct streak
- Cards automatically archive after 5 consecutive correct answers
- Navigate between cards easily

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

- **flashcards_data.json**: Stores all flashcard data and statistics
- **flashcard_images/**: Folder for uploaded images
- Data persists between sessions

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

## Initial Data

The app starts with flashcards from `ppl_flashcards.csv` (aviation/pilot training content).
You can add, edit, or delete these flashcards as needed.

## Keyboard Navigation

- Use the Previous/Next buttons to navigate
- Click "Show Answer" before marking your response
- Use the sidebar for quick statistics overview

---

**Enjoy your learning journey! 🚀**
