'use client';

import ArrowLeftIcon from '@heroicons/react/24/outline/ArrowLeftIcon';
import { useRouter } from 'next/navigation';

export default function BackButton() {
  const router = useRouter();

  return (
    <button
      className="mb-20 self-start border-0 bg-transparent px-0 shadow-none hover:bg-none hover:text-brand focus:border-none focus:bg-none focus:shadow-none focus:outline-none active:border-none active:bg-none"
      onClick={() => router.back()}
    >
      <ArrowLeftIcon className="h-5 w-5" />
    </button>
  );
}
