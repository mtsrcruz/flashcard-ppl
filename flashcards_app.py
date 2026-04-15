import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path
import base64

# File paths
FLASHCARDS_JSON = "flashcards_data.json"
IMAGES_FOLDER = "flashcard_images"

# Ensure images folder exists
Path(IMAGES_FOLDER).mkdir(exist_ok=True)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.current_card_index = 0
    st.session_state.show_answer = False
    st.session_state.study_mode = 'active'  # 'active' or 'archived'
    

def load_flashcards():
    """Load flashcards from JSON file, or import from CSV if JSON doesn't exist."""
    if os.path.exists(FLASHCARDS_JSON):
        with open(FLASHCARDS_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Import from CSV for first time
        if os.path.exists('ppl_flashcards.csv'):
            df = pd.read_csv('ppl_flashcards.csv')
            flashcards = []
            for idx, row in df.iterrows():
                flashcards.append({
                    'id': idx,
                    'question': row['Question / Prompt'],
                    'answer_text': row['Answer / Notes'],
                    'answer_image': None,
                    'total_correct': 0,
                    'total_wrong': 0,
                    'consecutive_correct': 0,
                    'archived': False,
                    'created_date': datetime.now().isoformat(),
                    'history': []  # List of study sessions with results
                })
            save_flashcards(flashcards)
            return flashcards
        return []


def save_flashcards(flashcards):
    """Save flashcards to JSON file."""
    with open(FLASHCARDS_JSON, 'w', encoding='utf-8') as f:
        json.dump(flashcards, f, indent=2, ensure_ascii=False)


def get_next_id(flashcards):
    """Get the next available ID."""
    if not flashcards:
        return 0
    return max(card['id'] for card in flashcards) + 1


def get_active_cards(flashcards):
    """Get non-archived flashcards."""
    return [card for card in flashcards if not card['archived']]


def get_archived_cards(flashcards):
    """Get archived flashcards."""
    return [card for card in flashcards if card['archived']]


def display_image(image_path):
    """Display an image from file."""
    if image_path and os.path.exists(image_path):
        st.image(image_path, use_container_width=True)


def study_mode():
    """Study mode interface."""
    st.header("📚 Study Flashcards")
    
    flashcards = load_flashcards()
    
    # Mode selector
    mode = st.radio("Study mode:", ["Active Cards", "Archived Cards"], horizontal=True)
    st.session_state.study_mode = 'active' if mode == "Active Cards" else 'archived'
    
    if st.session_state.study_mode == 'active':
        cards = get_active_cards(flashcards)
        if not cards:
            st.info("No active flashcards available. Create some flashcards or reset archived ones!")
            return
    else:
        cards = get_archived_cards(flashcards)
        if not cards:
            st.info("No archived flashcards. Study active cards to archive them!")
            return
    
    # Ensure current index is valid
    if st.session_state.current_card_index >= len(cards):
        st.session_state.current_card_index = 0
    
    current_card = cards[st.session_state.current_card_index]
    
    # Progress indicator
    st.progress((st.session_state.current_card_index + 1) / len(cards))
    st.write(f"Card {st.session_state.current_card_index + 1} of {len(cards)}")
    
    # Statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ Correct", current_card['total_correct'])
    with col2:
        st.metric("❌ Wrong", current_card['total_wrong'])
    with col3:
        st.metric("🔥 Streak", current_card['consecutive_correct'])
    
    # Display question
    st.markdown("---")
    st.subheader("Question:")
    st.markdown(f"### {current_card['question']}")
    
    # Show/Hide answer button
    if not st.session_state.show_answer:
        if st.button("🔍 Show Answer", use_container_width=True, type="primary"):
            st.session_state.show_answer = True
            st.rerun()
    else:
        st.markdown("---")
        st.subheader("Answer:")
        
        # Display answer text
        if current_card['answer_text']:
            st.markdown(current_card['answer_text'])
        
        # Display answer image
        if current_card['answer_image']:
            display_image(current_card['answer_image'])
        
        st.markdown("---")
        
        # Answer buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("❌ Wrong", use_container_width=True, type="secondary"):
                # Update card statistics
                current_card['total_wrong'] += 1
                current_card['consecutive_correct'] = 0
                current_card['history'].append({
                    'date': datetime.now().isoformat(),
                    'result': 'wrong'
                })
                
                # Update flashcards
                for i, card in enumerate(flashcards):
                    if card['id'] == current_card['id']:
                        flashcards[i] = current_card
                        break
                
                save_flashcards(flashcards)
                
                # Move to next card
                st.session_state.current_card_index = (st.session_state.current_card_index + 1) % len(cards)
                st.session_state.show_answer = False
                st.rerun()
        
        with col2:
            if st.button("✅ Correct", use_container_width=True, type="primary"):
                # Update card statistics
                current_card['total_correct'] += 1
                current_card['consecutive_correct'] += 1
                current_card['history'].append({
                    'date': datetime.now().isoformat(),
                    'result': 'correct'
                })
                
                # Archive if 5 consecutive correct
                if current_card['consecutive_correct'] >= 5 and not current_card['archived']:
                    current_card['archived'] = True
                    st.success("🎉 Card archived! You got it right 5 times in a row!")
                
                # Update flashcards
                for i, card in enumerate(flashcards):
                    if card['id'] == current_card['id']:
                        flashcards[i] = current_card
                        break
                
                save_flashcards(flashcards)
                
                # Move to next card (or wrap around)
                next_index = st.session_state.current_card_index + 1
                if next_index >= len(cards):
                    next_index = 0
                    if st.session_state.study_mode == 'active':
                        # Reload cards to check if any are left
                        remaining_cards = get_active_cards(load_flashcards())
                        if not remaining_cards:
                            st.success("🎊 Congratulations! You've archived all active flashcards!")
                
                st.session_state.current_card_index = next_index
                st.session_state.show_answer = False
                st.rerun()
    

     # Navigation
    st.markdown("---")

    # Create a dictionary for selection
    card_options = {f"ID {card['id']}: {card['question'][:50]}...": card['id'] for card in flashcards}
    
    selected_card_label = st.selectbox("Jump to question:", list(card_options.keys()))
    selected_card_id = card_options[selected_card_label]

    if selected_card_id:
        st.session_state.current_card_index = selected_card_id
        st.session_state.show_answer = False
        st.rerun()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Previous"):
            st.session_state.current_card_index = (st.session_state.current_card_index - 1) % len(cards)
            st.session_state.show_answer = False
            st.rerun()
    with col3:
        if st.button("Next ➡️"):
            st.session_state.current_card_index = (st.session_state.current_card_index + 1) % len(cards)
            st.session_state.show_answer = False
            st.rerun()


def create_flashcard():
    """Create new flashcard interface."""
    st.header("➕ Create New Flashcard")
    
    with st.form("create_flashcard_form"):
        question = st.text_area("Question / Prompt:", height=100)
        
        answer_text = st.text_area("Answer (Text):", height=150)
        
        st.markdown("**Or add an image:**")
        uploaded_file = st.file_uploader("Upload Answer Image (optional)", type=['png', 'jpg', 'jpeg', 'gif'])
        
        submitted = st.form_submit_button("Create Flashcard", type="primary", use_container_width=True)
        
        if submitted:
            if not question:
                st.error("Please enter a question!")
            elif not answer_text and not uploaded_file:
                st.error("Please provide either text answer or image!")
            else:
                flashcards = load_flashcards()
                
                # Handle image upload
                image_path = None
                if uploaded_file:
                    image_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
                    image_path = os.path.join(IMAGES_FOLDER, image_filename)
                    with open(image_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                
                # Create new flashcard
                new_card = {
                    'id': get_next_id(flashcards),
                    'question': question,
                    'answer_text': answer_text,
                    'answer_image': image_path,
                    'total_correct': 0,
                    'total_wrong': 0,
                    'consecutive_correct': 0,
                    'archived': False,
                    'created_date': datetime.now().isoformat(),
                    'history': []
                }
                
                flashcards.append(new_card)
                save_flashcards(flashcards)
                
                st.success("✅ Flashcard created successfully!")
                st.balloons()


def edit_flashcard():
    """Edit existing flashcard interface."""
    st.header("✏️ Edit Flashcard")
    
    flashcards = load_flashcards()
    
    if not flashcards:
        st.info("No flashcards available to edit.")
        return
    
    # Create a dictionary for selection
    card_options = {f"ID {card['id']}: {card['question'][:50]}...": card['id'] for card in flashcards}
    
    selected_card_label = st.selectbox("Select flashcard to edit:", list(card_options.keys()))
    selected_card_id = card_options[selected_card_label]
    
    # Find the selected card
    selected_card = next(card for card in flashcards if card['id'] == selected_card_id)
    
    with st.form("edit_flashcard_form"):
        question = st.text_area("Question / Prompt:", value=selected_card['question'], height=100)
        
        answer_text = st.text_area("Answer (Text):", value=selected_card['answer_text'] or "", height=150)
        
        # Show current image if exists
        if selected_card['answer_image']:
            st.markdown("**Current Answer Image:**")
            display_image(selected_card['answer_image'])
            remove_image = st.checkbox("Remove current image")
        else:
            remove_image = False
        
        st.markdown("**Upload New Image (optional):**")
        uploaded_file = st.file_uploader("Upload Answer Image", type=['png', 'jpg', 'jpeg', 'gif'], key="edit_image")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)
        
        if submitted:
            if not question:
                st.error("Please enter a question!")
            elif not answer_text and not uploaded_file and (remove_image or not selected_card['answer_image']):
                st.error("Please provide either text answer or image!")
            else:
                # Handle image changes
                image_path = selected_card['answer_image']
                
                if remove_image:
                    if image_path and os.path.exists(image_path):
                        os.remove(image_path)
                    image_path = None
                
                if uploaded_file:
                    # Remove old image if replacing
                    if image_path and os.path.exists(image_path):
                        os.remove(image_path)
                    
                    image_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
                    image_path = os.path.join(IMAGES_FOLDER, image_filename)
                    with open(image_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                
                # Update card
                selected_card['question'] = question
                selected_card['answer_text'] = answer_text
                selected_card['answer_image'] = image_path
                
                # Update in flashcards list
                for i, card in enumerate(flashcards):
                    if card['id'] == selected_card_id:
                        flashcards[i] = selected_card
                        break
                
                save_flashcards(flashcards)
                st.success("✅ Flashcard updated successfully!")


def delete_flashcard():
    """Delete flashcard interface."""
    st.header("🗑️ Delete Flashcard")
    
    flashcards = load_flashcards()
    
    if not flashcards:
        st.info("No flashcards available to delete.")
        return
    
    # Create a dictionary for selection
    card_options = {f"ID {card['id']}: {card['question'][:50]}...": card['id'] for card in flashcards}
    
    selected_card_label = st.selectbox("Select flashcard to delete:", list(card_options.keys()))
    selected_card_id = card_options[selected_card_label]
    
    # Find the selected card
    selected_card = next(card for card in flashcards if card['id'] == selected_card_id)
    
    # Preview
    st.markdown("---")
    st.subheader("Preview:")
    st.markdown(f"**Question:** {selected_card['question']}")
    st.markdown(f"**Answer:** {selected_card['answer_text']}")
    if selected_card['answer_image']:
        st.markdown("**Image:**")
        display_image(selected_card['answer_image'])
    
    st.markdown("---")
    st.warning("⚠️ This action cannot be undone!")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🗑️ Confirm Delete", type="primary", use_container_width=True):
            # Remove image file if exists
            if selected_card['answer_image'] and os.path.exists(selected_card['answer_image']):
                os.remove(selected_card['answer_image'])
            
            # Remove from flashcards
            flashcards = [card for card in flashcards if card['id'] != selected_card_id]
            save_flashcards(flashcards)
            
            st.success("✅ Flashcard deleted successfully!")
            st.rerun()


def manage_archived():
    """Manage archived flashcards."""
    st.header("📦 Manage Archived Flashcards")
    
    flashcards = load_flashcards()
    archived_cards = get_archived_cards(flashcards)
    
    if not archived_cards:
        st.info("No archived flashcards yet. Archive cards by getting them correct 5 times in a row!")
        return
    
    st.write(f"**Total archived cards:** {len(archived_cards)}")
    
    # Display archived cards
    for card in archived_cards:
        with st.expander(f"ID {card['id']}: {card['question'][:60]}..."):
            st.markdown(f"**Question:** {card['question']}")
            st.markdown(f"**Answer:** {card['answer_text']}")
            if card['answer_image']:
                display_image(card['answer_image'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Correct", card['total_correct'])
            with col2:
                st.metric("Total Wrong", card['total_wrong'])
            with col3:
                st.metric("Streak", card['consecutive_correct'])
    
    st.markdown("---")
    
    # Reset options
    st.subheader("Reset Options:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Reset ALL Archived Cards", type="primary", use_container_width=True):
            for card in flashcards:
                if card['archived']:
                    card['archived'] = False
                    card['consecutive_correct'] = 0
            
            save_flashcards(flashcards)
            st.success(f"✅ Reset {len(archived_cards)} archived cards!")
            st.rerun()
    
    with col2:
        # Individual reset
        if archived_cards:
            card_options = {f"ID {card['id']}: {card['question'][:40]}...": card['id'] 
                          for card in archived_cards}
            selected_label = st.selectbox("Select card to reset:", list(card_options.keys()))
            selected_id = card_options[selected_label]
            
            if st.button("🔄 Reset Selected Card", use_container_width=True):
                for card in flashcards:
                    if card['id'] == selected_id:
                        card['archived'] = False
                        card['consecutive_correct'] = 0
                        break
                
                save_flashcards(flashcards)
                st.success("✅ Card reset successfully!")
                st.rerun()


def statistics():
    """Display statistics dashboard."""
    st.header("📊 Statistics")
    
    flashcards = load_flashcards()
    
    if not flashcards:
        st.info("No flashcards available. Create some flashcards first!")
        return
    
    active_cards = get_active_cards(flashcards)
    archived_cards = get_archived_cards(flashcards)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📝 Total Cards", len(flashcards))
    with col2:
        st.metric("✅ Active Cards", len(active_cards))
    with col3:
        st.metric("📦 Archived Cards", len(archived_cards))
    with col4:
        total_attempts = sum(card['total_correct'] + card['total_wrong'] for card in flashcards)
        st.metric("🎯 Total Attempts", total_attempts)
    
    # Overall accuracy
    total_correct = sum(card['total_correct'] for card in flashcards)
    total_wrong = sum(card['total_wrong'] for card in flashcards)
    total = total_correct + total_wrong
    
    if total > 0:
        accuracy = (total_correct / total) * 100
        st.markdown("---")
        st.subheader(f"Overall Accuracy: {accuracy:.1f}%")
        st.progress(accuracy / 100)
    
    # Detailed statistics
    st.markdown("---")
    st.subheader("Detailed Card Statistics")
    
    # Create DataFrame for display
    stats_data = []
    for card in flashcards:
        total_attempts = card['total_correct'] + card['total_wrong']
        accuracy = (card['total_correct'] / total_attempts * 100) if total_attempts > 0 else 0
        
        stats_data.append({
            'ID': card['id'],
            'Question': card['question'][:60] + '...' if len(card['question']) > 60 else card['question'],
            'Correct': card['total_correct'],
            'Wrong': card['total_wrong'],
            'Streak': card['consecutive_correct'],
            'Accuracy': f"{accuracy:.1f}%",
            'Status': '📦 Archived' if card['archived'] else '✅ Active'
        })
    
    df = pd.DataFrame(stats_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def main():
    """Main application."""
    st.set_page_config(
        page_title="Flashcards App",
        page_icon="🎴",
        layout="wide"
    )
    
    st.title("🎴 Flashcards Study App")
    st.markdown("Learn effectively with spaced repetition!")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    menu = st.sidebar.radio(
        "Choose an option:",
        ["📚 Study", "➕ Create", "✏️ Edit", "🗑️ Delete", "📦 Archived", "📊 Statistics"]
    )
    
    st.sidebar.markdown("---")
    
    # Display quick stats in sidebar
    flashcards = load_flashcards()
    active_count = len(get_active_cards(flashcards))
    archived_count = len(get_archived_cards(flashcards))
    
    st.sidebar.markdown("### Quick Stats")
    st.sidebar.metric("Active Cards", active_count)
    st.sidebar.metric("Archived Cards", archived_count)

    st.sidebar.markdown("---")
    
    # --- NEW BACKUP SECTION START ---
    st.sidebar.markdown("### Backup Progress")
    if os.path.exists(FLASHCARDS_JSON):
        with open(FLASHCARDS_JSON, 'r', encoding='utf-8') as f:
            json_data = f.read()
            
        st.sidebar.download_button(
            label="💾 Download Backup",
            data=json_data,
            file_name=f"flashcards_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )
    else:
        st.sidebar.info("No save data yet.")
    # --- NEW BACKUP SECTION END ---
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "Study flashcards and track your progress. "
        "Cards are automatically archived after 5 consecutive correct answers."
    )
    
    # Route to appropriate page
    if menu == "📚 Study":
        study_mode()
    elif menu == "➕ Create":
        create_flashcard()
    elif menu == "✏️ Edit":
        edit_flashcard()
    elif menu == "🗑️ Delete":
        delete_flashcard()
    elif menu == "📦 Archived":
        manage_archived()
    elif menu == "📊 Statistics":
        statistics()


if __name__ == "__main__":
    main()
