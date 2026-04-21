import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { FlatCompat } from '@eslint/eslintrc';
import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';

const configFilename = fileURLToPath(import.meta.url);
const configDirname = path.dirname(configFilename);

const compat = new FlatCompat({
  baseDirectory: configDirname,
  recommendedConfig: js.configs.recommended,
});

export default tseslint.config(
  { ignores: ['dist', 'node_modules', 'playwright-report', 'coverage'] },

  ...compat.extends(
    'airbnb',
    'airbnb-typescript',
    'airbnb/hooks',
    'plugin:react/recommended',
    'plugin:prettier/recommended',
  ),

  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: {
      ecmaVersion: 2020,
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.jest,
      },
      parserOptions: {
        projectService: {
          allowDefaultProject: [
            'eslint.config.js',
            'postcss.config.js',
            'tailwind.config.ts',
            'vitest.config.ts',
          ],
        },
        tsconfigRootDir: configDirname,
      },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    settings: {
      'import/resolver': {
        typescript: { project: './tsconfig.json' },
        node: { extensions: ['.js', '.jsx', '.ts', '.tsx'] },
      },
      react: { version: 'detect' },
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],

      '@typescript-eslint/lines-between-class-members': 'off',
      '@typescript-eslint/no-throw-literal': 'off',
      '@typescript-eslint/space-before-function-paren': 'off',
      '@typescript-eslint/comma-dangle': 'off',
      '@typescript-eslint/object-curly-spacing': 'off',
      '@typescript-eslint/quotes': 'off',
      '@typescript-eslint/semi': 'off',
      '@typescript-eslint/indent': 'off',
      '@typescript-eslint/no-loss-of-precision': 'off',
      '@typescript-eslint/no-useless-constructor': 'off',
      '@typescript-eslint/keyword-spacing': 'off',
      '@typescript-eslint/brace-style': 'off',
      '@typescript-eslint/func-call-spacing': 'off',
      '@typescript-eslint/space-infix-ops': 'off',

      'no-restricted-exports': 0,
      'no-use-before-define': 'off',
      '@typescript-eslint/no-explicit-any': 0,
      '@typescript-eslint/no-use-before-define': [
        'error',
        { variables: false, functions: false },
      ],
      '@typescript-eslint/no-var-requires': 0,
      '@typescript-eslint/ban-ts-comment': 0,
      'global-require': 0,
      'import/no-extraneous-dependencies': 0,
      'import/extensions': [
        'error',
        'ignorePackages',
        { js: 'never', jsx: 'never', ts: 'never', tsx: 'never' },
      ],
      'import/no-import-module-exports': 0,
      'import/prefer-default-export': 0,
      'jsx-a11y/no-static-element-interactions': 0,
      'jsx-a11y/click-events-have-key-events': 0,
      'no-console': 0,
      'react/prop-types': 0,
      'react/button-has-type': 0,
      'react/function-component-definition': 0,
      'react/jsx-filename-extension': [
        1,
        { extensions: ['.js', '.jsx', '.ts', '.tsx'] },
      ],
      'react/jsx-props-no-spreading': 0,
      'react/react-in-jsx-scope': 0,
      'react/require-default-props': 0,
      'max-len': [
        'error',
        { code: 120, ignoreStrings: true, ignoreTemplateLiterals: true },
      ],

      '@typescript-eslint/no-unused-vars': 'off',
      'no-irregular-whitespace': [
        'error',
        { skipStrings: true, skipJSXText: true },
      ],
    },
  },
);
