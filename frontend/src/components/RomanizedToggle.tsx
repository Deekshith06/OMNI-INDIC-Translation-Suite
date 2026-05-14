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
    <div className={`flex w-full items-center p-1 bg-[var(--bg-elevated)] border border-[var(--border-primary)] rounded-lg shadow-inner ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      <button
        onClick={() => onChange('native')}
        className={`flex-1 px-3 py-1.5 text-xs font-semibold rounded-md whitespace-nowrap transition-all border ${
          mode === 'native'
            ? 'bg-[var(--accent-muted)] text-[var(--accent-bright)] shadow-sm border-[var(--border-accent)]'
            : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-input)] border-transparent'
        }`}
      >
        Native Script
      </button>
      <button
        onClick={() => onChange('romanized')}
        className={`flex-1 px-3 py-1.5 text-xs font-semibold rounded-md whitespace-nowrap transition-all border ${
          mode === 'romanized'
            ? 'bg-[var(--accent-muted)] text-[var(--accent-bright)] shadow-sm border-[var(--border-accent)]'
            : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-input)] border-transparent'
        }`}
      >
        Romanized
      </button>
      <button
        onClick={() => onChange('both')}
        className={`flex-1 px-3 py-1.5 text-xs font-semibold rounded-md whitespace-nowrap transition-all border ${
          mode === 'both'
            ? 'bg-[var(--accent-muted)] text-[var(--accent-bright)] shadow-sm border-[var(--border-accent)]'
            : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-input)] border-transparent'
        }`}
      >
        Show Both
      </button>
    </div>
  );
}
