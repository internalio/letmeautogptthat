import { Database } from '@/lib/database.types';
import { createServerSupabaseClient } from '@supabase/auth-helpers-nextjs';
import { NextApiRequest, NextApiResponse } from 'next';

const post = async (req: NextApiRequest, res: NextApiResponse) => {
  const query: string = req.body['query'];

  const supabase = createServerSupabaseClient<Database>({ req, res });

  const { data, error } = await supabase
    .from('jobs')
    .insert({
      task: query,
    })
    .select();

  if (error) {
    return res.status(400).json({ ok: false });
  }

  return res.redirect(303, `/job/${data[0].id}`);
};

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  switch (req.method) {
    case 'POST':
      await post(req, res);
      break;
    default:
      res.send({ status: 404, body: '' });
  }
}
