import { Database } from '@/lib/database.types';
import { createServerSupabaseClient } from '@supabase/auth-helpers-nextjs';
import { NextApiRequest, NextApiResponse } from 'next';

const get = async (req: NextApiRequest, res: NextApiResponse) => {
  const { id } = req.query;

  const supabase = createServerSupabaseClient<Database>({ req, res });

  const { data, error } = await supabase
    .from('jobs')
    .select()
    .eq('id', id)
    .is('deleted_at', null);
  if (error) {
    return res.status(400).json({ ok: false });
  }

  if (!data || !data.length) {
    res.status(404).json({});
    return;
  }

  const job = data[0];

  res.status(200).json({
    status: job.status,
    statusMessage: job.status_message,
    messages: job.messages,
    output: job.output,
    query: job.task,
  });

  return;
};

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  switch (req.method) {
    case 'GET':
      await get(req, res);
      break;
    default:
      res.send({ status: 404, body: '' });
  }
}
