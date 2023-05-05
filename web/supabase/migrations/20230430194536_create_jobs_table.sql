create table "public"."jobs" (
    "id" uuid not null default extensions.uuid_generate_v4(),
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone,
    "started_at" timestamp with time zone,
    "deleted_at" timestamp with time zone,
    "status" character varying,
    "status_message" character varying,
    "messages" jsonb,
    "log" jsonb,
    "output" text,
    "task" text
);


alter table "public"."jobs" enable row level security;

CREATE UNIQUE INDEX jobs_pkey ON public.jobs USING btree (id);

alter table "public"."jobs" add constraint "jobs_pkey" PRIMARY KEY using index "jobs_pkey";