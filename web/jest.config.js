/** @type {import('jest').Config} */
const config = {
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.(ts|tsx|js|jsx)$': ['babel-jest', { presets: ['next/babel'] }],
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
    '\\.(css|less|scss|sass|png|jpg|gif|svg|webp)$': '<rootDir>/__mocks__/fileMock.js',
  },
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testMatch: [
    '<rootDir>/tests/**/*.test.{ts,tsx}',
    '<rootDir>/tests/**/*.test.{js,jsx}',
  ],
  // Limitar la cobertura als fitxers efectivament testats.
  // NOTA: els parentesi en "app/(auth)" es tracten com a literals en micromatch.
  collectCoverageFrom: [
    'app/**/login/page.tsx',
    'app/**/register/page.tsx',
    'components/ui/NavBar.tsx',
    'components/ui/SideMenu.tsx',
    'lib/stores/auth.store.ts',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
}

module.exports = config
