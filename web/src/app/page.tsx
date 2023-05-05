'use client';

import AboutLink from '@/components/AboutLink';
import ShareLink from '@/components/ShareLink';
import { createShareURL } from '@/services/share';
import { useRef, useState } from 'react';

export default function Home() {
  const [link, setLink] = useState<string | undefined>();
  const formRef = useRef<HTMLFormElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const onGetLink = () => {
    if (inputRef?.current) {
      const url = createShareURL(inputRef.current.value);
      setLink(url);
    }
  };

  return (
    <>
      <div className="flex w-full grow flex-col items-center justify-center">
        <h2 className="text-3xl md:text-5xl">Let me AutoGPT that for you...</h2>
        <form
          ref={formRef}
          action="/api/jobs"
          method="POST"
          className="mt-4 flex w-full flex-col items-center object-center"
        >
          <input
            ref={inputRef}
            type="search"
            placeholder="What can I do for you?"
            name="query"
            className="w-full"
          />
          <div className="mt-2 flex items-center">
            <button
              type="submit"
              onClick={() => formRef.current?.submit()}
              className="button-primary"
            >
              Execute it
            </button>
            <button type="button" onClick={onGetLink} className="button-primary ml-2">
              Get link
            </button>
          </div>
        </form>

        {link && <ShareLink link={link} header="All done! Share the link below." />}
      </div>
      <AboutLink />
    </>
  );
}
