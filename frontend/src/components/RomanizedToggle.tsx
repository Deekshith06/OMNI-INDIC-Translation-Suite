'use client';

import React from 'react';

export type RomanizedViewMode = 'native' | 'romanized' | 'both';

interface RomanizedToggleProps {
  mode: RomanizedViewMode;
  onChange: (mode: RomanizedViewMode) => void;
  disabled?: boolean;
}

export default function RomanizedToggle({ mode, onChange, disabled }: RomanizedToggleProps) {
  return (
    <div className={`flex items-center p-1 ml-2 bg-[var(--bg-input)] border border-[var(--border-primary)] rounded-lg w-fit ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      <button
        onClick={() => onChange('native')}
        className={`px-3 py-1.5 text-xs font-semibold rounded-md whitespace-nowrap transition-all ${
          mode === 'native'
            ? 'bg-[var(--accent-muted)] text-[var(--accent-bright)] shadow-sm border border-[var(--border-accent)]'
            : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
        }`}
      >
        Native
      </button>
      <button
        onClick={() => onChange('romanized')}
        className={`px-3 py-1.5 text-xs font-semibold rounded-md whitespace-nowrap transition-all ${
          mode === 'romanized'
            ? 'bg-[var(--accent-muted)] text-[var(--accent-bright)] shadow-sm border border-[var(--border-accent)]'
            : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
        }`}
      >
        Romanized
      </button>
      <button
        onClick={() => onChange('both')}
        className={`px-3 py-1.5 text-xs font-semibold rounded-md whitespace-nowrap transition-all ${
          mode === 'both'
            ? 'bg-[var(--accent-muted)] text-[var(--accent-bright)] shadow-sm border border-[var(--border-accent)]'
            : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
        }`}
      >
        Both
      </button>
    </div>
  );
}
