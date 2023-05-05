'use client';

import ShareLink from '@/components/ShareLink';
import { Spinner } from '@/components/Spinner/Spinner';
import { createJobURL, createShareURL } from '@/services/share';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';
import Link from 'next/link';
import { useEffect, useMemo, useRef, useState } from 'react';

interface JobData {
  status: string;
  statusMessage: string;
  messages: string[];
  output: string;
  query: string;
}

function PollJob(jobId: string) {
  const [job, setJob] = useState<JobData | undefined>(undefined);
  const [jobError, setJobError] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (job?.status === 'completed' || jobError !== undefined) {
      return;
    }

    const timeoutId = setTimeout(
      async () => {
        const response = await fetch('/api/jobs/' + jobId);
        const body = await response.json();

        if (response.status >= 400) {
          setJobError(body);
        } else {
          setJob(body as JobData);
        }
      },
      job === undefined ? 0 : 1000
    );
    return () => clearTimeout(timeoutId);
  }, [jobId, job, jobError, setJob, setJobError]);

  return {
    job,
    jobError,
  };
}

function JobMessages({ messages, animate }: { messages: string[]; animate: boolean }) {
  const lastMessage = useRef<HTMLDivElement | null>(null);
  const [messageStyles, setMessageStyles] = useState<Array<object | undefined>>([]);

  useEffect(() => {
    if (!animate || messages.length === messageStyles.length) {
      return;
    }

    setTimeout(() => {
      setMessageStyles((prev) =>
        prev.map((style, index) => {
          if (index === messageStyles.length) {
            setTimeout(() => {
              lastMessage.current?.scrollIntoView();
            }, 800);

            return {
              transition: '300ms',
            };
          }

          return style;
        })
      );
    }, 300);

    setMessageStyles((prev) =>
      prev.concat({
        opacity: 0.0,
        position: 'absolute',
        transform: 'translate(0, -70px)',
      })
    );
  }, [animate, messageStyles, messages, setMessageStyles]);

  return (
    <div>
      {messages.map((message, index) => (
        <div
          key={index}
          ref={index == messages.length - 1 ? lastMessage : undefined}
          className="mb-3 rounded-md border-2 bg-slate-800 p-3 text-lime-400 hover:border-lime-200"
          style={messageStyles[index]}
        >
          {message}
        </div>
      ))}
    </div>
  );
}

export default function JobPage({ params: { id } }) {
  const { job, jobError } = PollJob(id);

  const searchLink = useMemo(() => {
    if (job?.query) {
      return createShareURL(job?.query);
    }
  }, [job?.query]);

  if (jobError) {
    return (
      <>
        <Link href="/" className="flex items-center">
          <ArrowLeftIcon className="h-5 w-5" />{' '}
          <span className="ml-2">try another search</span>
        </Link>
        <div className="mt-4 rounded-md border-2 border-red-400 bg-slate-800 p-3 text-white">
          Something went wrong loading the job. Please try again later.
        </div>
      </>
    );
  }

  if (!job) {
    return (
      <h1 className="flex items-center">
        Task: <Spinner className="ml-2 inline-block h-5 w-5" />
      </h1>
    );
  }

  const jobCompleted = job.status === 'failed' || job.status === 'completed';

  return (
    <>
      <Link href="/" className="flex items-center">
        <ArrowLeftIcon className="h-5 w-5" />{' '}
        <span className="ml-2">try another search</span>
      </Link>
      <h1 className="mt-4">Task: {job.query}</h1>
      <div className="flex items-center">
        <span className="mr-2">Status:</span> <JobStatus status={job.status} />
      </div>
      {job.status === 'failed' && (
        <div className="rounded-md border-2 border-red-400 bg-slate-800 p-3 text-white">
          We’re sorry, because this is a demo, we cannot have our agents running for too
          long.
        </div>
      )}

      <h1 className="mb-2 mt-3">Thoughts by AutoGPT</h1>
      <JobMessages messages={job.messages || []} animate={!job.output} />

      {job.output && (
        <>
          <h1 className="mt-3">Result</h1>
          <div className="rounded-md border-2 border-yellow-400 bg-slate-800 p-3 text-yellow-400">
            {job.output}
          </div>
        </>
      )}

      {searchLink && jobCompleted && (
        <div className="flex w-full grow items-center justify-center">
          <ShareLink link={searchLink} header="Share your query below." />
          <ShareLink
            link={createJobURL(id)}
            header="Share your results below."
            className="ml-4"
          />
        </div>
      )}
    </>
  );
}

function JobStatus({ status }: { status: string }) {
  if (status === 'completed') {
    return <span className="text-green-400">completed</span>;
  }

  if (status === 'failed') {
    return <div className="text-red-400">failed</div>;
  }

  return (
    <span className="flex items-center">
      {status} <Spinner className="ml-2 inline-block h-5 w-5" />
    </span>
  );
}
