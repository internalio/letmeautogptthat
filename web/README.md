# Setup

## Run locally

```bash
yarn run dev
```

## Supabase

1. Install supabase cli: https://supabase.com/docs/guides/cli
2. Run `supabase login` to auth with supabase
3. Run `supabase link --project-ref <project id>` and enter the password
4. Run `supabase start` to run a local instance of supabase
5. Set an env var for `NEXT_PUBLIC_SUPABASE_URL` with the provided `API URL`
6. Set an env var for `NEXT_PUBLIC_SUPABASE_ANON_KEY` with the provided `anon key`

### Supabase local

Here are the default local supabase URLs:
API URL: http://localhost:54321
DB URL: postgresql://postgres:postgres@localhost:54322/postgres
Studio URL: http://localhost:54323

### Supabase workflow

You can work with supabase by manually writing data migrations. Details are here: TODO
Alternatively supabase can diff changes in a local database against remote.

1. Make changes to the local db manually or through the studio
2. Run `supabase db diff` to view the diff with remote
3. Run `supabase db diff -f <file-name>` to generate a migration for the diff
4. Run `supabase db push` to run the migration in production (TODO automate)
5. When shutting down run the local instance run `supabase stop --backup` or any local data will be lost

#### Applying migrations locally

1. Run `supabase db reset`
   NOTE: This will delete local data. If you want to keep local data do the following
1. Run `supabase stop --backup`
1. Run `supabase db start`
1. Run `supabase db reset`

   (MK - Haven't tested this yet.)

### Generating types

1. `supabase gen types typescript --local > src/lib/database.types.ts`

More details are available here: https://supabase.com/docs/guides/cli/local-development
And this github issue has been helpful: https://github.com/orgs/supabase/discussions/6366
