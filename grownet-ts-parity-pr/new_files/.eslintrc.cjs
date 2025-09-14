// ESM + NodeNext friendly ESLint config for TS package
module.exports = {
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint', 'import'],
  extends: ['plugin:@typescript-eslint/recommended', 'prettier'],
  env: { node: true, es2022: true },
  settings: {
    'import/resolver': { node: { extensions: ['.js', '.ts'] } },
  },
  rules: {
    'import/extensions': 'off',
    'import/no-unresolved': 'off',
    '@typescript-eslint/no-explicit-any': 'warn',
  },
};
