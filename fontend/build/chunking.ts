type AssetInfo = {
  name?: string;
  names?: string[];
};

const vendorGroups = [
  {
    name: 'vendor/react',
    matchers: ['react', 'react-dom', 'react-router', 'react-router-dom', '@remix-run/router', 'scheduler'],
  },
  {
    name: 'vendor/state-data',
    matchers: ['@tanstack/react-query', 'zustand', 'axios'],
  },
  {
    name: 'vendor/forms-validation',
    matchers: ['react-hook-form', '@hookform/resolvers', 'zod'],
  },
  {
    name: 'vendor/visual',
    matchers: ['framer-motion', 'lucide-react', 'clsx', 'tailwind-merge'],
  },
];

function normalizeModuleId(id: string) {
  return id.replaceAll('\\', '/');
}

export function resolveManualChunk(id: string) {
  const normalizedId = normalizeModuleId(id);

  if (normalizedId.includes('/node_modules/')) {
    const matchedGroup = vendorGroups.find((group) =>
      group.matchers.some((matcher) => normalizedId.includes(`/node_modules/${matcher}/`)),
    );

    return matchedGroup?.name ?? 'vendor/misc';
  }

  return undefined;
}

export function resolveAssetFileName(assetInfo: AssetInfo) {
  const assetName = assetInfo.names?.[0] ?? assetInfo.name ?? 'asset';

  if (assetName.endsWith('.css')) {
    return 'assets/styles/[name]-[hash][extname]';
  }

  if (/\.(png|jpe?g|gif|svg|webp|avif)$/.test(assetName)) {
    return 'assets/media/[name]-[hash][extname]';
  }

  if (/\.(woff2?|ttf|otf|eot)$/.test(assetName)) {
    return 'assets/fonts/[name]-[hash][extname]';
  }

  return 'assets/misc/[name]-[hash][extname]';
}
