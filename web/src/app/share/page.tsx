'use client';

import AboutLink from '@/components/AboutLink';
import Image from 'next/image';
import { useEffect, useMemo, useRef, useState } from 'react';

const OFFSET_X = 50;
const OFFSET_Y = 50;

const BUTTON_FOCUS_STYLE = {
  '--tw-text-opacity': 1,
  color: 'rgb(255 255 255 / var(--tw-text-opacity))',
  borderColor: 'transparent',
  background: 'linear-gradient(to right, #f8491b, #f12f3f, #dc1860) border-box',
  outline: '2px solid transparent',
  outlineOffset: '2px',
  '--tw-ring-offset-shadow':
    'var(--tw-ring-inset) 0 0 0 var(--tw-ring-offset-width) var(--tw-ring-offset-color)',
  '--tw-ring-shadow':
    'var(--tw-ring-inset) 0 0 0 calc(2px + var(--tw-ring-offset-width)) var(--tw-ring-color)',
  boxShadow:
    'var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow, 0 0 #0000)',
  '--tw-ring-opacity': 1,
  '--tw-ring-color': 'rgb(226 31 88 / var(--tw-ring-opacity))',
  '--tw-ring-offset-width': '2px',
};

function getCenter(rect: DOMRect) {
  const x = Math.floor(rect.left + rect.width / 2);
  const y = Math.floor(rect.top + rect.height / 2);

  return [x, y];
}

function writeInput(
  ele: HTMLInputElement,
  text: string,
  time: number,
  startDelay: number
) {
  const millisecondsPerCharacter = Math.floor(time / text.length);
  for (let i = 0; i < text.length; i++) {
    const char = text.charAt(i);

    setTimeout(() => {
      ele.value += char;
    }, millisecondsPerCharacter * i + startDelay);
  }
}

export default function Home() {
  const [inputRef, setInputRef] = useState<HTMLInputElement | null>(null);
  const [buttonRef, setButtonRef] = useState<HTMLButtonElement | null>(null);
  const formRef = useRef<HTMLFormElement | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const currentUrl = new URL(window.location.href);
  const query = currentUrl.searchParams.get('q');
  const hasQuery = query !== null;

  const [animationState, setAnimationState] = useState<
    | 'loading'
    | 'go-to-input'
    | 'wait-at-input'
    | 'go-to-button'
    | 'wait-at-button'
    | 'done'
  >('loading');

  const cursorStyle = useMemo(() => {
    switch (animationState) {
      case 'go-to-input': {
        const rect = inputRef?.getBoundingClientRect();
        if (!rect) {
          return {};
        }

        const [x, y] = getCenter(rect);

        return {
          transition: '1.2s',
          transform: `translate(${x - OFFSET_X}px, ${y - OFFSET_Y}px)`,
        };
      }
      case 'wait-at-input': {
        const rect = inputRef?.getBoundingClientRect();
        if (!rect) {
          return {};
        }

        const [x, y] = getCenter(rect);

        return {
          transition: '1.5s',
          transform: `translate(${x - OFFSET_X}px, ${y - OFFSET_Y}px)`,
        };
      }
      case 'done':
      case 'wait-at-button':
      case 'go-to-button': {
        const rect = buttonRef?.getBoundingClientRect();
        if (!rect) {
          return {};
        }

        const [x, y] = getCenter(rect);
        return {
          transition: '800ms',
          transform: `translate(${x - OFFSET_X}px, ${y - OFFSET_Y}px)`,
        };
      }
      default: {
        return {};
      }
    }
  }, [animationState, inputRef, buttonRef]);

  useEffect(() => {
    if (timeoutRef.current || !query) {
      return;
    }

    if (!inputRef || !buttonRef) {
      return;
    }

    switch (animationState) {
      case 'loading': {
        timeoutRef.current = setTimeout(() => {
          timeoutRef.current = null;
          setAnimationState('go-to-input');
        }, 100);
      }
      case 'go-to-input': {
        timeoutRef.current = setTimeout(() => {
          timeoutRef.current = null;
          inputRef.focus();
          setAnimationState('wait-at-input');
        }, 1600);
        break;
      }
      case 'wait-at-input': {
        const keyDelay = 75;
        writeInput(inputRef, query, query.length * keyDelay, 200);

        timeoutRef.current = setTimeout(() => {
          timeoutRef.current = null;
          setAnimationState('go-to-button');
        }, query.length * keyDelay + 500);
        break;
      }
      case 'go-to-button': {
        timeoutRef.current = setTimeout(() => {
          timeoutRef.current = null;
          setAnimationState('wait-at-button');
        }, 700);
        break;
      }
      case 'wait-at-button': {
        timeoutRef.current = setTimeout(() => {
          timeoutRef.current = null;
          setAnimationState('done');
        }, 300);
        break;
      }
      case 'done': {
        timeoutRef.current = setTimeout(() => {
          timeoutRef.current = null;
          formRef.current?.submit();
        }, 1000);
        break;
      }
    }
  }, [animationState, inputRef, buttonRef, query]);

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
            ref={setInputRef}
            type="search"
            placeholder="What can I do for you?"
            name="query"
            className="w-full"
          />
          <div className="mt-2 flex items-center">
            <button
              type="button"
              ref={setButtonRef}
              className="button-primary"
              style={animationState === 'wait-at-button' ? BUTTON_FOCUS_STYLE : {}}
            >
              Execute it
            </button>
          </div>
        </form>

        <Image
          src="/mouse_arrow.png"
          alt="mouse arrow"
          width={15}
          height={21}
          className={hasQuery ? '' : 'hidden'}
          style={{
            position: 'fixed',
            top: OFFSET_X,
            left: OFFSET_Y,
            transition: '1s',
            ...cursorStyle,
          }}
        />
      </div>
      <AboutLink />
    </>
  );
}
