import path from 'node:path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolveAssetFileName, resolveManualChunk } from './build/chunking';

export default defineConfig({
  build: {
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        entryFileNames: 'assets/entries/[name]-[hash].js',
        chunkFileNames: 'assets/chunks/[name]-[hash].js',
        assetFileNames: resolveAssetFileName,
        manualChunks: resolveManualChunk,
      },
    },
  },
  plugins: [
    react({
      babel: {
        plugins: [['babel-plugin-react-compiler']],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
