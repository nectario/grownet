module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint', 'import'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:import/recommended',
    'plugin:import/typescript',
    'prettier'
  ],
  settings: {
    'import/resolver': {
      node: { extensions: ['.js', '.ts'] }
    }
  },
  rules: {
    '@typescript-eslint/naming-convention': [
      'error',
      { selector: 'class', format: ['PascalCase'] },
      { selector: 'function', format: ['camelCase'] },
      { selector: 'method', format: ['camelCase'] },
      { selector: 'variable', format: ['camelCase', 'UPPER_CASE'] },
      { selector: 'property', format: ['camelCase', 'UPPER_CASE'] }
    ],
    'id-length': ['error', { min: 3, exceptions: ['i', 'j', 'k'] }],

    // No Aliases — hard bans
    'no-restricted-syntax': [
      'error',
      { selector: 'TSTypeAliasDeclaration', message: 'Do not use type aliases.' },
      { selector: 'ImportNamespaceSpecifier', message: 'Do not use namespace import aliases.' },
      { selector: 'ImportSpecifier[imported.name!=local.name]', message: 'Do not alias imported names.' },
      { selector: 'ExportSpecifier[exported.name!=local.name]', message: 'Do not alias exported names.' },
      { selector: 'ExportAllDeclaration[exported!=null]', message: 'Do not alias re-exported module members.' },
      { selector: 'TSImportEqualsDeclaration', message: 'Do not use import equals (alias).' }
    ],

    '@typescript-eslint/consistent-type-definitions': ['error', 'interface'],
    'import/prefer-default-export': 'off',
    'import/no-default-export': 'warn',
    'import/no-unresolved': 'off',
    'import/extensions': 'off'
  },
  overrides: [
    {
      files: ['**/*.ts'],
      parserOptions: { project: false }
    }
  ]
};
