-- Update updated_at 
create extension if not exists moddatetime schema extensions;

-- this trigger will set the "updated_at" column to the current timestamp for every update
create trigger handle_updated_at before update on jobs
  for each row execute procedure extensions.moddatetime (updated_at);