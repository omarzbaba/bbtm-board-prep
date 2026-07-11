-- Optional cloud-sync backend for the BB/TM board-prep app.
-- Run this once against your Supabase project (SQL editor or `supabase db push`).
--
-- Model: one row per learner profile, holding the whole LearnerState JSON blob.
-- The app upserts on change (debounced) and loads on startup.

create table if not exists public.learner_states (
  learner_id  text primary key,
  state       jsonb       not null default '{}'::jsonb,
  updated_at  timestamptz not null default now()
);

alter table public.learner_states enable row level security;

-- SECURITY POSTURE (documented tradeoff):
-- This is a personal study tool. The learner_id is a random string that acts as a
-- shared secret / handle. With the public anon key, these policies let the app
-- read and upsert rows by learner_id. Do NOT store sensitive data here — it is only
-- quiz progress, notes, and weak-marks. For multi-user hardening, replace the anon
-- policies below with Supabase Auth (auth.uid()) and add a user_id column.

drop policy if exists "study read"   on public.learner_states;
drop policy if exists "study insert" on public.learner_states;
drop policy if exists "study update" on public.learner_states;

create policy "study read"   on public.learner_states for select to anon using (true);
create policy "study insert" on public.learner_states for insert to anon with check (true);
create policy "study update" on public.learner_states for update to anon using (true) with check (true);
