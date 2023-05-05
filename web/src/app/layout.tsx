import { Inter } from 'next/font/google';

// https://github.com/FortAwesome/react-fontawesome/issues/234
import { config } from '@fortawesome/fontawesome-svg-core';
import '@fortawesome/fontawesome-svg-core/styles.css';
import { Analytics } from '@vercel/analytics/react';

config.autoAddCss = false;

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'fallback',
  weight: ['400', '500', '600', '700'],
});
import '@/styles/globals.css';
import Head from './head';

// do not cache this layout
export const revalidate = 0;

export default async function RootLayout({ children }) {
  return (
    <html lang="en">
      <Head />
      <body className={inter.className}>
        <div className={`flex min-h-screen flex-col items-center justify-start`}>
          <main className="relative z-0 flex min-h-screen w-full max-w-6xl flex-col p-4 md:p-24">
            {children}
          </main>
        </div>
        <Analytics />
      </body>
    </html>
  );
}
