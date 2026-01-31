'use client';

import { useState } from 'react';
import Image from 'next/image';
import { useRive } from '@rive-app/react-canvas';

const ARXIV_TOPICS = [
  'Artificial Intelligence',
  'Machine Learning',
  'Computer Vision',
  'Natural Language Processing',
  'Robotics',
  'LLMs',
  'Deep Learning',
  'Neural Networks',
  'Quantum Computing',
  'Cryptography',
  'Computational Biology',
  'Astrophysics',
  'Condensed Matter',
  'High Energy Physics',
  'Mathematics',
  'Statistics',
  'Data Science',
];

export default function Home() {
  const [email, setEmail] = useState('');
  const [topic, setTopic] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  // Rive animation for corgi
  const { RiveComponent: CorgiRive } = useRive({
    src: '/corgis.riv',
    animations: 'Timeline 1',
    autoplay: true,
    loop: true,
  });

  // Rive animation for logo
  const { RiveComponent: LogoRive } = useRive({
    src: '/corgis.riv',
    animations: 'Timeline 1',
    autoplay: true,
    loop: true,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess(false);

    try {
      const response = await fetch('/api/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, topic }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'subscription failed');
      }

      setSuccess(true);
      setEmail('');
      setTopic('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white px-4 py-12">
      <div className="max-w-xl w-full border-4 border-black p-8 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        {/* Title */}
        
        {/* Subtitle */}
        <p className="text-lg text-center text-black mb-6">
          research papers as manga, delivered to your inbox
        </p>

      

        {/* Logo below corgi */}
        <div className="flex justify-center mb-8">
          <div className="w-full h-96">
            <LogoRive />
          </div>
        </div>

        {/* Subscribe Form */}
        <form onSubmit={handleSubmit} className="mb-6">
          {/* Topic Dropdown */}
          <div className="relative mb-3">
            <select
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              required
              disabled={loading}
              className="w-full px-5 py-3 text-base border-3 border-black focus:outline-none focus:ring-2 focus:ring-black transition-all disabled:bg-gray-100 disabled:cursor-not-allowed appearance-none bg-white cursor-pointer font-medium"
            >
              <option value="" disabled>
                Choose your research topic
              </option>
              {ARXIV_TOPICS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <div className="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none">
              <svg
                className="w-5 h-5 text-black"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={3}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </div>
          </div>

          {/* Combined input with button */}
          <div className="flex items-stretch border-3 border-black overflow-hidden">
            <div className="flex-1 flex items-stretch">
              {/* Email input */}
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Type your email..."
                required
                disabled={loading}
                className="flex-1 px-5 py-3.5 text-base focus:outline-none disabled:bg-gray-100 disabled:cursor-not-allowed font-medium"
              />

              {/* Dropdown icon indicator */}
              <div className="flex items-center px-3 border-l-2 border-black">
                <svg
                  className="w-5 h-5 text-black"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={3}
                    d="M8 9l4-4 4 4m0 6l-4 4-4-4"
                  />
                </svg>
              </div>
            </div>

            {/* Subscribe button */}
            <button
              type="submit"
              disabled={loading}
              className="px-8 py-3.5 text-base font-bold text-white bg-black hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed uppercase tracking-wider"
            >
              {loading ? 'Subscribing...' : 'Subscribe'}
            </button>
          </div>
        </form>

        {/* Success Message */}
        {success && (
          <div className="mb-6 p-4 bg-white border-3 border-black">
            <p className="text-black text-center text-sm font-bold">
              ✓ SUBSCRIBED! CHECK YOUR EMAIL FOR MANGA RESEARCH DIGESTS
            </p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-black border-3 border-black">
            <p className="text-white text-center text-sm font-bold">{error.toUpperCase()}</p>
          </div>
        )}

        {/* Terms */}
        <p className="text-xs text-center text-black leading-relaxed mb-6">
          By subscribing, I agree to receive manga research digests via email
        </p>

        {/* No thanks */}
        <div className="text-center mb-8">
          <button
            type="button"
            className="text-black hover:underline text-sm inline-flex items-center gap-1 transition-all font-semibold"
          >
            No thanks
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={3}
                d="M9 5l7 7-7 7"
              />
            </svg>
          </button>
        </div>

        {/* Special Thanks */}
        <div className="text-center pt-6 border-t-2 border-black">
          <p className="text-xs text-black mb-4 font-bold uppercase tracking-wider">special thanks to</p>
          <div className="flex flex-wrap justify-center items-center gap-8">
            <a
              href="https://reducto.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 hover:underline transition-all"
            >
              <img
                src="https://reducto.ai/favicon.ico"
                alt="reducto logo"
                className="w-10 h-10 object-contain"
                style={{ filter: 'grayscale(100%) contrast(1.2)' }}
              />
              <span className="text-base text-black font-bold">reducto</span>
            </a>

            <a
              href="https://firecrawl.dev"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 hover:underline transition-all"
            >
              <img
                src="https://firecrawl.dev/favicon.ico"
                alt="firecrawl logo"
                className="w-10 h-10 object-contain"
                style={{ filter: 'grayscale(100%) contrast(1.2)' }}
              />
              <span className="text-base text-black font-bold">firecrawl</span>
            </a>

            <a
              href="https://lovable.dev"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 hover:underline transition-all"
            >
              <img
                src="https://lovable.dev/favicon.ico"
                alt="lovable logo"
                className="w-10 h-10 object-contain"
                style={{ filter: 'grayscale(100%) contrast(1.2)' }}
              />
              <span className="text-base text-black font-bold">lovable</span>
            </a>

            <a
              href="https://resend.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 hover:underline transition-all"
            >
              <img
                src="https://resend.com/favicon.ico"
                alt="resend logo"
                className="w-10 h-10 object-contain"
                style={{ filter: 'grayscale(100%) contrast(1.2)' }}
              />
              <span className="text-base text-black font-bold">resend</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
