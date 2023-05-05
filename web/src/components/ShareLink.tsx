import { useRef } from 'react';

interface Props {
  header: string;
  link: string;
  className?: string;
}

export default function ShareLink({ header, link, className }: Props) {
  const outputRef = useRef<HTMLInputElement | null>(null);

  const copyToClipboard = async () => {
    if (!outputRef.current) {
      return;
    }

    if ('clipboard' in navigator) {
      await navigator.clipboard.writeText(link);
    } else {
      document.execCommand('copy', true, link);
    }

    alert('URL copied');

    outputRef.current?.focus();
    outputRef.current?.select();
  };

  return (
    <div className={className}>
      <div className="mt-6 bg-cyan-300 p-6 text-center">{header}</div>
      <div>
        <input ref={outputRef} value={link} readOnly className="mt-4 w-full" />
        <div
          className="mt-4 bg-cyan-300 p-1 text-center text-white underline hover:cursor-pointer"
          onClick={copyToClipboard}
        >
          Copy URL
        </div>
      </div>
    </div>
  );
}
