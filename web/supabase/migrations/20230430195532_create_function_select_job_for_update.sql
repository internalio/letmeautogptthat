CREATE OR REPLACE FUNCTION public.select_job_for_update()
 RETURNS SETOF jobs
 LANGUAGE plpgsql
AS $function$
DECLARE job_id UUID;
BEGIN 
	SELECT jobs.id INTO job_id 
	FROM jobs 
	WHERE jobs.status IS NULL
	ORDER BY created_at ASC
	LIMIT 1 
	FOR UPDATE;
	
	RETURN QUERY
	UPDATE jobs 
		SET started_at = now(),
        status = 'queued'
	WHERE id = job_id
	RETURNING jobs.*;
END;
$function$
;