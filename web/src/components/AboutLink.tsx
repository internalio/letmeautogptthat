import Link from 'next/link';

export default function AboutLink() {
  return (
    <div className="fixed bottom-0 left-0 flex w-full justify-center border-t-2 border-slate-200 p-1">
      <Link href="/about" className="text-sm text-slate-600">
        What is this?
      </Link>
    </div>
  );
}
