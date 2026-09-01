-- ============================================================
-- PPL Flashcards — Supabase setup
-- Run this once in your Supabase project:
--   Dashboard > SQL Editor > New query > paste > Run
-- ============================================================

-- 1. Table holding all card metadata (small — no images here)
create table if not exists public.flashcards (
    id                  integer primary key,
    question            text not null,
    answer_text         text,
    answer_image        text,            -- public URL to an image in Storage (or null)
    total_correct       integer not null default 0,
    total_wrong         integer not null default 0,
    consecutive_correct integer not null default 0,
    archived            boolean not null default false,
    created_date        text,
    history             jsonb not null default '[]'::jsonb
);

-- 2. Storage bucket for the (few) answer images.
--    Public bucket => images load with a plain URL, no signed links needed.
insert into storage.buckets (id, name, public)
values ('flashcard-images', 'flashcard-images', true)
on conflict (id) do nothing;

-- ============================================================
-- Notes:
-- * The app connects with the SERVICE_ROLE key (kept in st.secrets),
--   which bypasses row-level security, so no RLS policies are needed.
-- * If you'd rather use the anon key, enable RLS and add permissive
--   policies — but service_role is simpler for a single-user app.
-- ============================================================
