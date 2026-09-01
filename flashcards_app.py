import streamlit as st
import pandas as pd
import json
import os
import uuid
from datetime import datetime
from supabase import create_client, Client

# Supabase storage
STORAGE_BUCKET = "flashcard-images"


@st.cache_resource
def get_supabase() -> Client:
    """Create a cached Supabase client from Streamlit secrets."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def save_session_state():
    """Save current session state (card index and study mode) to Supabase."""
    get_supabase().table("app_state").upsert({
        'id': 1,
        'current_card_index': st.session_state.current_card_index,
        'study_mode': st.session_state.study_mode
    }).execute()

def load_session_state():
    """Load the last saved session state (card index and study mode) from Supabase."""
    resp = get_supabase().table("app_state").select("*").eq("id", 1).execute()
    if resp.data:
        return resp.data[0]
    return None

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    
    # Load saved session state or use defaults
    saved_state = load_session_state()
    if saved_state:
        st.session_state.current_card_index = saved_state.get('current_card_index', 0)
        st.session_state.study_mode = saved_state.get('study_mode', 'active')
    else:
        st.session_state.current_card_index = 0
        st.session_state.study_mode = 'active'  # 'active' or 'archived'
    
    st.session_state.show_answer = False
    st.session_state.selected_jump_card = None  # Track selectbox selection
    

def load_flashcards():
    """Load all flashcards from Supabase, ordered by id."""
    resp = get_supabase().table("flashcards").select("*").order("id").execute()
    cards = resp.data or []
    for card in cards:
        # jsonb comes back as a list already; guard against nulls
        if card.get("history") is None:
            card["history"] = []
    return cards


def save_flashcards(flashcards):
    """Upsert all flashcards to Supabase (payload is small — images live in Storage)."""
    if not flashcards:
        return
    get_supabase().table("flashcards").upsert(flashcards).execute()


def save_card(card):
    """Upsert a single flashcard (cheap, used after answering)."""
    get_supabase().table("flashcards").upsert(card).execute()


def delete_card(card_id):
    """Delete a single flashcard row from Supabase."""
    get_supabase().table("flashcards").delete().eq("id", card_id).execute()


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


def upload_image(uploaded_file):
    """Upload an image to Supabase Storage and return its public URL."""
    if uploaded_file is None:
        return None

    file_ext = uploaded_file.name.split('.')[-1].lower()
    if file_ext not in ['png', 'jpg', 'jpeg', 'gif']:
        file_ext = 'png'
    mime_type = f"image/{file_ext}"
    object_path = f"{uuid.uuid4().hex}.{file_ext}"

    storage = get_supabase().storage.from_(STORAGE_BUCKET)
    storage.upload(
        object_path,
        uploaded_file.getvalue(),
        {"content-type": mime_type},
    )
    return storage.get_public_url(object_path)


def display_image(image_data):
    """Display an image from a URL or a legacy base64 data URI."""
    if not image_data:
        return
    if isinstance(image_data, str) and (
        image_data.startswith('http') or image_data.startswith('data:image')
    ):
        st.image(image_data, use_container_width=True)


def study_mode():
    """Study mode interface."""
    st.header("📚 Study Flashcards")
    
    flashcards = load_flashcards()
    
    # Mode selector
    mode = st.radio("Study mode:", ["Active Cards", "Archived Cards"], horizontal=True)
    new_mode = 'active' if mode == "Active Cards" else 'archived'
    
    # If mode changed, reset to first card of new mode
    if new_mode != st.session_state.study_mode:
        st.session_state.study_mode = new_mode
        st.session_state.current_card_index = 0
    else:
        st.session_state.study_mode = new_mode
    
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

                save_card(current_card)

                # Move to next card
                st.session_state.current_card_index = (st.session_state.current_card_index + 1) % len(cards)
                st.session_state.show_answer = False
                save_session_state()
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

                save_card(current_card)
                
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
                save_session_state()
                st.rerun()
    

    # Navigation
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Previous"):
            st.session_state.current_card_index = (st.session_state.current_card_index - 1) % len(cards)
            st.session_state.show_answer = False
            st.session_state.selected_jump_card = None  # Clear jump selection
            save_session_state()
            st.rerun()
    with col3:
        if st.button("Next ➡️"):
            st.session_state.current_card_index = (st.session_state.current_card_index + 1) % len(cards)
            st.session_state.show_answer = False
            st.session_state.selected_jump_card = None  # Clear jump selection
            save_session_state()
            st.rerun()
    
    # Jump to specific question
    st.markdown("---")
    
    # Build options with current card pre-selected
    current_card = cards[st.session_state.current_card_index]
    card_options = [f"ID {card['id']}: {card['question'][:50]}..." for card in cards]
    current_option = f"ID {current_card['id']}: {current_card['question'][:50]}..."
    
    # Find the index of current card in the selectbox options
    try:
        default_index = card_options.index(current_option)
    except ValueError:
        default_index = 0
    
    selected_label = st.selectbox(
        "Jump to question:", 
        card_options,
        index=default_index,
        key="jump_selectbox"
    )
    
    # Extract ID from selected label
    selected_id = int(selected_label.split(":")[0].replace("ID ", ""))
    
    # Only jump if selection changed from a user action (not just a rerun)
    if st.session_state.selected_jump_card != selected_id:
        # Find the index in cards list
        for idx, card in enumerate(cards):
            if card['id'] == selected_id:
                if idx != st.session_state.current_card_index:
                    st.session_state.current_card_index = idx
                    st.session_state.show_answer = False
                    st.session_state.selected_jump_card = selected_id
                    save_session_state()
                    st.rerun()
                break


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
                
                # Handle image upload - store in Supabase Storage
                image_data = None
                if uploaded_file:
                    image_data = upload_image(uploaded_file)
                
                # Create new flashcard
                new_card = {
                    'id': get_next_id(flashcards),
                    'question': question,
                    'answer_text': answer_text,
                    'answer_image': image_data,
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
                image_data = selected_card['answer_image']
                
                if remove_image:
                    image_data = None
                
                if uploaded_file:
                    # Upload new image to Supabase Storage
                    image_data = upload_image(uploaded_file)
                
                # Update card
                selected_card['question'] = question
                selected_card['answer_text'] = answer_text
                selected_card['answer_image'] = image_data
                
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
            # Remove the row from Supabase (images stay in Storage; harmless)
            delete_card(selected_card_id)
            
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
        page_title="PPL Flashcards",
        page_icon="🎴",
        layout="wide"
    )
    
    st.title("🎴 PPL Flashcards")
    st.markdown("Learning to fly high!")
    
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
    
    # --- BACKUP & RESTORE SECTION START ---
    # Data now lives in Supabase (synced across devices). These are optional
    # export/import helpers for extra safety.
    st.sidebar.markdown("### 💾 Backup & Restore")
    
    # Upload backup file -> upsert into Supabase
    uploaded_backup = st.sidebar.file_uploader(
        "📤 Restore from backup:",
        type=['json'],
        help="Upload a previously downloaded backup file to merge it back into the cloud database"
    )
    
    if uploaded_backup is not None:
        try:
            backup_data = json.load(uploaded_backup)
            if isinstance(backup_data, list):
                save_flashcards(backup_data)
                st.sidebar.success(f"✅ Restored {len(backup_data)} flashcards to the cloud!")
                if st.sidebar.button("🔄 Reload Now", use_container_width=True):
                    st.rerun()
            else:
                st.sidebar.error("❌ Invalid backup file format!")
        except json.JSONDecodeError:
            st.sidebar.error("❌ Invalid JSON file!")
        except Exception as e:
            st.sidebar.error(f"❌ Error: {str(e)}")
    
    # Download backup -> current cloud data
    st.sidebar.markdown("---")
    if flashcards:
        json_data = json.dumps(flashcards, indent=2, ensure_ascii=False)
        st.sidebar.download_button(
            label="💾 Download Backup",
            data=json_data,
            file_name="flashcards_data.json",
            mime="application/json",
            use_container_width=True
        )
        st.sidebar.caption("💡 Your data auto-saves to the cloud — this is just an extra copy.")
    else:
        st.sidebar.info("No save data yet.")
    # --- BACKUP & RESTORE SECTION END ---
    
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
